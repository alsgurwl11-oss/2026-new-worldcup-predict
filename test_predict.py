# ================================
# test_predict.py - 기본 테스트
# ================================
import os
os.chdir('C:\\Users\\alsgu\\2026-new-worldcup-predict')

import sys
sys.path.append('.')

from model import initialize
from predict import ensemble_predict

print("테스트 시작...")
(model, top_features, continent_winrate,
 team_cache, h2h_cache, df, ranking, wc_df) = initialize()

# ================================
# 테스트 1: 확률 합이 100%인지
# ================================
def test_probability_sum():
    result = ensemble_predict(
        'Brazil', 'South Korea',
        team_cache, h2h_cache,
        continent_winrate, model, top_features
    )
    total = result['home_win'] + result['draw'] + result['away_win']
    assert abs(total - 100.0) < 0.1, f"확률 합 오류: {total}"
    print(f"✅ 테스트1 통과: 확률 합 = {total}%")

# ================================
# 테스트 2: 강팀이 약팀보다 높은 확률
# ================================
def test_strong_vs_weak():
    result = ensemble_predict(
        'Brazil', 'Haiti',
        team_cache, h2h_cache,
        continent_winrate, model, top_features
    )
    assert result['home_win'] > result['away_win'], \
        f"브라질이 아이티보다 낮음: {result['home_win']} vs {result['away_win']}"
    print(f"✅ 테스트2 통과: 브라질 {result['home_win']}% > 아이티 {result['away_win']}%")

# ================================
# 테스트 3: 없는 팀 입력 시 에러 없이 처리
# ================================
def test_unknown_team():
    result = ensemble_predict(
        'UnknownTeam', 'Brazil',
        team_cache, h2h_cache,
        continent_winrate, model, top_features
    )
    total = result['home_win'] + result['draw'] + result['away_win']
    assert abs(total - 100.0) < 0.1, f"확률 합 오류: {total}"
    print(f"✅ 테스트3 통과: 없는 팀 처리 정상")

# ================================
# 테스트 4: 같은 팀끼리 50% 근처
# ================================
def test_same_strength():
    result = ensemble_predict(
        'France', 'Brazil',
        team_cache, h2h_cache,
        continent_winrate, model, top_features
    )
    print(f"✅ 테스트4: 프랑스 {result['home_win']}% vs 브라질 {result['away_win']}%")
    print(f"   (비슷한 강팀끼리라 큰 차이 없어야 함)")

# ================================
# 테스트 5: detail 키 존재 확인
# ================================
def test_detail_keys():
    result = ensemble_predict(
        'Argentina', 'England',
        team_cache, h2h_cache,
        continent_winrate, model, top_features
    )
    assert 'detail' in result, "detail 키 없음"
    assert 'ml' in result['detail'], "ml 키 없음"
    assert 'opta' in result['detail'], "opta 키 없음"
    assert 'betting' in result['detail'], "betting 키 없음"
    assert 'elo' in result['detail'], "elo 키 없음"
    print(f"✅ 테스트5 통과: detail 키 정상")

# ================================
# 전체 실행
# ================================
test_probability_sum()
test_strong_vs_weak()
test_unknown_team()
test_same_strength()
test_detail_keys()

print("\n🎉 모든 테스트 통과!")