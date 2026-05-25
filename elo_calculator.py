# ================================
# elo_calculator.py - World Football ELO 계산
# eloratings.net 공식 방법론 기반
# ================================
import pandas as pd
import numpy as np

# K값 (경기 중요도)
K_FACTORS = {
    'FIFA World Cup':                60,
    'FIFA World Cup qualification':  40,
    'UEFA Euro':                     50,
    'UEFA Euro qualification':       35,
    'Copa América':                  50,
    'African Cup of Nations':        50,
    'AFC Asian Cup':                 50,
    'UEFA Nations League':           40,
    'CONCACAF Nations League':       40,
    'Gold Cup':                      40,
    'Friendly':                      20,
}
DEFAULT_K = 30

# 초기 ELO (FIFA 랭킹 기반)
BASE_ELO = 1500

def get_k_factor(tournament):
    for key, k in K_FACTORS.items():
        if key.lower() in str(tournament).lower():
            return k
    return DEFAULT_K

def expected_score(r_a, r_b, home=False):
    """기대 승률 계산"""
    dr = r_a - r_b + (100 if home else 0)
    return 1 / (10 ** (-dr / 400) + 1)

def goal_diff_multiplier(goal_diff):
    """득실차 보정 (eloratings.net 공식)"""
    if goal_diff == 1: return 1.0
    if goal_diff == 2: return 1.5
    if goal_diff >= 3: return 1.75 + (goal_diff - 3) * 0.25 / 3
    return 1.0

def calculate_elo_ratings(results_path='data/results.csv', start_year=1992):
    """
    전체 경기 결과로 ELO 계산
    반환: 팀별 현재 ELO 딕셔너리
    """
    df = pd.read_csv(results_path)
    df = df.dropna(subset=['home_score', 'away_score'])
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['date'].dt.year >= start_year]
    df = df.sort_values('date').reset_index(drop=True)

    elo = {}  # 팀별 ELO

    for _, row in df.iterrows():
        home = row['home_team']
        away = row['away_team']
        hs   = row['home_score']
        as_  = row['away_score']
        tournament = row.get('tournament', 'Friendly')
        neutral = row.get('neutral', False)

        # 초기 ELO 설정
        if home not in elo: elo[home] = BASE_ELO
        if away not in elo: elo[away] = BASE_ELO

        # K값
        k = get_k_factor(tournament)

        # 실제 결과
        if hs > as_:   w_home, w_away = 1.0, 0.0
        elif hs < as_: w_home, w_away = 0.0, 1.0
        else:          w_home, w_away = 0.5, 0.5

        # 기대 승률
        is_home = not neutral
        we_home = expected_score(elo[home], elo[away], home=is_home)
        we_away = 1 - we_home

        # 득실차 보정
        gd_mult = goal_diff_multiplier(abs(int(hs) - int(as_)))

        # ELO 업데이트
        elo[home] += k * gd_mult * (w_home - we_home)
        elo[away] += k * gd_mult * (w_away - we_away)

    # 반올림
    return {team: round(rating, 1) for team, rating in elo.items()}


def elo_win_prob(elo_a, elo_b):
    """ELO 기반 순수 승리 확률 (무승부 없음)"""
    return 1 / (10 ** (-(elo_a - elo_b) / 400) + 1)


def predict_elo_full(home, away, elo_ratings):
    """
    ELO 기반 홈승/무/원정승 확률 반환
    무승부 = 25% 고정 (축구 평균)
    """
    h_elo = elo_ratings.get(home, BASE_ELO)
    a_elo = elo_ratings.get(away, BASE_ELO)

    hw = elo_win_prob(h_elo, a_elo)
    aw = 1 - hw
    d  = 0.25

    total = hw + d + aw
    return hw/total, d/total, aw/total


if __name__ == '__main__':
    print("ELO 계산 중...")
    elo_ratings = calculate_elo_ratings()

    # 상위 20개 출력
    top20 = sorted(elo_ratings.items(), key=lambda x: x[1], reverse=True)[:20]
    print("\nELO 랭킹 TOP 20:")
    for i, (team, rating) in enumerate(top20, 1):
        print(f"  {i:2}. {team:<30} {rating:.1f}")

    # 2026 월드컵 참가팀 확인
    from config import GROUPS_2026
    all_teams = [t for teams in GROUPS_2026.values() for t in teams]
    print("\n2026 월드컵 참가팀 ELO:")
    wc_elo = [(t, elo_ratings.get(t, BASE_ELO)) for t in all_teams]
    wc_elo.sort(key=lambda x: x[1], reverse=True)
    for team, rating in wc_elo:
        print(f"  {team:<30} {rating:.1f}")