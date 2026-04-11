# ================================
# app.py - Flask 라우트만 담당
# ================================

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
from config import GROUPS_2026

app = Flask(__name__)

# ================================
# 서버 시작 시 초기화
# ================================
print("서버 초기화 중...")
(
    model, top_features, continent_winrate,
    team_cache, h2h_cache, df, ranking, wc_df
) = initialize()
print("✅ 서버 준비 완료!")

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

if __name__ == '__main__':
    print("\n🚀 Flask 서버 시작!")
    print("http://127.0.0.1:5000 접속하세요\n")
    app.run(debug=True)