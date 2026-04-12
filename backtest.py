# ================================
# backtest.py - 가중치 최적화
# ================================
import os
os.chdir('C:\\Users\\alsgu\\2026-new-worldcup-predict')

import pandas as pd
import numpy as np
from itertools import product
from model import initialize
from predict import ensemble_predict
import config

# 모델 로딩
print("모델 로딩 중...")
(model, top_features, continent_winrate,
 team_cache, h2h_cache, df, ranking, wc_df) = initialize()

# 역대 월드컵 데이터
hist = pd.read_csv('data/wc_historical.csv')

# 팀명 매핑 (백테스트용)
BACKTEST_NAME_MAP = {
    'Korea Republic': 'South Korea',
    'IR Iran':        'Iran',
    'USA':            'United States',
}

# ================================
# 백테스트 함수
# ================================
def backtest(year):
    wc_year = hist[hist['Year'] == year].copy()
    wc_year = wc_year.dropna(subset=['home_score', 'away_score'])

    correct = 0
    total   = 0

    for _, row in wc_year.iterrows():
        home = BACKTEST_NAME_MAP.get(row['home_team'], row['home_team'])
        away = BACKTEST_NAME_MAP.get(row['away_team'], row['away_team'])

        if row['home_score'] > row['away_score']:
            actual = 'home'
        elif row['home_score'] < row['away_score']:
            actual = 'away'
        else:
            actual = 'draw'

        try:
            pred = ensemble_predict(
                home, away,
                team_cache, h2h_cache,
                continent_winrate, model, top_features
            )
            probs = {
                'home': pred['home_win'],
                'draw': pred['draw'],
                'away': pred['away_win'],
            }
            predicted = max(probs, key=probs.get)
            if predicted == actual:
                correct += 1
            total += 1
        except:
            continue

    return correct / total * 100 if total > 0 else 0

# ================================
# 현재 가중치 정확도 확인
# ================================
print(f"\n현재 가중치: {config.ENSEMBLE_WEIGHTS}")
acc_22 = backtest(2022)
print(f"2022 정확도: {acc_22:.1f}%")

# ================================
# 가중치 최적화
# ================================
print("\n가중치 최적화 중... ☕")

best_acc     = 0
best_weights = None

ml_list  = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
op_list  = [0.20, 0.25, 0.30, 0.35, 0.40]
bet_list = [0.15, 0.20, 0.25, 0.30, 0.35]

count = 0
for ml, opta, bet in product(ml_list, op_list, bet_list):
    elo = round(1.0 - ml - opta - bet, 2)
    if elo < 0.05 or elo > 0.25:
        continue

    config.ENSEMBLE_WEIGHTS = {
        'ml':      ml,
        'opta':    opta,
        'betting': bet,
        'elo':     elo,
    }

    acc_22 = backtest(2022)
    count += 1

    if count % 10 == 0:
        print(f"  진행중... {count}개 조합 테스트")

    if acc_22 > best_acc:
        best_acc     = acc_22
        best_weights = {
            'ml': ml, 'opta': opta,
            'betting': bet, 'elo': elo,
        }
        print(f"  새 최고: {acc_22:.1f}% → {best_weights}")

# ================================
# 최적 결과 출력
# ================================
print(f"\n{'='*50}")
print(f"최적 가중치: {best_weights}")
print(f"최고 정확도: {best_acc:.1f}%")

print(f"\n# config.py ENSEMBLE_WEIGHTS 교체:")
print(f"ENSEMBLE_WEIGHTS = {{")
for k, v in best_weights.items():
    print(f"    '{k}': {v},")
print(f"}}")

# ================================
# 기존 가중치와 비교
# ================================
print("\n=== 기존 가중치와 비교 ===")
config.ENSEMBLE_WEIGHTS = {
    'ml': 0.35, 'opta': 0.30,
    'betting': 0.25, 'elo': 0.10,
}
old_22 = backtest(2022)
print(f"기존 가중치 2022: {old_22:.1f}%")
print(f"최적 가중치 2022: {best_acc:.1f}%")
print(f"개선: +{best_acc - old_22:.1f}%p")