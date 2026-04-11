# ================================
# simulate.py - 시뮬레이션 함수
# ================================

import numpy as np
from config import GROUPS_2026, SIM_CONFIG
from predict import ensemble_predict, get_win_prob_pure

# ================================
# 1. 공통 유틸 함수
# ================================

def _play_group_match(home, away, matchup_cache):
    """
    조별리그 단일 경기 시뮬레이션
    반환: (home_goals, away_goals, home_points, away_points)
    """
    hw   = matchup_cache.get((home, away), 0.5)
    dw   = 0.25
    rand = np.random.random()

    if rand < hw * 0.75:
        # 홈팀 승
        hg = max(1, int(np.random.poisson(1.8)))
        ag = max(0, int(np.random.poisson(0.7)))
        hp, ap = 3, 0
    elif rand < hw * 0.75 + dw:
        # 무승부
        hg = int(np.random.poisson(1.1))
        ag = hg
        hp, ap = 1, 1
    else:
        # 원정팀 승
        hg = max(0, int(np.random.poisson(0.7)))
        ag = max(1, int(np.random.poisson(1.8)))
        hp, ap = 0, 3

    return hg, ag, hp, ap

def _play_knockout(t1, t2, matchup_cache):
    """
    토너먼트 단판 승부 (승부차기 포함)
    """
    hw = matchup_cache.get((t1, t2), 0.5)
    return t1 if np.random.random() < hw else t2

def _sort_group(teams, points, gd, gf):
    """
    승점 → 득실차 → 다득점 순 정렬
    """
    return sorted(
        teams,
        key=lambda t: (points[t], gd[t], gf[t]),
        reverse=True
    )

def _simulate_one_group(teams, matchup_cache):
    """
    단일 조 1회 시뮬레이션
    반환: sorted_teams, points, gd, gf
    """
    points = {t: 0 for t in teams}
    gd     = {t: 0 for t in teams}
    gf     = {t: 0 for t in teams}

    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            home, away       = teams[i], teams[j]
            hg, ag, hp, ap   = _play_group_match(home, away, matchup_cache)
            points[home] += hp
            points[away] += ap
            gd[home] += hg - ag
            gd[away] += ag - hg
            gf[home] += hg
            gf[away] += ag

    return _sort_group(teams, points, gd, gf), points, gd, gf

def _build_matchup_cache(all_teams, team_cache, h2h_cache,
                         continent_winrate, model, top_features):
    """
    모든 팀 조합의 승리 확률 사전 계산
    토너먼트 시뮬레이션 속도 향상용
    """
    matchup_cache = {}
    for i, t1 in enumerate(all_teams):
        for t2 in all_teams[i+1:]:
            hw, aw = get_win_prob_pure(
                t1, t2, team_cache, h2h_cache,
                continent_winrate, model, top_features
            )
            matchup_cache[(t1, t2)] = hw
            matchup_cache[(t2, t1)] = aw
    return matchup_cache

def _select_best_thirds(third_place_list, n=8):
    """
    3위팀 중 성적 우수 n팀 선발
    """
    third_place_list.sort(
        key=lambda x: (x['points'], x['gd'], x['gf']),
        reverse=True
    )
    return [t['team'] for t in third_place_list[:n]]

# ================================
# 2. 조별리그 시뮬레이션
# ================================

def simulate_group(group_name, team_cache, h2h_cache,
                   continent_winrate, model, top_features,
                   n_sim=None):
    """
    단일 조 시뮬레이션
    반환: 팀별 순위 확률 및 32강 진출 확률
    """
    if n_sim is None:
        n_sim = SIM_CONFIG['group']

    teams = GROUPS_2026[group_name]

    # 경기 확률 미리 계산
    match_probs = {}
    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            home, away = teams[i], teams[j]
            result     = ensemble_predict(
                home, away, team_cache, h2h_cache,
                continent_winrate, model, top_features
            )
            hw, aw = get_win_prob_pure(
                home, away, team_cache, h2h_cache,
                continent_winrate, model, top_features
            )
            match_probs[(home, away)] = hw
            match_probs[(away, home)] = aw

    rank_count    = {t: [0,0,0,0] for t in teams}
    qualify_count = {t: 0 for t in teams}
    points_total  = {t: 0 for t in teams}

    for _ in range(n_sim):
        sorted_teams, points, gd, gf = _simulate_one_group(teams, match_probs)

        for rank, team in enumerate(sorted_teams):
            rank_count[team][rank] += 1
            points_total[team]     += points[team]
            if rank < 2:
                qualify_count[team] += 1

    result = []
    for team in teams:
        result.append({
            'team':       team,
            'rank':       team_cache.get(team, {}).get('rank', 99),
            'form':       round(team_cache.get(team, {}).get('form', 0) * 100, 1),
            'first':      round(rank_count[team][0] / n_sim * 100, 1),
            'second':     round(rank_count[team][1] / n_sim * 100, 1),
            'third':      round(rank_count[team][2] / n_sim * 100, 1),
            'fourth':     round(rank_count[team][3] / n_sim * 100, 1),
            'qualify':    round(qualify_count[team] / n_sim * 100, 1),
            'avg_points': round(points_total[team] / n_sim, 1),
        })

    result.sort(key=lambda x: x['qualify'], reverse=True)
    return result

def simulate_all_groups(team_cache, h2h_cache,
                        continent_winrate, model, top_features,
                        n_sim=None):
    """
    전체 12개 조 시뮬레이션
    반환: 조별 결과 딕셔너리
    """
    if n_sim is None:
        n_sim = SIM_CONFIG['all_groups']

    all_results = {}
    for group_name in GROUPS_2026.keys():
        all_results[group_name] = simulate_group(
            group_name, team_cache, h2h_cache,
            continent_winrate, model, top_features,
            n_sim=n_sim
        )
    return all_results

# ================================
# 3. 전체 토너먼트 시뮬레이션
# ================================

def simulate_tournament(team_cache, h2h_cache,
                        continent_winrate, model, top_features,
                        n_sim=None):
    """
    전체 대회 시뮬레이션 (조별리그 → 결승)
    반환: 팀별 각 라운드 진출 확률
    """
    if n_sim is None:
        n_sim = SIM_CONFIG['tournament']

    all_teams     = list(set(
        team for teams in GROUPS_2026.values() for team in teams
    ))
    matchup_cache = _build_matchup_cache(
        all_teams, team_cache, h2h_cache,
        continent_winrate, model, top_features
    )

    champion_count = {}
    final_count    = {}
    semi_count     = {}
    quarter_count  = {}

    for _ in range(n_sim):
        group_results = {}
        third_place   = []

        # 조별리그
        for group_name, teams in GROUPS_2026.items():
            sorted_teams, points, gd, gf = _simulate_one_group(
                teams, matchup_cache
            )
            group_results[group_name] = sorted_teams
            third_place.append({
                'team':   sorted_teams[2],
                'points': points[sorted_teams[2]],
                'gd':     gd[sorted_teams[2]],
                'gf':     gf[sorted_teams[2]],
            })

        # 3위팀 8개 선발
        best_thirds = _select_best_thirds(third_place, n=8)

        # 32강 진출팀 구성
        r32 = []
        for gn, st in group_results.items():
            r32.append(st[0])
            r32.append(st[1])
        r32.extend(best_thirds)
        current = r32[:32]

        # 토너먼트 진행
        for round_name in ['32강', '16강', '8강', '4강', '결승']:
            next_round = []
            for i in range(0, len(current), 2):
                if i+1 < len(current):
                    t1, t2  = current[i], current[i+1]
                    winner  = _play_knockout(t1, t2, matchup_cache)
                    next_round.append(winner)

                    if round_name == '8강':
                        quarter_count[t1] = quarter_count.get(t1, 0) + 1
                        quarter_count[t2] = quarter_count.get(t2, 0) + 1
                    elif round_name == '4강':
                        semi_count[t1] = semi_count.get(t1, 0) + 1
                        semi_count[t2] = semi_count.get(t2, 0) + 1
                    elif round_name == '결승':
                        final_count[t1]    = final_count.get(t1, 0) + 1
                        final_count[t2]    = final_count.get(t2, 0) + 1
                        champion_count[winner] = champion_count.get(winner, 0) + 1

            current = next_round

    result = []
    for team in all_teams:
        result.append({
            'team':     team,
            'rank':     team_cache.get(team, {}).get('rank', 99),
            'champion': round(champion_count.get(team, 0) / n_sim * 100, 1),
            'final':    round(final_count.get(team, 0) / n_sim * 100, 1),
            'semi':     round(semi_count.get(team, 0) / n_sim * 100, 1),
            'quarter':  round(quarter_count.get(team, 0) / n_sim * 100, 1),
        })

    result.sort(key=lambda x: x['champion'], reverse=True)
    return result

# ================================
# 4. 브라켓 시뮬레이션
# ================================

def simulate_bracket(team_cache, h2h_cache,
                     continent_winrate, model, top_features,
                     n_sim=None):
    """
    토너먼트 브라켓 시뮬레이션
    각 팀의 라운드별 진출 확률 + 예상 상대 TOP3
    """
    if n_sim is None:
        n_sim = SIM_CONFIG['bracket']

    all_teams     = list(set(
        team for teams in GROUPS_2026.values() for team in teams
    ))
    matchup_cache = _build_matchup_cache(
        all_teams, team_cache, h2h_cache,
        continent_winrate, model, top_features
    )

    reach_count    = {t: {'r32':0,'r16':0,'qf':0,'sf':0,'final':0,'champion':0}
                      for t in all_teams}
    opponent_count = {t: {} for t in all_teams}

    for _ in range(n_sim):
        group_results = {}
        third_place   = []

        for group_name, teams in GROUPS_2026.items():
            sorted_teams, points, gd, gf = _simulate_one_group(
                teams, matchup_cache
            )
            group_results[group_name] = sorted_teams
            third_place.append({
                'team':   sorted_teams[2],
                'points': points[sorted_teams[2]],
                'gd':     gd[sorted_teams[2]],
                'gf':     gf[sorted_teams[2]],
            })

        best_thirds = _select_best_thirds(third_place, n=8)

        r32 = []
        for gn, st in group_results.items():
            r32.append(st[0])
            r32.append(st[1])
        r32.extend(best_thirds)

        for team in r32:
            reach_count[team]['r32'] += 1

        current = r32[:32]
        for round_name in ['r16', 'qf', 'sf', 'final', 'champion']:
            next_round = []
            for i in range(0, len(current), 2):
                if i+1 < len(current):
                    t1, t2  = current[i], current[i+1]
                    winner  = _play_knockout(t1, t2, matchup_cache)

                    # 상대 기록
                    opponent_count[t1][t2] = opponent_count[t1].get(t2, 0) + 1
                    opponent_count[t2][t1] = opponent_count[t2].get(t1, 0) + 1

                    reach_count[winner][round_name] += 1
                    next_round.append(winner)

            current = next_round

    team_results = []
    for team in all_teams:
        rc  = reach_count[team]
        ops = sorted(
            opponent_count[team].items(),
            key=lambda x: x[1], reverse=True
        )[:3]

        team_results.append({
            'team':      team,
            'rank':      team_cache.get(team, {}).get('rank', 99),
            'r32':       round(rc['r32']      / n_sim * 100, 1),
            'r16':       round(rc['r16']      / n_sim * 100, 1),
            'qf':        round(rc['qf']       / n_sim * 100, 1),
            'sf':        round(rc['sf']       / n_sim * 100, 1),
            'final':     round(rc['final']    / n_sim * 100, 1),
            'champion':  round(rc['champion'] / n_sim * 100, 1),
            'opponents': [
                {'team': o, 'prob': round(c/n_sim*100, 1)}
                for o, c in ops
            ],
        })

    team_results.sort(key=lambda x: x['champion'], reverse=True)
    return team_results

# ================================
# 5. 한국 시나리오 시뮬레이션
# ================================

def simulate_korea_scenario(team_cache, h2h_cache,
                             continent_winrate, model, top_features,
                             target_team='South Korea', n_sim=None):
    """
    특정 팀(기본: 한국)의 시나리오 분석
    - 라운드별 진출 확률
    - 라운드별 예상 상대 TOP8
    """
    if n_sim is None:
        n_sim = SIM_CONFIG['korea']

    all_teams     = list(set(
        team for teams in GROUPS_2026.values() for team in teams
    ))
    matchup_cache = _build_matchup_cache(
        all_teams, team_cache, h2h_cache,
        continent_winrate, model, top_features
    )

    rounds    = {'group':0,'r32':0,'r16':0,'qf':0,'sf':0,'final':0,'champion':0}
    opponents = {}

    # 라운드별 상대 기록
    round_opponents = {
        'r32': {}, 'r16': {}, 'qf': {},
        'sf': {}, 'final': {}, 'champion': {}
    }

    for _ in range(n_sim):
        group_results = {}
        third_place   = []

        for group_name, teams in GROUPS_2026.items():
            sorted_teams, points, gd, gf = _simulate_one_group(
                teams, matchup_cache
            )
            group_results[group_name] = sorted_teams
            third_place.append({
                'team':   sorted_teams[2],
                'points': points[sorted_teams[2]],
                'gd':     gd[sorted_teams[2]],
                'gf':     gf[sorted_teams[2]],
            })

        best_thirds = _select_best_thirds(third_place, n=8)

        r32 = []
        for gn, st in group_results.items():
            r32.append(st[0])
            r32.append(st[1])
        r32.extend(best_thirds)

        if target_team not in r32:
            rounds['group'] += 1
            continue

        rounds['r32'] += 1
        current      = r32[:32]
        team_alive   = True

        for round_name in ['r16', 'qf', 'sf', 'final', 'champion']:
            next_round = []
            for i in range(0, len(current), 2):
                if i+1 < len(current):
                    t1, t2 = current[i], current[i+1]

                    if team_alive and target_team in [t1, t2]:
                        opp    = t2 if t1 == target_team else t1
                        winner = _play_knockout(t1, t2, matchup_cache)

                        # 전체 상대 기록
                        opponents[opp] = opponents.get(opp, 0) + 1

                        # 라운드별 상대 기록
                        round_opponents[round_name][opp] = \
                            round_opponents[round_name].get(opp, 0) + 1

                        if winner == target_team:
                            rounds[round_name] += 1
                            next_round.append(winner)
                        else:
                            team_alive = False
                    else:
                        next_round.append(
                            _play_knockout(t1, t2, matchup_cache)
                        )

            if not team_alive:
                break
            current = next_round

    # 전체 예상 상대 TOP8
    ops_sorted = sorted(
        opponents.items(), key=lambda x: x[1], reverse=True
    )[:8]

    # 라운드별 예상 상대 TOP3
    round_ops_sorted = {}
    for rn, ops in round_opponents.items():
        sorted_ops = sorted(ops.items(), key=lambda x: x[1], reverse=True)[:3]
        round_ops_sorted[rn] = [
            {'team': o, 'prob': round(c/n_sim*100, 1)}
            for o, c in sorted_ops
        ]

    return {
        'team': target_team,
        'rounds': {
            'group_exit': round(rounds['group']    / n_sim * 100, 1),
            'r32':        round(rounds['r32']      / n_sim * 100, 1),
            'r16':        round(rounds['r16']      / n_sim * 100, 1),
            'qf':         round(rounds['qf']       / n_sim * 100, 1),
            'sf':         round(rounds['sf']       / n_sim * 100, 1),
            'final':      round(rounds['final']    / n_sim * 100, 1),
            'champion':   round(rounds['champion'] / n_sim * 100, 1),
        },
        'likely_opponents': [
            {'team': o, 'prob': round(c/n_sim*100, 1)}
            for o, c in ops_sorted
        ],
        'round_opponents': round_ops_sorted,
    }