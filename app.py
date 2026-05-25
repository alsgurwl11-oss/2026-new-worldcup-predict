# ================================
# app.py - Flask 라우트만 담당
# ================================
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import time
import pandas as pd
from predict import predict_scoreline
from simulate import simulate_full_bracket, simulate_what_if
from backtest import run_backtest, run_all_backtests
from analysis_advanced import calculate_all_groups_difficulty
from flask import Flask, render_template, request, jsonify
from model import initialize
from predict import (
    ensemble_predict, predict_group_matches, get_team_analysis
)
from simulate import (
    simulate_group, simulate_all_groups,
    simulate_tournament, simulate_bracket,
    simulate_korea_scenario
)
from upset_model import (
    calculate_uvi,
    calculate_all_group_uvi,
    get_confidence_level
)
from config import GROUPS_2026
from lineup_engine import load_fc26, preload_all_lineups, build_lineup, calculate_lineup_adjustment
app = Flask(__name__)

# ================================
# 서버 시작 시 초기화
# ================================
print("서버 초기화 중...")
print("라인업 데이터 로딩 중...")
fc26_df = load_fc26()
lineup_cache = preload_all_lineups(GROUPS_2026, fc26_df)
print(" OK 라인업 캐싱 완료!")
(
    model, top_features, continent_winrate,
    team_cache, h2h_cache, df, ranking, wc_df
) = initialize()
print(" OK 서버 준비 완료!")

# ================================
# 공통 예측 인자 묶음
# ================================
def pred_args():
    """예측 함수에 공통으로 필요한 인자"""
    return dict(
        team_cache        = team_cache,
        h2h_cache         = h2h_cache,
        continent_winrate = continent_winrate,
        model             = model,
        top_features      = top_features,
    )

# ================================
# 메인 페이지
# ================================
@app.route('/')
def index():
    return render_template('index.html', groups=GROUPS_2026)

# ================================
# API - 경기 예측
# ================================
@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    home = data.get('home')
    away = data.get('away')

    if not home or not away:
        return jsonify({'error': '팀을 선택해주세요'}), 400
    if home == away:
        return jsonify({'error': '서로 다른 팀을 선택해주세요'}), 400

    result = ensemble_predict(home, away, **pred_args())

    h_rank = team_cache.get(home, {}).get('rank', 'N/A')
    a_rank = team_cache.get(away, {}).get('rank', 'N/A')
    h_form = round(team_cache.get(home, {}).get('form', 0) * 100, 1)
    a_form = round(team_cache.get(away, {}).get('form', 0) * 100, 1)

    if (home, away) in h2h_cache:
        h2h = h2h_cache[(home, away)]
    elif (away, home) in h2h_cache:
        h2h_r = h2h_cache[(away, home)]
        h2h   = (h2h_r[2], h2h_r[1], h2h_r[0])
    else:
        h2h = (0.33, 0.33, 0.33)

    return jsonify({
        'home':      home,
        'away':      away,
        'home_win':  result['home_win'],
        'draw':      result['draw'],
        'away_win':  result['away_win'],
        'home_rank': h_rank,
        'away_rank': a_rank,
        'home_form': h_form,
        'away_form': a_form,
        'h2h_home':  round(h2h[0] * 100, 1),
        'h2h_draw':  round(h2h[1] * 100, 1),
        'h2h_away':  round(h2h[2] * 100, 1),
        'detail':    result['detail'],
    })

# ================================
# API - 조별리그 경기 예측
# ================================
@app.route('/api/group_matches', methods=['POST'])
def group_matches():
    data       = request.json
    group_name = data.get('group')

    if group_name not in GROUPS_2026:
        return jsonify({'error': '조를 선택해주세요'}), 400

    matches = predict_group_matches(group_name, **pred_args())
    return jsonify({'group': group_name, 'matches': matches})

# ================================
# API - 팀 상세 분석
# ================================
@app.route('/api/team_analysis', methods=['POST'])
def team_analysis():
    data = request.json
    team = data.get('team')

    if not team:
        return jsonify({'error': '팀을 선택해주세요'}), 400

    analysis = get_team_analysis(team, **pred_args())
    if analysis is None:
        return jsonify({'error': '팀 정보를 찾을 수 없습니다'}), 404

    return jsonify(analysis)

# ================================
# API - 조별리그 순위 시뮬레이션
# ================================
@app.route('/api/simulate_group', methods=['POST'])
def simulate_group_api():
    data       = request.json
    group_name = data.get('group')

    if group_name not in GROUPS_2026:
        return jsonify({'error': '조를 선택해주세요'}), 400

    result = simulate_group(group_name, **pred_args())
    return jsonify({'group': group_name, 'result': result})

# ================================
# API - 전체 32강 진출 확률
# ================================
@app.route('/api/simulate_all', methods=['GET'])
def simulate_all():
    result = simulate_all_groups(**pred_args())
    return jsonify(result)

# ================================
# API - 우승팀 예측
# ================================
@app.route('/api/tournament', methods=['GET'])
def tournament():
    result = simulate_tournament(**pred_args())
    return jsonify(result)

# ================================
# API - 토너먼트 브라켓
# ================================
@app.route('/api/bracket', methods=['GET'])
def bracket():
    result = simulate_bracket(**pred_args())
    return jsonify(result)

# ================================
# API - 한국 시나리오
# ================================
@app.route('/api/korea_scenario', methods=['GET'])
def korea_scenario():
    result = simulate_korea_scenario(**pred_args())
    return jsonify(result)

# ================================
# API - 특정 팀 시나리오 (한국 외 팀도 가능)
# ================================
@app.route('/api/team_scenario', methods=['POST'])
def team_scenario():
    data = request.json
    team = data.get('team', 'South Korea')

    if team not in [t for teams in GROUPS_2026.values() for t in teams]:
        return jsonify({'error': '팀을 찾을 수 없습니다'}), 404

    result = simulate_korea_scenario(target_team=team, **pred_args())
    return jsonify(result)
# ================================
# API - 이변 분석
# ================================
@app.route('/api/upset_analysis', methods=['GET'])
def upset_analysis():
    """전체 경기 이변 가능성 분석"""
    result = calculate_all_group_uvi(**pred_args())
    return jsonify(result)

@app.route('/api/match_uvi', methods=['POST'])
def match_uvi():
    """특정 경기 UVI 계산"""
    data     = request.json
    home     = data.get('home')
    away     = data.get('away')
    round_n  = data.get('round', 'Group stage')
    fav_pts  = data.get('favorite_pts', 0)
    und_pts  = data.get('underdog_pts', 0)

    if not home or not away:
        return jsonify({'error': '팀을 선택해주세요'}), 400

    home_tc  = team_cache.get(home, {})
    away_tc  = team_cache.get(away, {})
    home_str = home_tc.get('fpoints', 500)
    away_str = away_tc.get('fpoints', 500)

    favorite = home if home_str >= away_str else away
    underdog = away if home_str >= away_str else home

    result = calculate_uvi(
        favorite     = favorite,
        underdog     = underdog,
        team_cache   = team_cache,
        round_name   = round_n,
        favorite_pts = fav_pts,
        underdog_pts = und_pts,
    )

    return jsonify({
        'home':     home,
        'away':     away,
        'favorite': favorite,
        'underdog': underdog,
        **result
    })
# ================================
# app.py에 추가할 내용
# ================================
# 1. 파일 상단 import에 추가:
#
# from predict import predict_scoreline
# from simulate import simulate_full_bracket, simulate_what_if
# from backtest import run_backtest, run_all_backtests
# from analysis_advanced import calculate_all_groups_difficulty
#
# 2. 아래 라우트들을 if __name__ == '__main__': 바로 위에 추가
# ================================


# ================================
# API - 포아송 스코어라인
# ================================
@app.route('/api/scoreline', methods=['POST'])
def scoreline():
    """
    포아송 분포 기반 예상 스코어라인
    Request: {home, away, round}
    Response: top5 스코어, xG, BTTS, 오버언더
    """
    data       = request.json or {}
    home       = data.get('home')
    away       = data.get('away')
    round_name = data.get('round', 'Group')

    if not home or not away:
        return jsonify({'error': '팀을 선택해주세요'}), 400
    if home == away:
        return jsonify({'error': '서로 다른 팀을 선택해주세요'}), 400

    result = predict_scoreline(
        home, away, team_cache,
        venue='neutral', round_name=round_name
    )
    return jsonify(result)


# ================================
# API - 백테스트 시각화
# ================================
@app.route('/api/backtest', methods=['GET'])
def backtest_all():
    """전체 백테스트 결과 (2018 + 2022)"""
    try:
        hist    = pd.read_csv('data/wc_historical.csv')
        results = run_all_backtests(
            hist, team_cache, h2h_cache,
            continent_winrate, model, top_features
        )
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/<year>', methods=['GET'])
def backtest_year(year):
    """특정 연도 백테스트"""
    from config import BACKTEST_TOURNAMENTS
    if year not in BACKTEST_TOURNAMENTS:
        return jsonify({'error': '지원하지 않는 대회 (2022 또는 2018)'}), 400
    try:
        hist   = pd.read_csv('data/wc_historical.csv')
        result = run_backtest(
            year, hist, team_cache, h2h_cache,
            continent_winrate, model, top_features
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================================
# API - 죽음의 조 GDI
# ================================
@app.route('/api/group_difficulty', methods=['GET'])
def group_difficulty():
    """죽음의 조 난이도 랭킹"""
    results = calculate_all_groups_difficulty(team_cache)
    return jsonify(results)


# ================================
# API - What-if 시나리오
# ================================
@app.route('/api/what_if', methods=['POST'])
def what_if():
    """
    What-if 시나리오 분석
    Request: {group, fixed_results: [{home, away, result}]}
    result 값: 'home_win' / 'draw' / 'away_win'
    """
    data          = request.json or {}
    group_name    = data.get('group')
    fixed_results = data.get('fixed_results', [])

    from config import GROUPS_2026
    if not group_name or group_name not in GROUPS_2026:
        return jsonify({'error': '올바른 조를 선택해주세요'}), 400

    valid = ['home_win', 'draw', 'away_win']
    for fr in fixed_results:
        if fr.get('result') not in valid:
            return jsonify({'error': 'result는 home_win/draw/away_win'}), 400

    result = simulate_what_if(
        group_name, fixed_results, **pred_args()
    )
    return jsonify(result)


# API - 기본 라인업 조회
@app.route('/api/lineup/<team>', methods=['GET'])
def get_lineup(team):
    from urllib.parse import unquote
    team = unquote(team)
    formation = request.args.get('formation', None)
    if formation:
        lineup = build_lineup(team, formation=formation, fc26_df=fc26_df)
    else:
        lineup = lineup_cache.get(team)
        if not lineup:
            lineup = build_lineup(team, fc26_df=fc26_df)
    return jsonify(lineup)

# API - 커스텀 라인업으로 예측
@app.route('/api/predict_with_lineup', methods=['POST'])
def predict_with_lineup():
    data = request.json
    home = data.get('home')
    away = data.get('away')
    home_formation = data.get('home_formation')
    away_formation = data.get('away_formation')
    home_players = data.get('home_players')  # 커스텀 라인업
    away_players = data.get('away_players')

    # 기본 예측
    base = ensemble_predict(home, away, **pred_args())

    # 라인업 강도 계산
    if home_players:
        from lineup_engine import calculate_custom_lineup_strength
        home_lu = calculate_custom_lineup_strength(home, home_formation, home_players)
        away_lu = calculate_custom_lineup_strength(away, away_formation, away_players)
    else:
        home_lu = lineup_cache.get(home, build_lineup(home, fc26_df=fc26_df))
        away_lu = lineup_cache.get(away, build_lineup(away, fc26_df=fc26_df))

    adj = calculate_lineup_adjustment(home_lu, away_lu)
    adj_val = adj['total_home_adj']

    # 확률 보정
    home_win = round(base['home_win'] + adj_val, 1)
    away_win = round(base['away_win'] - adj_val, 1)
    draw     = round(base['draw'], 1)

    # 정규화
    total = home_win + draw + away_win
    return jsonify({
        'home': home, 'away': away,
        'home_win':  round(home_win / total * 100, 1),
        'draw':      round(draw     / total * 100, 1),
        'away_win':  round(away_win / total * 100, 1),
        'base':      base,
        'adjustment': adj,
        'home_lineup': home_lu,
        'away_lineup': away_lu,
    })
# ================================
# API - 예상 대진표 브라켓
# ================================
#  OK 이렇게 기존 함수 안에 넣는 거야

@app.route('/api/bracket_prediction', methods=['GET'])
def bracket_prediction():
    try:
        t0 = time.time()          # ← 추가
        
        group_results = {}
        for group in GROUPS_2026.keys():
            result = simulate_group(group, **pred_args(), n_sim=300)
            group_results[group] = result
        
        print(f"조별 시뮬 완료: {time.time()-t0:.1f}초")  # ← 추가
        
        output = simulate_full_bracket(group_results, **pred_args())
        
        print(f"브라켓 완료: {time.time()-t0:.1f}초")  # ← 추가
        
        return jsonify(output)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# ================================
# API - 라운드별 베팅 픽
# ================================
@app.route('/api/betting_picks/<int:round_num>', methods=['GET'])
def betting_picks(round_num):
    from config import WC2026_SCHEDULE
    from predict import get_betting_strength
    from upset_model import calculate_uvi

    matches = WC2026_SCHEDULE.get(round_num, [])
    result = []

    for match in matches:
        home = match['home']
        away = match['away']

        try:
            pred = ensemble_predict(home, away, **pred_args())
        except:
            continue

        probs = {
            'home_win': pred['home_win'],
            'draw':     pred['draw'],
            'away_win': pred['away_win'],
        }
        best_outcome = max(probs, key=probs.get)
        confidence   = probs[best_outcome]

        # UVI 계산
        home_str = team_cache.get(home, {}).get('fpoints', 500)
        away_str = team_cache.get(away, {}).get('fpoints', 500)
        favorite = home if home_str >= away_str else away
        underdog = away if home_str >= away_str else home
        uvi_result = calculate_uvi(favorite, underdog, team_cache)
        uvi = uvi_result['uvi']

        # 배당 엣지 계산
        bet_h = get_betting_strength(home)
        bet_a = get_betting_strength(away)
        total = bet_h + bet_a + 0.001
        if best_outcome == 'home_win':
            bet_implied = round(bet_h / total * 100, 1)
        elif best_outcome == 'away_win':
            bet_implied = round(bet_a / total * 100, 1)
        else:
            bet_implied = round((1 - bet_h/total - bet_a/total) * 100, 1)

        edge = round(confidence - bet_implied, 1)

        # 픽 라벨
        if best_outcome == 'home_win': label = f"{home} 승"
        elif best_outcome == 'away_win': label = f"{away} 승"
        else: label = '무승부'

        # 추천 기준: 신뢰도 55%+ AND UVI 35% 미만 AND 엣지 양수
        # 지금은 신뢰도 + UVI 기준 (개막 후 배당 엣지 추가 예정)
        recommended = confidence >= 55 and uvi < 0.35

        result.append({
            'home':         home,
            'away':         away,
            'group':        match['group'],
            'date':         match['date'],
            'home_win':     pred['home_win'],
            'draw':         pred['draw'],
            'away_win':     pred['away_win'],
            'best_outcome': best_outcome,
            'confidence':   round(confidence, 1),
            'uvi':          round(uvi * 100, 1),
            'edge':         edge,
            'bet_implied':  bet_implied,
            'pick_label':   label,
            'recommended':  recommended,
        })

    result.sort(key=lambda x: x['confidence'], reverse=True)
    return jsonify(result)

# ================================
# API - 최적 조합 추천
# ================================
@app.route('/api/best_combo/<int:round_num>', methods=['GET'])
def best_combo(round_num):
    from config import WC2026_SCHEDULE
    from itertools import combinations
    from upset_model import calculate_uvi

    n         = int(request.args.get('n', 5))
    uvi_limit = float(request.args.get('uvi_limit', 100))
    min_conf  = float(request.args.get('min_conf', 0))

    matches = WC2026_SCHEDULE.get(round_num, [])

    # 전체 경기 예측
    preds = []
    for match in matches:
        home, away = match['home'], match['away']
        try:
            pred = ensemble_predict(home, away, **pred_args())
        except:
            continue

        probs = {'home_win': pred['home_win'],
                 'draw': pred['draw'], 'away_win': pred['away_win']}
        best   = max(probs, key=probs.get)
        conf   = probs[best]
        label  = f"{home} 승" if best == 'home_win' else \
                 (f"{away} 승" if best == 'away_win' else '무승부')

        home_str = team_cache.get(home, {}).get('fpoints', 500)
        away_str = team_cache.get(away, {}).get('fpoints', 500)
        fav = home if home_str >= away_str else away
        und = away if home_str >= away_str else home
        uvi = calculate_uvi(fav, und, team_cache)['uvi'] * 100

        preds.append({
            'home': home, 'away': away,
            'group': match['group'], 'date': match['date'],
            'confidence': round(conf, 1),
            'uvi': round(uvi, 1),
            'pick_label': label,
        })

    # 필터
    filtered = [m for m in preds
                if m['uvi'] <= uvi_limit and m['confidence'] >= min_conf]

    if len(filtered) < n:
        return jsonify({
            'error': f'조건 충족 경기 {len(filtered)}개 → {n}폴더 조합 불가',
            'available': len(filtered)
        }), 400

    # 전체 조합 계산 → TOP5
    best_combos = sorted([
        {
            'matches':    list(combo),
            'combo_prob': round(
                __import__('math').prod(m['confidence']/100 for m in combo) * 100, 1
            ),
        }
        for combo in combinations(filtered, n)
    ], key=lambda x: x['combo_prob'], reverse=True)[:5]

    return jsonify(best_combos)
if __name__ == '__main__':
    print("\n>> Flask 서버 시작!")
    print("http://127.0.0.1:5000 접속하세요\n")
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)  