# ================================
# backtest.py - 완전 리팩토링
# 기존 파일을 이걸로 교체
# ================================

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from itertools import product
from model import initialize
from predict import ensemble_predict
from config import BACKTEST_TOURNAMENTS, ENSEMBLE_WEIGHTS
import config


# ================================
# 모델 로딩 (백테스트 스크립트 직접 실행 시)
# ================================

def _load_model():
    print("모델 로딩 중...")
    return initialize()


# ================================
# 단일 경기 예측 + 평가
# ================================

def predict_match(home, away, team_cache, h2h_cache,
                  continent_winrate, model, top_features):
    """단일 경기 예측 (예외 처리 포함)"""
    try:
        result = ensemble_predict(
            home, away,
            team_cache, h2h_cache,
            continent_winrate, model, top_features
        )
        return result
    except Exception:
        return {'home_win': 33.3, 'draw': 33.3, 'away_win': 33.3}


# ================================
# 단일 월드컵 백테스트
# ================================

def run_backtest(tournament_year, hist_df,
                 team_cache, h2h_cache,
                 continent_winrate, model, top_features):
    """
    특정 월드컵 백테스트

    프로세스:
      1. 해당 대회 경기 필터링
      2. 각 경기 앙상블 예측
      3. 실제 결과와 비교
      4. 다양한 지표 계산
    """
    tourney = BACKTEST_TOURNAMENTS.get(tournament_year)
    if not tourney:
        return {'error': f'{tournament_year} 설정 없음'}

    wc_year = hist_df[hist_df['Year'] == int(tournament_year)].copy()
    wc_year = wc_year.dropna(subset=['home_score', 'away_score'])

    if len(wc_year) == 0:
        return {'error': f'{tournament_year} 데이터 없음'}

    predictions = []

    for _, row in wc_year.iterrows():
        home = row['home_team']
        away = row['away_team']

        # 실제 결과
        hs = float(row['home_score'])
        as_ = float(row['away_score'])
        if hs > as_:   actual = 'home_win'
        elif hs < as_: actual = 'away_win'
        else:           actual = 'draw'

        # 예측
        result    = predict_match(home, away, team_cache, h2h_cache,
                                  continent_winrate, model, top_features)
        probs     = {
            'home_win': result['home_win'],
            'draw':     result['draw'],
            'away_win': result['away_win'],
        }
        predicted  = max(probs, key=probs.get)
        confidence = max(probs.values())
        correct    = (predicted == actual)

        predictions.append({
            'home':       home,
            'away':       away,
            'round':      row.get('Round', ''),
            'actual':     actual,
            'predicted':  predicted,
            'correct':    correct,
            'home_prob':  result['home_win'],
            'draw_prob':  result['draw'],
            'away_prob':  result['away_win'],
            'confidence': round(confidence, 1),
        })

    df_pred = pd.DataFrame(predictions)

    # 라운드 분리
    group_df    = df_pred[df_pred['round'].str.contains('Group', na=False)]
    knockout_df = df_pred[~df_pred['round'].str.contains('Group', na=False)]

    # 4강 맞춤 확인
    top4_actual = [
        tourney['champion'], tourney['runner_up'],
        tourney['third'],    tourney['fourth'],
    ]

    return {
        'tournament':          tourney['name'],
        'year':                tournament_year,
        'total_matches':       len(df_pred),
        'total_accuracy':      round(df_pred['correct'].mean() * 100, 1),
        'group_accuracy':      round(group_df['correct'].mean() * 100, 1) if len(group_df) > 0 else 0,
        'knockout_accuracy':   round(knockout_df['correct'].mean() * 100, 1) if len(knockout_df) > 0 else 0,
        'avg_confidence':      round(df_pred['confidence'].mean(), 1),
        'high_conf_accuracy':  round(
            df_pred[df_pred['confidence'] >= 50]['correct'].mean() * 100, 1
        ) if len(df_pred[df_pred['confidence'] >= 50]) > 0 else 0,
        'high_conf_count':     int((df_pred['confidence'] >= 50).sum()),
        'champion_actual':     tourney['champion'],
        'runner_up_actual':    tourney['runner_up'],
        'top4_actual':         top4_actual,
        'match_details':       predictions,
    }


# ================================
# 전체 백테스트 실행
# ================================

def run_all_backtests(hist_df, team_cache, h2h_cache,
                      continent_winrate, model, top_features):
    """모든 설정된 월드컵 백테스트"""
    results = {}
    for year in BACKTEST_TOURNAMENTS:
        print(f"\n=== {year} 백테스트 ===")
        results[year] = run_backtest(
            year, hist_df,
            team_cache, h2h_cache,
            continent_winrate, model, top_features
        )
        r = results[year]
        if 'error' not in r:
            print(f"전체: {r['total_accuracy']}% | 조별: {r['group_accuracy']}% | 토너먼트: {r['knockout_accuracy']}%")

    return results


# ================================
# 가중치 최적화 (기존 로직 유지)
# ================================

def backtest(year, hist_df, team_cache, h2h_cache,
             continent_winrate, model, top_features):
    """단순 정확도 반환 (가중치 최적화용)"""
    result = run_backtest(year, hist_df, team_cache, h2h_cache,
                          continent_winrate, model, top_features)
    if 'error' in result:
        return 0.0
    return result['total_accuracy']


# ================================
# 스크립트 직접 실행 시
# ================================

if __name__ == '__main__':
    (model, top_features, continent_winrate,
     team_cache, h2h_cache, df, ranking, wc_df) = _load_model()

    hist = pd.read_csv('data/wc_historical.csv')

    print(f"\n현재 가중치: {config.ENSEMBLE_WEIGHTS}")

    # 2022 백테스트
    r22 = run_backtest('2022', hist, team_cache, h2h_cache,
                       continent_winrate, model, top_features)
    print(f"\n2022 전체: {r22['total_accuracy']}%")
    print(f"2022 조별: {r22['group_accuracy']}%")
    print(f"2022 토너먼트: {r22['knockout_accuracy']}%")
    print(f"2022 고신뢰도({r22['high_conf_count']}경기): {r22['high_conf_accuracy']}%")

    # 가중치 최적화
    print("\n가중치 최적화 중... ☕")
    best_acc     = 0
    best_weights = None

    for ml, opta, bet in product(
        [0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        [0.15, 0.20, 0.25, 0.30, 0.35],
        [0.20, 0.25, 0.30, 0.35, 0.40],
    ):
        elo = round(1.0 - ml - opta - bet, 2)
        if elo < 0.05 or elo > 0.30:
            continue

        config.ENSEMBLE_WEIGHTS = {
            'ml': ml, 'opta': opta, 'betting': bet, 'elo': elo
        }

        acc = backtest('2022', hist, team_cache, h2h_cache,
                       continent_winrate, model, top_features)

        if acc > best_acc:
            best_acc     = acc
            best_weights = {'ml': ml, 'opta': opta, 'betting': bet, 'elo': elo}
            print(f"  새 최고: {acc:.1f}% → {best_weights}")

    print(f"\n{'='*50}")
    print(f"최적 가중치: {best_weights}")
    print(f"최고 정확도: {best_acc:.1f}%")
    print(f"\n# config.py ENSEMBLE_WEIGHTS 교체:")
    print(f"ENSEMBLE_WEIGHTS = {{")
    for k, v in best_weights.items():
        print(f"    '{k}': {v},")
    print(f"}}")

    # 기존 가중치 복원
    config.ENSEMBLE_WEIGHTS = {
        'ml': 0.20, 'opta': 0.20, 'betting': 0.35, 'elo': 0.25
    }
    old = backtest('2022', hist, team_cache, h2h_cache,
                   continent_winrate, model, top_features)
    print(f"\n기존 가중치 2022: {old:.1f}%")