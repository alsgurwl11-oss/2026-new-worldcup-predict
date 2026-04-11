# ================================
# upset_model.py - 이변 취약성 지수 (UVI)
# 데이터 기반 설계:
# - xG 차이별 이변율: wc_historical.csv 분석
# - 라운드별 이변율: wc_historical.csv 분석
# - 슈팅 효율: wc_2022.csv 분석
# - 점유율 역설: wc_2022.csv 분석
# - 압박 강도: wc_2022.csv 분석
# ================================

import pandas as pd
import numpy as np
from config import GROUPS_2026, TEAM_STRENGTH_FC25

# ================================
# 1. 데이터 기반 상수 (분석 결과)
# ================================

# 라운드별 기저 이변율 (wc_historical 분석 결과)
ROUND_BASE_UPSET_RATE = {
    'Group stage':        0.219,  # 21.9%
    'Round of 16':        0.125,  # 12.5%
    'Quarter-finals':     0.375,  # 37.5% ← 가장 높음!
    'Semi-finals':        0.000,  # 0%
    'Final':              0.000,  # 0%
    'Third-place match':  0.500,  # 50%
    # 기본값
    'default':            0.211,  # 전체 평균
}

# xG 차이별 이변율 (wc_historical 분석 결과)
XG_GAP_UPSET_RATE = {
    '0~0.3':   0.368,  # 36.8% ← 박빙 경기 이변 최고
    '0.3~0.6': 0.296,  # 29.6%
    '0.6~1.0': 0.174,  # 17.4%
    '1.0~1.5': 0.130,  # 13.0%
    '1.5+':    0.167,  # 16.7%
}

# 점유율 구간별 승률 (wc_2022 분석 결과)
# 점유율 낮을수록 오히려 높은 승률!
POSSESSION_WIN_RATE = {
    '~35%':   0.588,  # 58.8% ← 수비 집중팀 최강!
    '35~45%': 0.357,
    '45~55%': 0.423,
    '55~65%': 0.200,
    '65%+':   1.000,  # 샘플 적음 → 참고만
}

# UVI 가중치 (데이터 기반 확정)
UVI_WEIGHTS = {
    'xg_gap':        0.30,  # xG 차이 → 가장 강력
    'shooting_eff':  0.25,  # 슈팅 효율 → 승패 핵심
    'possession':    0.20,  # 점유율 역설
    'round_rate':    0.15,  # 라운드별 기저율
    'pressure':      0.10,  # 압박 강도 (보조)
}

# ================================
# 2. 팀 스타일 프로파일
# FC25 데이터 기반으로 팀 전술 스타일 분류
# ================================

def get_team_style(team, team_cache):
    """
    팀 전술 스타일 분류
    FC25 수비/공격 스탯 기반
    반환: 'defensive' / 'balanced' / 'attacking'
    """
    tc = team_cache.get(team, {})

    # FC25 OVR 기반 강도
    fc25 = TEAM_STRENGTH_FC25.get(team, {})
    top23 = fc25.get('top23', 65.0)
    top11 = fc25.get('top11', 68.0)

    # 최근 득실 기반 스타일 추정
    avg_gf = tc.get('gf', 1.2)
    avg_ga = tc.get('ga', 1.2)

    if avg_ga < 0.8:
        return 'defensive'   # 실점 적음 → 수비적
    elif avg_gf > 1.8:
        return 'attacking'   # 득점 많음 → 공격적
    else:
        return 'balanced'

def get_tactical_mismatch(favorite, underdog, team_cache):
    """
    전술 상성 분석
    수비적 언더독 vs 공격적 강팀 → 이변 가능성 UP
    """
    fav_style = get_team_style(favorite, team_cache)
    und_style = get_team_style(underdog, team_cache)

    # 수비 집중 언더독이 공격적 강팀 만나면 이변 가능성 높음
    if und_style == 'defensive' and fav_style == 'attacking':
        return 0.8   # 이변 가능성 높음
    elif und_style == 'balanced' and fav_style == 'attacking':
        return 0.5
    elif und_style == 'defensive' and fav_style == 'balanced':
        return 0.4
    else:
        return 0.2   # 일반적 상황

# ================================
# 3. FC25 기반 원맨팀 취약도
# ================================

def get_key_man_dependency(team):
    """
    원맨팀 취약도 계산
    TOP1 OVR과 TOP11 평균의 차이
    → 클수록 에이스 의존도 높음 → 이변 취약
    """
    fc25 = TEAM_STRENGTH_FC25.get(team, {})
    top11 = fc25.get('top11', 68.0)
    top23 = fc25.get('top23', 65.0)

    # top11과 top23 차이가 클수록 상위 선수 의존도 높음
    dependency = (top11 - top23) / top11

    # 0~1 사이로 정규화
    return min(max(dependency, 0.0), 1.0)

# ================================
# 4. 절박도 지수
# 조별리그 승점 상황 기반
# ================================

def get_desperation_gap(favorite_pts, underdog_pts, round_name):
    """
    절박도 격차 계산
    언더독이 더 절박할수록 이변 가능성 UP

    조별리그 승점 기준:
    0점: 절박도 1.0 (탈락 위기)
    3점: 절박도 0.5
    6점: 절박도 0.1 (진출 확정)
    """
    if 'Group' not in round_name:
        # 토너먼트는 모두 절박
        return 0.5

    def pts_to_desperation(pts):
        if pts == 0:   return 1.0
        elif pts == 1: return 0.8
        elif pts == 3: return 0.5
        elif pts == 4: return 0.3
        elif pts == 6: return 0.1
        else:          return 0.3

    fav_desp = pts_to_desperation(favorite_pts)
    und_desp = pts_to_desperation(underdog_pts)

    # 언더독이 더 절박한 정도
    gap = und_desp - fav_desp

    # 0~1 사이로 정규화
    return min(max(gap, 0.0), 1.0)

# ================================
# 5. xG 기반 이변 기저율
# ================================

def get_xg_upset_rate(home_xg, away_xg):
    """
    두 팀의 xG 차이로 이변 기저율 반환
    wc_historical 분석 결과 기반
    """
    if home_xg is None or away_xg is None:
        return XG_GAP_UPSET_RATE['0.6~1.0']  # 기본값

    gap = abs(home_xg - away_xg)

    if gap < 0.3:
        return XG_GAP_UPSET_RATE['0~0.3']
    elif gap < 0.6:
        return XG_GAP_UPSET_RATE['0.3~0.6']
    elif gap < 1.0:
        return XG_GAP_UPSET_RATE['0.6~1.0']
    elif gap < 1.5:
        return XG_GAP_UPSET_RATE['1.0~1.5']
    else:
        return XG_GAP_UPSET_RATE['1.5+']

# ================================
# 6. 슈팅 효율 기반 이변 가능성
# ================================

def get_shooting_efficiency_factor(
    favorite_shots_on_target,
    underdog_shots_on_target,
    favorite_goals,
    underdog_goals
):
    """
    슈팅 효율 기반 이변 가능성
    승리팀 효율 22.1% vs 패배팀 6.2% (분석 결과)

    실제 경기 데이터 없으면 팀 캐시 기반으로 추정
    """
    if (favorite_shots_on_target is None or
        underdog_shots_on_target is None):
        return 0.5  # 데이터 없으면 중립

    # 슈팅 효율 계산
    fav_eff = (favorite_goals / favorite_shots_on_target
               if favorite_shots_on_target > 0 else 0)
    und_eff = (underdog_goals / underdog_shots_on_target
               if underdog_shots_on_target > 0 else 0)

    # 언더독 효율이 강팀보다 높으면 이변 가능성 UP
    if und_eff > fav_eff:
        return min(und_eff / (fav_eff + 0.01), 1.0)
    else:
        return 0.2

# ================================
# 7. 메인 UVI 계산 함수
# ================================

def calculate_uvi(
    favorite,
    underdog,
    team_cache,
    round_name      = 'Group stage',
    favorite_pts    = 3,
    underdog_pts    = 0,
    home_xg         = None,
    away_xg         = None,
    match_stats     = None,
):
    """
    이변 취약성 지수 (Upset Vulnerability Index) 계산

    Parameters:
        favorite:     예측 우세팀
        underdog:     예측 열세팀
        team_cache:   팀 데이터 캐시
        round_name:   라운드 이름
        favorite_pts: 강팀 현재 승점 (조별리그)
        underdog_pts: 약팀 현재 승점 (조별리그)
        home_xg:      홈팀 xG (있으면)
        away_xg:      원정팀 xG (있으면)
        match_stats:  경기 세부 통계 (있으면)

    반환:
        dict {
            uvi: 0.0~1.0,
            confidence: 신뢰도 레벨,
            factors: 요소별 점수,
            message: 설명
        }
    """
    W = UVI_WEIGHTS

    # ① xG 차이 기반 이변율
    xg_factor = get_xg_upset_rate(home_xg, away_xg)

    # ② 슈팅 효율 (match_stats 있으면 사용, 없으면 기본값)
    if match_stats:
        shooting_factor = get_shooting_efficiency_factor(
            match_stats.get('fav_shots_on_target'),
            match_stats.get('und_shots_on_target'),
            match_stats.get('fav_goals', 0),
            match_stats.get('und_goals', 0),
        )
    else:
        # 팀 캐시 기반 득점력으로 추정
        fav_tc = team_cache.get(favorite, {})
        und_tc = team_cache.get(underdog, {})
        fav_gf = fav_tc.get('gf', 1.2)
        und_gf = und_tc.get('gf', 0.8)
        # 언더독 득점력이 높을수록 이변 가능
        shooting_factor = min(und_gf / (fav_gf + 0.01), 1.0)

    # ③ 점유율 역설 (전술 상성)
    possession_factor = get_tactical_mismatch(
        favorite, underdog, team_cache
    )

    # ④ 라운드별 기저율
    round_factor = ROUND_BASE_UPSET_RATE.get(
        round_name,
        ROUND_BASE_UPSET_RATE['default']
    )

    # ⑤ 압박/절박도 (보조 지표)
    desperation_factor = get_desperation_gap(
        favorite_pts, underdog_pts, round_name
    )

    # ⑥ 원맨팀 취약도 (강팀이 원맨팀이면 더 취약)
    key_man_factor = get_key_man_dependency(favorite)

    # 최종 UVI 계산 (가중 합산)
    uvi = (
        xg_factor         * W['xg_gap']       +
        shooting_factor   * W['shooting_eff'] +
        possession_factor * W['possession']   +
        round_factor      * W['round_rate']   +
        desperation_factor* W['pressure']
    )

    # 원맨팀 보정 (최대 +0.1)
    uvi += key_man_factor * 0.1
    uvi  = min(round(uvi, 3), 1.0)

    # 요소별 점수
    factors = {
        'xg_gap':       round(xg_factor, 3),
        'shooting':     round(shooting_factor, 3),
        'tactical':     round(possession_factor, 3),
        'round':        round(round_factor, 3),
        'desperation':  round(desperation_factor, 3),
        'key_man':      round(key_man_factor, 3),
    }

    return {
        'uvi':        uvi,
        'confidence': get_confidence_level(uvi),
        'factors':    factors,
    }

# ================================
# 8. 신뢰도 레벨 변환
# ================================

def get_confidence_level(uvi):
    """
    UVI → 예측 신뢰도 변환
    """
    if uvi < 0.20:
        return {
            'level':   'HIGH',
            'label':   '✅ 신뢰도 높음',
            'color':   '#00ff88',
            'message': '강팀 승리 가능성 매우 높음',
            'upset_chance': round(uvi * 100, 1),
        }
    elif uvi < 0.35:
        return {
            'level':   'MEDIUM',
            'label':   '🟡 이변 가능',
            'color':   '#ffbb44',
            'message': '변수 존재. 약팀 선전 가능',
            'upset_chance': round(uvi * 100, 1),
        }
    elif uvi < 0.50:
        return {
            'level':   'LOW',
            'label':   '🔴 이변 주의',
            'color':   '#ff7777',
            'message': '이변 발생 조건 다수 충족',
            'upset_chance': round(uvi * 100, 1),
        }
    else:
        return {
            'level':   'CRITICAL',
            'label':   '⚡ 이변 경보',
            'color':   '#ff0000',
            'message': '강팀 패배 가능성 매우 높음',
            'upset_chance': round(uvi * 100, 1),
        }

# ================================
# 9. 전체 조별리그 UVI 계산
# ================================

def calculate_all_group_uvi(team_cache, h2h_cache,
                             continent_winrate, model, top_features):
    """
    2026 월드컵 전체 조별리그 경기 UVI 계산
    이변 가능성 높은 경기 TOP 순위 반환
    """
    from predict import ensemble_predict

    all_matches = []

    for group_name, teams in GROUPS_2026.items():
        for i in range(len(teams)):
            for j in range(i+1, len(teams)):
                home, away = teams[i], teams[j]

                # 기본 예측
                result = ensemble_predict(
                    home, away, team_cache, h2h_cache,
                    continent_winrate, model, top_features
                )

                # 강팀/약팀 판별
                home_tc  = team_cache.get(home, {})
                away_tc  = team_cache.get(away, {})
                home_str = home_tc.get('fpoints', 500)
                away_str = away_tc.get('fpoints', 500)

                if home_str >= away_str:
                    favorite = home
                    underdog = away
                    fav_win  = result['home_win']
                else:
                    favorite = away
                    underdog = home
                    fav_win  = result['away_win']

                # UVI 계산
                uvi_result = calculate_uvi(
                    favorite    = favorite,
                    underdog    = underdog,
                    team_cache  = team_cache,
                    round_name  = 'Group stage',
                    favorite_pts= 0,
                    underdog_pts= 0,
                )

                fav_rank = team_cache.get(favorite, {}).get('rank', 99)
                und_rank = team_cache.get(underdog, {}).get('rank', 99)

                all_matches.append({
                    'group':      group_name,
                    'home':       home,
                    'away':       away,
                    'favorite':   favorite,
                    'underdog':   underdog,
                    'fav_rank':   fav_rank,
                    'und_rank':   und_rank,
                    'fav_win':    fav_win,
                    'home_win':   result['home_win'],
                    'draw':       result['draw'],
                    'away_win':   result['away_win'],
                    'uvi':        uvi_result['uvi'],
                    'confidence': uvi_result['confidence'],
                    'factors':    uvi_result['factors'],
                })

    # UVI 높은 순으로 정렬
    all_matches.sort(key=lambda x: x['uvi'], reverse=True)
    return all_matches