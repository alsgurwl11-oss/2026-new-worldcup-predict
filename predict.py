# ================================
# predict.py - 앙상블 예측 함수
# ================================

import pandas as pd
import numpy as np
from config import (
    OPTA_WIN_PROB, BETTING_ODDS, ENSEMBLE_WEIGHTS,
    GROUPS_2026, TEAM_STRENGTH_FC25, TEAM_STRENGTH_NORMALIZED,
    TEAM_OVERALL_STRENGTH, TEAM_INJURY_INDEX, TEAM_FORM_INDEX,
    MATCH_ODDS_1X2, TEAM_MARKET_STRENGTH,
    DEFAULT_XG, VENUE_XG_MODIFIER,
    ROUND_DEFENSIVE_FACTOR, MAX_GOALS,
    OVER_UNDER_CONFIG, MATCH_ODDS_OU,
)
from scipy.stats import poisson
from motivation import apply_all_adjustments  # PL 교훈 기반 보정 모듈

# ================================
# 1. 강도 계산 함수들
# ================================

def odds_to_prob(odds_plus):
    """미국식 배당률 → 확률 변환"""
    return 100 / (odds_plus + 100)

def get_opta_strength(team):
    """Opta 우승 확률 기반 팀 강도"""
    return OPTA_WIN_PROB.get(team, 0.0001)

def get_betting_strength(team):
    """배당률 기반 팀 강도"""
    return odds_to_prob(BETTING_ODDS.get(team, 500000))

def calculate_elo_prob(home_str, away_str):
    """ELO 방식 승리 확률 계산"""
    diff = home_str - away_str
    return 1 / (1 + 10 ** (-diff * 10))

# ================================
# 2. 소스별 예측 함수
# ================================

def predict_ml(home, away, neutral, team_cache, h2h_cache,
               continent_winrate, model, top_features):
    """XGBoost ML 모델 예측"""
    hc = team_cache.get(home)
    ac = team_cache.get(away)

    if hc is None or ac is None:
        return [0.33, 0.33, 0.34]

    if (home, away) in h2h_cache:
        h2h_home, h2h_draw, h2h_away = h2h_cache[(home, away)]
    elif (away, home) in h2h_cache:
        h2h_away, h2h_draw, h2h_home = h2h_cache[(away, home)]
    else:
        h2h_home = h2h_draw = h2h_away = 0.33

    cont_adv = continent_winrate.get((hc['cont'], ac['cont']), 0.33)

    feat = pd.DataFrame([{
        'fpoints_diff':       hc['fpoints'] - ac['fpoints'],
        'rank_diff':          ac['rank'] - hc['rank'],
        'is_neutral':         int(neutral),
        'home_is_host':       hc.get('is_host_2026', 0),
        'away_is_host':       ac.get('is_host_2026', 0),
        'cont_advantage':     cont_adv,
        'host_cont_penalty':  hc['penalty'] - ac['penalty'],
        'h2h_advantage':      h2h_home - h2h_away,
        'h2h_home_wr':        h2h_home,
        'home_wc_exp':        hc['exp'],
        'away_wc_exp':        ac['exp'],
        'exp_diff':           hc['exp'] - ac['exp'],
        'form_diff':          hc['form'] - ac['form'],
        'home_form':          hc['form'],
        'away_form':          ac['form'],
        'gf_diff':            hc['gf'] - ac['gf'],
        'ga_diff':            hc['ga'] - ac['ga'],
        'home_gf':            hc['gf'],
        'away_gf':            ac['gf'],
        'home_defending': 1 if home == 'Argentina' else 0,
        'away_defending': 1 if away == 'Argentina' else 0,
        'fc25_strength_diff': hc.get('fc25_strength', 0.75) - ac.get('fc25_strength', 0.75),
        'home_fc25_strength': hc.get('fc25_strength', 0.75),
        'away_fc25_strength': ac.get('fc25_strength', 0.75),
        'top23_diff':         hc.get('fc25_top23', 65.0) - ac.get('fc25_top23', 65.0),
        'top11_diff':         hc.get('fc25_top11', 68.0) - ac.get('fc25_top11', 68.0),
        # Transfermarkt 데이터 기반 피처
        'home_overall_strength': TEAM_OVERALL_STRENGTH.get(home, 0.35),
        'away_overall_strength': TEAM_OVERALL_STRENGTH.get(away, 0.35),
        'overall_strength_diff': TEAM_OVERALL_STRENGTH.get(home, 0.35) - TEAM_OVERALL_STRENGTH.get(away, 0.35),
        'home_injury_index':     TEAM_INJURY_INDEX.get(home, 0.3),
        'away_injury_index':     TEAM_INJURY_INDEX.get(away, 0.3),
        'home_form_index':       TEAM_FORM_INDEX.get(home, 0.4),
        'away_form_index':       TEAM_FORM_INDEX.get(away, 0.4),
        'form_index_diff':       TEAM_FORM_INDEX.get(home, 0.4) - TEAM_FORM_INDEX.get(away, 0.4),
    }])

    available = [f for f in top_features if f in feat.columns]
    return model.predict_proba(feat[available])[0].tolist()

def predict_opta(home, away):
    """Opta 강도 기반 예측"""
    h_str = get_opta_strength(home)
    a_str = get_opta_strength(away)
    total = h_str + a_str + 0.001
    h = h_str / total
    a = a_str / total
    d = 0.25
    s = h + d + a
    return h/s, d/s, a/s

def decimal_to_prob(decimal_odds: float) -> float:
    """유럽식 소수 배당 → 확률 변환 (마진 제거 없는 단순 역수)"""
    return 1.0 / decimal_odds if decimal_odds > 0 else 0.0

def predict_betting(home, away):
    """
    배당률 기반 예측
    우선순위:
    1. MATCH_ODDS_1X2 (경기별 1x2 배당) → 가장 정확
    2. BETTING_ODDS (우승 배당 역산) → 폴백
    """
    match_key = (home, away)
    reverse_key = (away, home)

    if match_key in MATCH_ODDS_1X2:
        raw_h, raw_d, raw_a = MATCH_ODDS_1X2[match_key]
        p_h = decimal_to_prob(raw_h)
        p_d = decimal_to_prob(raw_d)
        p_a = decimal_to_prob(raw_a)
        total = p_h + p_d + p_a
        return p_h / total, p_d / total, p_a / total

    elif reverse_key in MATCH_ODDS_1X2:
        raw_a, raw_d, raw_h = MATCH_ODDS_1X2[reverse_key]
        p_h = decimal_to_prob(raw_h)
        p_d = decimal_to_prob(raw_d)
        p_a = decimal_to_prob(raw_a)
        total = p_h + p_d + p_a
        return p_h / total, p_d / total, p_a / total

    # 폴백: 우승 배당 역산
    h_str = get_betting_strength(home)
    a_str = get_betting_strength(away)
    total = h_str + a_str + 0.001
    h = h_str / total
    a = a_str / total
    d = 0.25
    s = h + d + a
    return h/s, d/s, a/s

def predict_elo(home, away):
    """ELO 레이팅 기반 예측"""
    h_str  = get_opta_strength(home)
    a_str  = get_opta_strength(away)
    elo_hw = calculate_elo_prob(h_str, a_str)
    elo_aw = 1 - elo_hw
    d      = 0.25
    s      = elo_hw + d + elo_aw
    return elo_hw/s, d/s, elo_aw/s

def get_match_odds_display(home, away):
    """
    UI 표시용 1x2 배당 반환
    반환: (홈배당, 무배당, 원정배당) 또는 None
    """
    match_key = (home, away)
    reverse_key = (away, home)

    if match_key in MATCH_ODDS_1X2:
        h, d, a = MATCH_ODDS_1X2[match_key]
        return {'home': h, 'draw': d, 'away': a}
    elif reverse_key in MATCH_ODDS_1X2:
        a, d, h = MATCH_ODDS_1X2[reverse_key]
        return {'home': h, 'draw': d, 'away': a}
    return None

def check_low_odds(home, away):
    """
    초저배당 경기 여부 체크 (3번 요구사항)
    배당 1.30 이하면 True → O/U로 강제 전환 권장
    """
    threshold = OVER_UNDER_CONFIG.get('low_odds_1x2_threshold', 1.30)
    odds = get_match_odds_display(home, away)
    if odds is None:
        return False
    return odds['home'] <= threshold or odds['away'] <= threshold

# ================================
# 3. 앙상블 예측 (메인 함수)
# ================================

def ensemble_predict(home, away, team_cache, h2h_cache,
                     continent_winrate, model, top_features,
                     neutral=True, match_context=None, round_name='Group'):
    """
    앙상블 최종 예측
    가중치: ML(20%) + Opta(10%) + 배당(20%) + ELO(15%) + 폼(15%) + 강도(10%) + 동기(5%) + 피드백(5%)
    """
    W = ENSEMBLE_WEIGHTS

    ml_probs = predict_ml(
        home, away, neutral,
        team_cache, h2h_cache,
        continent_winrate, model, top_features
    )
    ml_h, ml_d, ml_a       = ml_probs[2], ml_probs[1], ml_probs[0]
    opta_h, opta_d, opta_a = predict_opta(home, away)
    bet_h,  bet_d,  bet_a  = predict_betting(home, away)
    elo_h,  elo_d,  elo_a  = predict_elo(home, away)

    # --------------------------------
    # form 기반 예측 (TEAM_FORM_INDEX 활용)
    # 최근 경기 폼 지수를 독립 소스로 사용
    # --------------------------------
    home_form_val = TEAM_FORM_INDEX.get(home, 0.4)
    away_form_val = TEAM_FORM_INDEX.get(away, 0.4)
    form_total = home_form_val + away_form_val + 0.001
    form_h = home_form_val / form_total
    form_a = away_form_val / form_total
    form_d = 0.25
    form_s = form_h + form_d + form_a
    form_h, form_d, form_a = form_h/form_s, form_d/form_s, form_a/form_s

    # --------------------------------
    # strength 기반 예측 (FC25 능력치 + 이적시장 가치 복합)
    # 실력 지표를 배당/랭킹과 독립적으로 반영
    # --------------------------------
    home_str_val = (TEAM_STRENGTH_NORMALIZED.get(home, 0.75) + TEAM_MARKET_STRENGTH.get(home, 0.1)) / 2
    away_str_val = (TEAM_STRENGTH_NORMALIZED.get(away, 0.75) + TEAM_MARKET_STRENGTH.get(away, 0.1)) / 2
    str_total = home_str_val + away_str_val + 0.001
    str_h = home_str_val / str_total
    str_a = away_str_val / str_total
    str_d = 0.25
    str_s = str_h + str_d + str_a
    str_h, str_d, str_a = str_h/str_s, str_d/str_s, str_a/str_s

    # --------------------------------
    # 앙상블 합산 (6개 소스)
    # --------------------------------
    fh = (ml_h   * W['ml']
        + opta_h * W['opta']
        + bet_h  * W['betting']
        + elo_h  * W['elo']
        + form_h * W.get('form', 0.15)
        + str_h  * W.get('strength', 0.10))

    fd = (ml_d   * W['ml']
        + opta_d * W['opta']
        + bet_d  * W['betting']
        + elo_d  * W['elo']
        + form_d * W.get('form', 0.15)
        + str_d  * W.get('strength', 0.10))

    fa = (ml_a   * W['ml']
        + opta_a * W['opta']
        + bet_a  * W['betting']
        + elo_a  * W['elo']
        + form_a * W.get('form', 0.15)
        + str_a  * W.get('strength', 0.10))

    total      = fh + fd + fa
    fh, fd, fa = fh/total, fd/total, fa/total

    # --------------------------------
    # 무승부 확률 보정 (2022 오답노트 반영)
    # 오답 25개 중 12개(48%)가 무승부를 못 잡은 것이 원인
    # 양팀 승리 확률이 비슷할수록 → 무승부 상향
    # --------------------------------
    if round_name == 'Group':
        competitiveness = 1 - abs(fh - fa)
        draw_boost = competitiveness * 0.07      # 최대 7% 부스트
        fd = min(fd + draw_boost, 0.42)
        total = fh + fd + fa
        fh, fd, fa = fh/total, fd/total, fa/total

    # --------------------------------
    # 초저배당 체크 (3번 요구사항)
    # 배당 1.30 이하 경기는 1x2 추천 의미없음 → O/U 강제 전환
    # --------------------------------
    is_low_odds = check_low_odds(home, away)

    # --------------------------------
    # motivation.py 통합 보정 적용
    # --------------------------------
    motivation_applied = False
    adj_info = {}

    if match_context is not None:
        home_xg = calculate_team_xg(home, away, team_cache)
        away_xg = calculate_team_xg(away, home, team_cache)

        adj = apply_all_adjustments(
            home, away,
            fh, fd, fa,
            home_xg, away_xg,
            match_context,
            team_cache,
            round_name
        )

        fh = adj['home_prob']
        fd = adj['draw_prob']
        fa = adj['away_prob']
        motivation_applied = True
        adj_info = adj

    # --------------------------------
    # 배당 정보 (1번 요구사항: UI 표시용)
    # --------------------------------
    odds_display = get_match_odds_display(home, away)

    return {
        'home_win':  round(fh * 100, 1),
        'draw':      round(fd * 100, 1),
        'away_win':  round(fa * 100, 1),

        # 1번: 경기 옆 배당 표시용
        'odds': odds_display,

        # 3번: 초저배당 플래그 (프론트에서 O/U 뱃지로 전환)
        'is_low_odds': is_low_odds,

        'detail': {
            'ml':       {'home': round(ml_h*100,1),   'draw': round(ml_d*100,1),   'away': round(ml_a*100,1)},
            'opta':     {'home': round(opta_h*100,1), 'draw': round(opta_d*100,1), 'away': round(opta_a*100,1)},
            'betting':  {'home': round(bet_h*100,1),  'draw': round(bet_d*100,1),  'away': round(bet_a*100,1)},
            'elo':      {'home': round(elo_h*100,1),  'draw': round(elo_d*100,1),  'away': round(elo_a*100,1)},
            'form':     {'home': round(form_h*100,1), 'draw': round(form_d*100,1), 'away': round(form_a*100,1)},
            'strength': {'home': round(str_h*100,1),  'draw': round(str_d*100,1),  'away': round(str_a*100,1)},
        },

        # 보정 정보 (프론트엔드 뱃지 표시용)
        'motivation_applied': motivation_applied,
        'auto_switch_ou':     adj_info.get('auto_switch_ou', False),
        'confidence_1x2':     adj_info.get('confidence_1x2', max(fh, fd, fa)),
        'over_under':         adj_info.get('over_under', None),
        'adjustment_debug':   adj_info.get('debug', {}),
    }

# ================================
# 4. 토너먼트용 순수 승리 확률
# ================================

def get_win_prob_pure(home, away, team_cache, h2h_cache,
                      continent_winrate, model, top_features):
    """무승부 없는 순수 승리 확률 (연장/승부차기 포함)"""
    result     = ensemble_predict(
        home, away, team_cache, h2h_cache,
        continent_winrate, model, top_features
    )
    home_win   = result['home_win'] / 100
    draw       = result['draw'] / 100
    away_win   = result['away_win'] / 100
    home_total = home_win + draw * 0.5
    away_total = away_win + draw * 0.5
    total      = home_total + away_total
    return home_total / total, away_total / total

# ================================
# 5. 조별리그 경기별 예측
# ================================

def predict_group_matches(group_name, team_cache, h2h_cache,
                          continent_winrate, model, top_features):
    """특정 조의 모든 경기 예측 반환"""
    teams   = GROUPS_2026[group_name]
    matches = []

    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            home, away = teams[i], teams[j]
            result     = ensemble_predict(
                home, away, team_cache, h2h_cache,
                continent_winrate, model, top_features
            )
            matches.append({
                'home':        home,
                'away':        away,
                'home_rank':   team_cache.get(home, {}).get('rank', 99),
                'away_rank':   team_cache.get(away, {}).get('rank', 99),
                'home_form':   round(team_cache.get(home, {}).get('form', 0) * 100, 1),
                'away_form':   round(team_cache.get(away, {}).get('form', 0) * 100, 1),
                'home_win':    result['home_win'],
                'draw':        result['draw'],
                'away_win':    result['away_win'],
                'odds':        result['odds'],          # 1번: 배당 추가
                'is_low_odds': result['is_low_odds'],   # 3번: 저배당 플래그
                'detail':      result['detail'],
            })

    return matches

# ================================
# 6. 팀 분석 요약
# ================================

def get_team_analysis(team, team_cache, h2h_cache,
                      continent_winrate, model, top_features):
    """특정 팀의 상세 분석 반환"""
    tc = team_cache.get(team)
    if tc is None:
        return None

    group_name  = None
    group_teams = []
    for gn, teams in GROUPS_2026.items():
        if team in teams:
            group_name  = gn
            group_teams = [t for t in teams if t != team]
            break

    matchups = []
    for opponent in group_teams:
        result = ensemble_predict(
            team, opponent, team_cache, h2h_cache,
            continent_winrate, model, top_features
        )
        matchups.append({
            'opponent': opponent,
            'opp_rank': team_cache.get(opponent, {}).get('rank', 99),
            'win':      result['home_win'],
            'draw':     result['draw'],
            'lose':     result['away_win'],
        })

    return {
        'team':       team,
        'group':      group_name,
        'rank':       tc.get('rank', 99),
        'fpoints':    tc.get('fpoints', 0),
        'form':       round(tc.get('form', 0) * 100, 1),
        'wc_exp':     round(tc.get('exp', 0) * 100, 1),
        'continent':  tc.get('cont', 'OTHER'),
        'is_host':    tc.get('is_host_2026', 0),
        'avg_gf':     round(tc.get('gf', 0), 2),
        'avg_ga':     round(tc.get('ga', 0), 2),
        'opta_prob':  round(get_opta_strength(team) * 100, 2),
        'bet_prob':   round(get_betting_strength(team) * 100, 2),
        'fc25_top23': tc.get('fc25_top23', 65.0),
        'fc25_top11': tc.get('fc25_top11', 68.0),
        'fc25_rank':  sorted(
            TEAM_STRENGTH_FC25.keys(),
            key=lambda x: TEAM_STRENGTH_FC25[x]['top23'],
            reverse=True
        ).index(team) + 1 if team in TEAM_STRENGTH_FC25 else 99,
        'matchups':   matchups,
    }

# ================================
# 7. xG 계산 및 스코어라인 예측
# ================================

def calculate_team_xg(team, opponent, team_cache, venue='neutral'):
    """
    팀의 기대 득점(xG) 계산
    공식: base_xg = 팀 평균득점 × (리그평균실점 / 상대팀 평균실점)
    FC25 능력치 보정 + 홈/원정 보정 추가
    """
    tc = team_cache.get(team, {})
    oc = team_cache.get(opponent, {})

    team_gf    = tc.get('gf', 1.2)
    opp_ga     = oc.get('ga', 1.2)
    league_avg = 1.2

    if opp_ga > 0:
        xg = team_gf * (opp_ga / league_avg)
    else:
        rank = tc.get('rank', 50)
        if rank <= 15:   xg = DEFAULT_XG['strong']
        elif rank <= 40: xg = DEFAULT_XG['mid']
        else:            xg = DEFAULT_XG['weak']

    # FC25 능력치 보정 (1점 차이 = 1%)
    fc25_diff = tc.get('fc25_top11', 68) - oc.get('fc25_top11', 68)
    xg *= (1 + fc25_diff * 0.01)

    # 홈/어웨이 보정
    xg *= VENUE_XG_MODIFIER.get(venue, 1.0)

    return round(max(0.3, min(xg, 3.5)), 2)


def predict_scoreline(home, away, team_cache,
                      venue='neutral', round_name='Group'):
    """
    포아송 분포 기반 예상 스코어라인
    P(홈 h골, 원정 a골) = P_poisson(h, home_xg) × P_poisson(a, away_xg)
    """
    home_xg = calculate_team_xg(home, away, team_cache, venue)
    away_xg = calculate_team_xg(away, home, team_cache, venue)

    # 라운드별 수비 강화 보정
    def_factor = ROUND_DEFENSIVE_FACTOR.get(round_name, 1.0)
    home_xg = round(home_xg * def_factor, 2)
    away_xg = round(away_xg * def_factor, 2)

    # 모든 스코어 조합 확률 계산
    scorelines = []
    for h in range(MAX_GOALS + 1):
        for a in range(MAX_GOALS + 1):
            prob = poisson.pmf(h, home_xg) * poisson.pmf(a, away_xg)
            scorelines.append({
                'home_goals': h,
                'away_goals': a,
                'score':      f"{h}-{a}",
                'prob':       round(prob * 100, 2),
            })

    scorelines.sort(key=lambda x: x['prob'], reverse=True)

    cs_home = round(poisson.pmf(0, away_xg) * 100, 1)
    cs_away = round(poisson.pmf(0, home_xg) * 100, 1)
    btts = round(
        (1 - poisson.pmf(0, home_xg)) *
        (1 - poisson.pmf(0, away_xg)) * 100, 1
    )
    over_25 = round(sum(
        s['prob'] for s in scorelines
        if s['home_goals'] + s['away_goals'] >= 3
    ), 1)
    ou_odds = MATCH_ODDS_OU.get((home, away)) or MATCH_ODDS_OU.get((away, home))

    return {
        'home':             home,
        'away':             away,
        'home_xg':          home_xg,
        'away_xg':          away_xg,
        'expected_total':   round(home_xg + away_xg, 2),
        'top5':             scorelines[:5],
        'all_scorelines':   scorelines[:15],
        'clean_sheet_home': cs_home,
        'clean_sheet_away': cs_away,
        'btts':             btts,
        'over_25':          over_25,
        'under_25':         round(100 - over_25, 1),
        'ou_odds':          ou_odds,  
    }