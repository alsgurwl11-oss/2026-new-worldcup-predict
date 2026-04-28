# ================================
# analysis_advanced.py - 고급 분석 함수
# 신규 파일 - 프로젝트 루트에 추가
# ================================

import numpy as np
from config import GROUPS_2026, GDI_WEIGHTS


def _normalize(value, min_val, max_val):
    """0~100 정규화"""
    if max_val == min_val:
        return 50.0
    return round((value - min_val) / (max_val - min_val) * 100, 1)


def calculate_group_difficulty(group_name, team_cache):
    """
    조 난이도 지표 (GDI: Group Difficulty Index)

    설계 원리:
      "죽음의 조" = 약한 팀이 없는 조
      → 평균 강도 높고 + 최약체도 강하고 + 팀 간 균형 잡혀있으면 = 죽음의 조

    각 지표를 0~100 정규화 후 GDI_WEIGHTS 가중 합산
    """
    teams = GROUPS_2026[group_name]

    fpoints_list = []
    form_list    = []
    rank_list    = []

    for team in teams:
        tc = team_cache.get(team, {})
        fpoints_list.append(tc.get('fpoints', 500))
        form_list.append(tc.get('form', 0.5))
        rank_list.append(tc.get('rank', 99))

    avg_fpoints = np.mean(fpoints_list)
    min_fpoints = min(fpoints_list)
    std_fpoints = np.std(fpoints_list)
    avg_form    = np.mean(form_list)

    return {
        'group':       group_name,
        'teams':       teams,
        # 원시 지표 (정규화 전)
        'avg_fpoints': round(avg_fpoints, 1),
        'min_fpoints': round(min_fpoints, 1),
        'std_fpoints': round(std_fpoints, 1),
        'avg_form':    round(avg_form * 100, 1),
        'avg_rank':    round(np.mean(rank_list), 1),
        'best_rank':   min(rank_list),
        'worst_rank':  max(rank_list),
        'team_details': [
            {
                'team':    team,
                'rank':    team_cache.get(team, {}).get('rank', 99),
                'fpoints': round(team_cache.get(team, {}).get('fpoints', 500), 1),
                'form':    round(team_cache.get(team, {}).get('form', 0.5) * 100, 1),
            }
            for team in teams
        ],
    }


def calculate_all_groups_difficulty(team_cache):
    """
    전체 조 난이도 순위 계산

    1. 각 조 원시 지표 수집
    2. 전체 조 기준으로 0~100 정규화
    3. GDI_WEIGHTS 가중 합산
    4. 순위 부여 + 라벨 적용
    """
    # 1. 원시 데이터 수집
    raw = []
    for group_name in GROUPS_2026:
        data = calculate_group_difficulty(group_name, team_cache)
        raw.append(data)

    # 2. 정규화를 위한 전체 범위 계산
    all_avg  = [r['avg_fpoints']  for r in raw]
    all_min  = [r['min_fpoints']  for r in raw]
    all_std  = [r['std_fpoints']  for r in raw]
    all_form = [r['avg_form']     for r in raw]

    avg_min,  avg_max  = min(all_avg),  max(all_avg)
    min_min,  min_max  = min(all_min),  max(all_min)
    std_min,  std_max  = min(all_std),  max(all_std)
    form_min, form_max = min(all_form), max(all_form)

    # 3. GDI 계산
    results = []
    for r in raw:
        norm_avg     = _normalize(r['avg_fpoints'], avg_min, avg_max)
        norm_min     = _normalize(r['min_fpoints'], min_min, min_max)
        # 표준편차는 낮을수록 균형 잡힘 → 역정규화
        norm_balance = _normalize(std_max - r['std_fpoints'], 0, std_max - std_min)
        norm_form    = _normalize(r['avg_form'], form_min, form_max)

        gdi = round(
            norm_avg     * GDI_WEIGHTS['avg_strength'] +
            norm_min     * GDI_WEIGHTS['min_strength'] +
            norm_balance * GDI_WEIGHTS['balance']      +
            norm_form    * GDI_WEIGHTS['avg_form'],
            1
        )

        results.append({
            **r,
            'gdi':          gdi,
            'norm_avg':     norm_avg,
            'norm_min':     norm_min,
            'balance':      norm_balance,
            'norm_form':    norm_form,
        })

    # 4. GDI 순 정렬 + 라벨
    results.sort(key=lambda x: x['gdi'], reverse=True)
    labels = ['💀 죽음의 조', '💀 죽음의 조', '💀 죽음의 조',
              '⚠️ 위험한 조', '⚠️ 위험한 조', '⚠️ 위험한 조',
              '😐 보통 조',   '😐 보통 조',   '😐 보통 조',
              '😊 순한 조',   '😊 순한 조',   '😊 순한 조']

    for i, r in enumerate(results):
        r['difficulty_rank']  = i + 1
        r['difficulty_label'] = labels[i]

    return results