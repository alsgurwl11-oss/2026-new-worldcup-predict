# ================================
# predict.py - 앙상블 예측 함수
# ================================

import pandas as pd
import numpy as np
from config import (
    OPTA_WIN_PROB, BETTING_ODDS, ENSEMBLE_WEIGHTS,
    GROUPS_2026, TEAM_STRENGTH_FC25, TEAM_STRENGTH_NORMALIZED,
    TEAM_OVERALL_STRENGTH, TEAM_INJURY_INDEX, TEAM_FORM_INDEX
)

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
        'home_defending':     0,
        'away_defending':     0,
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

def predict_betting(home, away):
    """배당률 역산 기반 예측"""
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

# ================================
# 3. 앙상블 예측 (메인 함수)
# ================================

def ensemble_predict(home, away, team_cache, h2h_cache,
                     continent_winrate, model, top_features,
                     neutral=True):
    """앙상블 최종 예측: ML(35%) + Opta(30%) + 배당률(25%) + ELO(10%)"""
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

    fh = ml_h*W['ml'] + opta_h*W['opta'] + bet_h*W['betting'] + elo_h*W['elo']
    fd = ml_d*W['ml'] + opta_d*W['opta'] + bet_d*W['betting'] + elo_d*W['elo']
    fa = ml_a*W['ml'] + opta_a*W['opta'] + bet_a*W['betting'] + elo_a*W['elo']

    total      = fh + fd + fa
    fh, fd, fa = fh/total, fd/total, fa/total

    return {
        'home_win': round(fh * 100, 1),
        'draw':     round(fd * 100, 1),
        'away_win': round(fa * 100, 1),
        'detail': {
            'ml':      {'home': round(ml_h*100,1),   'draw': round(ml_d*100,1),   'away': round(ml_a*100,1)},
            'opta':    {'home': round(opta_h*100,1), 'draw': round(opta_d*100,1), 'away': round(opta_a*100,1)},
            'betting': {'home': round(bet_h*100,1),  'draw': round(bet_d*100,1),  'away': round(bet_a*100,1)},
            'elo':     {'home': round(elo_h*100,1),  'draw': round(elo_d*100,1),  'away': round(elo_a*100,1)},
        }
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
                'home':      home,
                'away':      away,
                'home_rank': team_cache.get(home, {}).get('rank', 99),
                'away_rank': team_cache.get(away, {}).get('rank', 99),
                'home_form': round(team_cache.get(home, {}).get('form', 0) * 100, 1),
                'away_form': round(team_cache.get(away, {}).get('form', 0) * 100, 1),
                'home_win':  result['home_win'],
                'draw':      result['draw'],
                'away_win':  result['away_win'],
                'detail':    result['detail'],
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