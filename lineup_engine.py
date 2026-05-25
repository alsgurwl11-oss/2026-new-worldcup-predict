# ================================
# lineup_engine.py - 라인업 엔진
# FC26 데이터 기반 팀별 베스트11 자동 구성
# 포메이션 상성 계산 → 예측 확률 보정
# ================================

import pandas as pd
import numpy as np

def safe_int(val, default=0):
    """NaN 안전 int 변환"""
    try:
        if pd.isna(val): return default
        return int(val)
    except:
        return default

def safe_str(val, default=''):
    """NaN 안전 str 변환"""
    try:
        if pd.isna(val): return default
        return str(val)
    except:
        return default
# --------------------------------
# FC26 국가명 → 프로젝트 팀명 매핑
# --------------------------------
FC26_TO_PROJECT = {
    'Korea Republic':        'South Korea',
    'Czechia':               'Czech Republic',
    'DR Congo':              'DR Congo',
    "Côte d'Ivoire":         'Ivory Coast',
    'Bosnia-Herzegovina':    'Bosnia and Herzegovina',
    'Curaçao':               'Curacao',
    'United States':         'United States',
    'England':               'England',
    'France':                'France',
    'Spain':                 'Spain',
    'Brazil':                'Brazil',
    'Argentina':             'Argentina',
    'Germany':               'Germany',
    'Portugal':              'Portugal',
    'Netherlands':           'Netherlands',
    'Belgium':               'Belgium',
    'Japan':                 'Japan',
    'Morocco':               'Morocco',
    'Croatia':               'Croatia',
    'Uruguay':               'Uruguay',
    'Mexico':                'Mexico',
    'Colombia':              'Colombia',
    'Senegal':               'Senegal',
    'Ecuador':               'Ecuador',
    'Norway':                'Norway',
    'Austria':               'Austria',
    'Sweden':                'Sweden',
    'Turkey':                'Turkey',
    'Australia':             'Australia',
    'Canada':                'Canada',
    'Scotland':              'Scotland',
    'Switzerland':           'Switzerland',
    'Paraguay':              'Paraguay',
    'Algeria':               'Algeria',
    'Iran':                  'Iran',
    'Egypt':                 'Egypt',
    'Ghana':                 'Ghana',
    'Saudi Arabia':          'Saudi Arabia',
    'Tunisia':               'Tunisia',
    'South Africa':          'South Africa',
    'Qatar':                 'Qatar',
    'Iraq':                  'Iraq',
    'Jordan':                'Jordan',
    'Uzbekistan':            'Uzbekistan',
    'New Zealand':           'New Zealand',
    'Haiti':                 'Haiti',
    'Panama':                'Panama',
    'Cape Verde':            'Cape Verde',
}

# 역방향 매핑 (프로젝트 → FC26)
PROJECT_TO_FC26 = {v: k for k, v in FC26_TO_PROJECT.items()}

# --------------------------------
# 포메이션 정의
# 각 포메이션별 필요 포지션 슬롯
# --------------------------------
FORMATIONS = {
    '4-3-3':   ['GK', 'LB', 'CB', 'CB', 'RB', 'CM', 'CM', 'CM', 'LW', 'ST', 'RW'],
    '4-2-3-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CDM', 'LM', 'CAM', 'RM', 'ST'],
    '4-4-2':   ['GK', 'LB', 'CB', 'CB', 'RB', 'LM', 'CM', 'CM', 'RM', 'ST', 'ST'],
    '3-5-2':   ['GK', 'CB', 'CB', 'CB', 'LWB', 'CM', 'CM', 'CDM', 'RWB', 'ST', 'ST'],
    '5-3-2':   ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'CM', 'CM', 'CM', 'ST', 'ST'],
    '4-1-4-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'LM', 'CM', 'CM', 'RM', 'ST'],
}

# 팀별 주 포메이션 (2025 기준 감독 전술)
TEAM_DEFAULT_FORMATION = {
    'Spain':                  '4-3-3',
    'France':                 '4-2-3-1',
    'England':                '4-2-3-1',
    'Brazil':                 '4-2-3-1',
    'Argentina':              '4-3-3',
    'Germany':                '4-2-3-1',
    'Portugal':               '4-2-3-1',
    'Netherlands':            '4-3-3',
    'Belgium':                '4-3-3',
    'Norway':                 '4-3-3',
    'Colombia':               '4-2-3-1',
    'Uruguay':                '4-4-2',
    'Mexico':                 '4-3-3',
    'United States':          '4-2-3-1',
    'Japan':                  '4-2-3-1',
    'Morocco':                '4-2-3-1',
    'Senegal':                '4-3-3',
    'South Korea':            '4-2-3-1',
    'Croatia':                '4-3-3',
    'Ecuador':                '4-4-2',
    'Australia':              '4-4-2',
    'Canada':                 '4-2-3-1',
    'Switzerland':            '4-2-3-1',
    'Austria':                '4-2-3-1',
    'Sweden':                 '4-4-2',
    'Scotland':               '3-5-2',
    'Turkey':                 '4-2-3-1',
    'Algeria':                '4-3-3',
    'Iran':                   '4-2-3-1',
    'Egypt':                  '4-2-3-1',
    'Ghana':                  '4-2-3-1',
    'Paraguay':               '4-4-2',
    'Saudi Arabia':           '4-2-3-1',
    'Tunisia':                '4-4-2',
    'South Africa':           '4-4-2',
    'Qatar':                  '5-3-2',
    'Iraq':                   '4-2-3-1',
    'Jordan':                 '4-4-2',
    'Uzbekistan':             '4-2-3-1',
    'New Zealand':            '4-4-2',
    'Haiti':                  '4-4-2',
    'Panama':                 '4-4-2',
    'Cape Verde':             '4-4-2',
    'Ivory Coast':            '4-3-3',
    'DR Congo':               '4-2-3-1',
    'Bosnia and Herzegovina': '4-3-3',
    'Curacao':                '4-4-2',
    'Czech Republic':         '4-2-3-1',
}

# --------------------------------
# 포지션 슬롯별 FC26 포지션 우선순위
# 선수 player_positions에서 이 순서대로 매칭
# --------------------------------
SLOT_PRIORITY = {
    'GK':  ['GK'],
    'CB':  ['CB', 'LCB', 'RCB', 'LB', 'RB'],
    'LB':  ['LB', 'LWB', 'CB'],
    'RB':  ['RB', 'RWB', 'CB'],
    'LWB': ['LWB', 'LB', 'LM'],
    'RWB': ['RWB', 'RB', 'RM'],
    'CDM': ['CDM', 'LDM', 'RDM', 'CM'],
    'CM':  ['CM', 'LCM', 'RCM', 'CDM', 'CAM'],
    'CAM': ['CAM', 'LAM', 'RAM', 'CM', 'LM', 'RM'],
    'LM':  ['LM', 'LW', 'LF', 'CAM', 'RM'],
    'RM':  ['RM', 'RW', 'RF', 'CAM', 'LM'],
    'LW':  ['LW', 'LM', 'LF', 'CAM', 'ST'],
    'RW':  ['RW', 'RM', 'RF', 'CAM', 'ST'],
    'ST':  ['ST', 'LS', 'RS', 'CF', 'LF', 'RF', 'LW', 'RW'],
}

# --------------------------------
# 포메이션 상성 매트릭스
# (공격팀_포메이션, 수비팀_포메이션) → 보정값 (-5 ~ +5%)
# 양수 = 공격팀 유리, 음수 = 불리
# --------------------------------
FORMATION_MATCHUP = {
    # 4-3-3 기준
    ('4-3-3',   '4-4-2'):   +3,   # 중원 수적 우위
    ('4-3-3',   '5-3-2'):   -2,   # 3백에 측면 막힘
    ('4-3-3',   '5-4-1'):   -3,   # 수비블록에 고전
    ('4-3-3',   '4-2-3-1'): +1,   # 중원 약간 우위
    ('4-3-3',   '3-5-2'):   +2,   # 3백 vs 윙어 유리
    # 4-2-3-1 기준
    ('4-2-3-1', '4-4-2'):   +2,   # CAM 활용 공간
    ('4-2-3-1', '4-3-3'):   -1,   # 중원 살짝 불리
    ('4-2-3-1', '5-3-2'):   -1,   # 수비적 팀에 고전
    ('4-2-3-1', '3-5-2'):   +3,   # 3백 측면 공략
    # 3-5-2 기준
    ('3-5-2',   '4-3-3'):   +2,   # 윙백으로 측면 장악
    ('3-5-2',   '4-4-2'):   +1,   # 중원 5명 우위
    ('3-5-2',   '4-2-3-1'): -2,   # 좁은 중원 고전
    # 4-4-2 기준
    ('4-4-2',   '4-3-3'):   -2,   # 중원 수적 열세
    ('4-4-2',   '4-2-3-1'): -2,   # 중원 조직력 열세
    ('4-4-2',   '3-5-2'):   +1,   # 투톱 vs 3백 유리
}

# --------------------------------
# 포지션별 능력치 가중치
# 라인업 강도 계산에 사용
# --------------------------------
POSITION_STAT_WEIGHTS = {
    'GK':  {'goalkeeping_reflexes': 0.3, 'goalkeeping_diving': 0.2,
             'goalkeeping_positioning': 0.2, 'goalkeeping_handling': 0.15,
             'goalkeeping_kicking': 0.15},
    'DEF': {'defending': 0.40, 'physic': 0.25, 'pace': 0.20, 'passing': 0.15},
    'MID': {'passing': 0.30, 'dribbling': 0.25, 'physic': 0.20,
             'defending': 0.15, 'pace': 0.10},
    'ATT': {'pace': 0.30, 'shooting': 0.30, 'dribbling': 0.25, 'physic': 0.15},
}

SLOT_TYPE = {
    'GK': 'GK', 'CB': 'DEF', 'LB': 'DEF', 'RB': 'DEF',
    'LWB': 'DEF', 'RWB': 'DEF', 'CDM': 'MID', 'CM': 'MID',
    'CAM': 'ATT', 'LM': 'ATT', 'RM': 'ATT', 'LW': 'ATT',
    'RW': 'ATT', 'ST': 'ATT',
}

# ================================
# FC26 데이터 로딩 (캐싱)
# ================================
_fc26_cache = None

def load_fc26(path='data/FC26_20250921.csv'):
    """FC26 데이터 로딩 (한번만 로딩 후 캐싱)"""
    global _fc26_cache
    if _fc26_cache is not None:
        return _fc26_cache

    df = pd.read_csv(path, low_memory=False)

    # 능력치 숫자 변환
    stat_cols = ['overall', 'pace', 'shooting', 'passing',
                 'dribbling', 'defending', 'physic',
                 'goalkeeping_reflexes', 'goalkeeping_diving',
                 'goalkeeping_positioning', 'goalkeeping_handling',
                 'goalkeeping_kicking']
    for col in stat_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    _fc26_cache = df
    print(f" OK FC26 데이터 로딩 완료: {len(df)}명")
    return df


# ================================
# 선수 포지션 매칭 함수
# ================================
def player_fits_slot(player_positions_str, slot):
    """선수의 포지션이 슬롯에 맞는지 확인"""
    if pd.isna(player_positions_str):
        return False, 99
    player_pos = [p.strip() for p in str(player_positions_str).split(',')]
    priorities = SLOT_PRIORITY.get(slot, [slot])
    for i, pos in enumerate(priorities):
        if pos in player_pos:
            return True, i  # (적합여부, 우선순위)
    return False, 99


def get_player_stat(row, slot):
    """포지션 타입에 맞는 능력치 계산"""
    slot_type = SLOT_TYPE.get(slot, 'MID')
    weights = POSITION_STAT_WEIGHTS[slot_type]
    score = 0
    for col, w in weights.items():
        score += row.get(col, 0) * w
    return round(score, 1)


# ================================
# 팀별 라인업 자동 구성
# ================================
def build_lineup(team, formation=None, fc26_df=None):
    """
    팀의 FC26 베스트11 자동 구성

    Args:
        team: 프로젝트 팀명 (예: 'South Korea')
        formation: 포메이션 (None이면 팀 기본값)
        fc26_df: FC26 데이터프레임

    Returns:
        dict: {
            formation, slots, players, strength,
            avg_overall, attack_str, defense_str, mid_str
        }
    """
    if fc26_df is None:
        fc26_df = load_fc26()

    # 포메이션 결정
    if formation is None:
        formation = TEAM_DEFAULT_FORMATION.get(team, '4-3-3')

    # FC26 국가명으로 변환
    fc26_nation = PROJECT_TO_FC26.get(team, team)

    # 해당 국적 선수 풀
    pool = fc26_df[fc26_df['nationality_name'] == fc26_nation].copy()

    if len(pool) == 0:
        return _empty_lineup(team, formation)

    # 포메이션 슬롯 목록
    slots = FORMATIONS.get(formation, FORMATIONS['4-3-3'])

    selected = []       # 선발 선수 목록
    used_ids = set()    # 중복 방지

    # CB 슬롯 먼저 처리 (전문 CB가 LB로 빠지는 문제 방지)
    slot_order = ['GK'] + [s for s in slots if s == 'CB'] + \
                 [s for s in slots if s not in ['GK', 'CB']]

    for slot in slot_order:
        best_player = None
        best_score = -1
        best_priority = 99

        for _, player in pool.iterrows():
            pid = player['player_id']
            if pid in used_ids:
                continue

            fits, priority = player_fits_slot(player['player_positions'], slot)
            if not fits:
                continue

            stat_score = get_player_stat(player, slot)
            # 우선순위 높고 + 능력치 높은 선수 선택
            score = stat_score - priority * 2

            if score > best_score:
                best_score = score
                best_priority = priority
                best_player = player

        if best_player is not None:
            used_ids.add(best_player['player_id'])
            selected.append({
                'slot':      slot,
                'name':      safe_str(best_player['short_name']),
                'overall':   safe_int(best_player['overall'], 70),
                'positions': safe_str(best_player['player_positions']),
                'pace':      safe_int(best_player.get('pace', 0)),
                'shooting':  safe_int(best_player.get('shooting', 0)),
                'passing':   safe_int(best_player.get('passing', 0)),
                'dribbling': safe_int(best_player.get('dribbling', 0)),
                'defending': safe_int(best_player.get('defending', 0)),
                'physic':    safe_int(best_player.get('physic', 0)),
                'club':      safe_str(best_player.get('club_name', '')),
                'stat_score': round(best_score, 1),
            })
        else:
            # 해당 포지션 선수 없으면 overall 기준 best
            remaining = pool[~pool['player_id'].isin(used_ids)]
            if len(remaining) > 0:
                bp = remaining.nlargest(1, 'overall').iloc[0]
                used_ids.add(bp['player_id'])
                selected.append({
                    'slot':      slot,
                    'name':      bp['short_name'],
                    'overall':   int(bp['overall']),
                    'positions': bp['player_positions'],
                    'pace':      int(bp.get('pace', 0)),
                    'shooting':  int(bp.get('shooting', 0)),
                    'passing':   int(bp.get('passing', 0)),
                    'dribbling': int(bp.get('dribbling', 0)),
                    'defending': int(bp.get('defending', 0)),
                    'physic':    int(bp.get('physic', 0)),
                    'club':      bp.get('club_name', ''),
                    'stat_score': 0,
                })

    return _calculate_lineup_strength(team, formation, slots, selected)


def _empty_lineup(team, formation):
    """선수 데이터 없을 때 빈 라인업"""
    return {
        'team':        team,
        'formation':   formation,
        'slots':       FORMATIONS.get(formation, []),
        'players':     [],
        'strength':    0.5,
        'avg_overall': 70,
        'attack_str':  0.5,
        'defense_str': 0.5,
        'mid_str':     0.5,
    }


def _calculate_lineup_strength(team, formation, slots, players):
    """라인업 강도 계산"""
    if not players:
        return _empty_lineup(team, formation)

    overalls = [p['overall'] for p in players]
    avg_overall = round(np.mean(overalls), 1)

    # 포지션별 강도 분리
    att_scores, def_scores, mid_scores = [], [], []
    for p in players:
        t = SLOT_TYPE.get(p['slot'], 'MID')
        if t == 'ATT':
            att_scores.append(p['overall'])
        elif t == 'DEF':
            def_scores.append(p['overall'])
        elif t == 'MID':
            mid_scores.append(p['overall'])

    # 0~1 정규화 (overall 60~95 범위 기준)
    def normalize(scores):
        if not scores:
            return 0.5
        return round((np.mean(scores) - 60) / 35, 3)

    return {
        'team':        team,
        'formation':   formation,
        'slots':       slots,
        'players':     players,
        'strength':    round((avg_overall - 60) / 35, 3),
        'avg_overall': avg_overall,
        'attack_str':  normalize(att_scores),
        'defense_str': normalize(def_scores),
        'mid_str':     normalize(mid_scores),
    }


# ================================
# 포메이션 상성 보정값 계산
# ================================
def get_formation_bonus(home_formation, away_formation):
    """
    포메이션 상성에 따른 홈팀 보정값 반환 (%)
    양수 = 홈팀 유리, 음수 = 원정팀 유리
    """
    bonus = FORMATION_MATCHUP.get((home_formation, away_formation), 0)
    return bonus  # -5 ~ +5


# ================================
# 라인업 강도 기반 예측 보정
# ================================
def calculate_lineup_adjustment(home_lineup, away_lineup):
    """
    두 팀 라인업 강도 비교 → 예측 확률 보정값 반환

    Returns:
        dict: {
            home_boost: 홈팀 승리확률 보정 (%p),
            formation_bonus: 포메이션 상성 보정 (%p),
            total_home_adj: 총 홈팀 보정값 (%p)
        }
    """
    # 1. 라인업 강도 차이 보정
    home_str = home_lineup.get('strength', 0.5)
    away_str = away_lineup.get('strength', 0.5)
    str_diff = home_str - away_str

    # 강도 차이 → 확률 보정 (최대 ±8%p)
    lineup_boost = round(str_diff * 15, 1)
    lineup_boost = max(-8, min(8, lineup_boost))

    # 2. 포메이션 상성 보정
    formation_bonus = get_formation_bonus(
        home_lineup.get('formation', '4-3-3'),
        away_lineup.get('formation', '4-3-3')
    )

    # 3. 공격/수비 매칭 보정
    home_att = home_lineup.get('attack_str', 0.5)
    away_def = away_lineup.get('defense_str', 0.5)
    away_att = away_lineup.get('attack_str', 0.5)
    home_def = home_lineup.get('defense_str', 0.5)

    # 공격 vs 상대수비 우위
    att_vs_def = (home_att - away_def) - (away_att - home_def)
    att_bonus = round(att_vs_def * 8, 1)
    att_bonus = max(-5, min(5, att_bonus))

    total = round(lineup_boost + formation_bonus * 0.1 + att_bonus * 0.5, 1)
    total = max(-10, min(10, total))

    return {
        'home_boost':       lineup_boost,
        'formation_bonus':  formation_bonus,
        'att_bonus':        att_bonus,
        'total_home_adj':   total,
    }


# ================================
# 커스텀 라인업 강도 계산
# (사용자가 직접 수정한 라인업용)
# ================================
def calculate_custom_lineup_strength(team, formation, player_overalls):
    """
    사용자 커스텀 라인업 강도 계산

    Args:
        team: 팀명
        formation: 포메이션
        player_overalls: [{slot, overall}, ...] 형태

    Returns:
        라인업 강도 dict
    """
    slots = FORMATIONS.get(formation, FORMATIONS['4-3-3'])
    players = []

    for item in player_overalls:
        slot = item.get('slot', 'CM')
        overall = item.get('overall', 75)
        players.append({
            'slot':    slot,
            'overall': overall,
            'name':    item.get('name', ''),
        })

    return _calculate_lineup_strength(team, formation, slots, players)


# ================================
# 전체 팀 기본 라인업 사전 로딩
# (앱 시작 시 캐싱용)
# ================================
_lineup_cache = {}

def preload_all_lineups(groups, fc26_df=None):
    """
    전체 참가팀 기본 라인업 미리 계산 (캐싱)
    """
    global _lineup_cache
    if fc26_df is None:
        fc26_df = load_fc26()

    all_teams = [t for teams in groups.values() for t in teams]
    for team in all_teams:
        _lineup_cache[team] = build_lineup(team, fc26_df=fc26_df)

    print(f" OK 전체 라인업 캐싱 완료: {len(_lineup_cache)}팀")
    return _lineup_cache


def get_cached_lineup(team):
    """캐시된 라인업 반환"""
    return _lineup_cache.get(team)


# ================================
# 테스트용 메인
# ================================
if __name__ == '__main__':
    import os
    os.chdir('C:\\Users\\alsgu\\2026-new-worldcup-predict')

    df = load_fc26()

    # 한국 라인업 테스트
    lineup = build_lineup('South Korea', formation='4-2-3-1', fc26_df=df)
    print(f"\n{'='*50}")
    print(f"  {lineup['team']} [{lineup['formation']}]")
    print(f"  평균 오버롤: {lineup['avg_overall']} | 강도: {lineup['strength']:.3f}")
    print(f"  공격: {lineup['attack_str']:.3f} | 미드: {lineup['mid_str']:.3f} | 수비: {lineup['defense_str']:.3f}")
    print(f"{'='*50}")
    for p in lineup['players']:
        print(f"  [{p['slot']:4s}] {p['name']:<20} OVR:{p['overall']} | {p['positions']}")

    # 포메이션 상성 테스트
    print(f"\n포메이션 상성 테스트:")
    print(f"  4-3-3 vs 4-4-2: {get_formation_bonus('4-3-3', '4-4-2'):+d}%")
    print(f"  4-2-3-1 vs 3-5-2: {get_formation_bonus('4-2-3-1', '3-5-2'):+d}%")
    print(f"  5-3-2 vs 4-3-3: {get_formation_bonus('5-3-2', '4-3-3'):+d}%")