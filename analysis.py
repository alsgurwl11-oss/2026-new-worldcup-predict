# ================================
# analysis.py - 데이터 분석 스크립트
# config.py에 추가할 지수 생성
# ================================
import os
os.chdir('C:\\Users\\alsgu\\2026-new-worldcup-predict')

import pandas as pd
import numpy as np

print("데이터 로딩 중...")

# 데이터 로딩
profiles  = pd.read_csv('data/player_profiles.csv', low_memory=False)
injuries  = pd.read_csv('data/player_injuries.csv')
perf      = pd.read_csv('data/player_performances.csv')
natl      = pd.read_csv('data/player_national_performances.csv')
market    = pd.read_csv('data/player_market_value.csv')

print("✅ 데이터 로딩 완료!")

# ================================
# 설정
# ================================
wc_countries = [
    'South Korea', 'Korea, South', 'Korea Republic',
    'United States', 'England', 'France', 'Brazil',
    'Argentina', 'Germany', 'Spain', 'Portugal',
    'Netherlands', 'Belgium', 'Japan', 'Morocco',
    'Mexico', 'Canada', 'Australia', 'Croatia',
    'Uruguay', 'Colombia', 'Senegal', 'Switzerland',
    'Ecuador', 'Norway', 'Austria', 'Sweden', 'Turkey',
    'Ghana', 'Iran', 'Saudi Arabia', 'Egypt', 'Algeria',
    'Scotland', 'Czech Republic', 'Qatar', 'Panama',
    'Paraguay', 'Tunisia', "Côte d'Ivoire", 'Ivory Coast',
    'Bosnia-Herzegovina', 'Bosnia and Herzegovina',
    'New Zealand', 'Iraq', 'Jordan', 'Uzbekistan',
    'South Africa', 'Haiti', 'Cape Verde', 'Curaçao', 'Curacao',
]

nation_name_map = {
    'Korea, South':         'South Korea',
    "Côte d'Ivoire":        'Ivory Coast',
    'Bosnia-Herzegovina':   'Bosnia and Herzegovina',
    'Curaçao':              'Curacao',
}

recent_seasons = ['23/24', '24/25', '2024', '2025']

def is_wc_player(citizenship):
    if pd.isna(citizenship): return False
    for c in wc_countries:
        if c in str(citizenship): return True
    return False

def extract_primary_nation(citizenship):
    for c in wc_countries:
        if c in str(citizenship):
            return nation_name_map.get(c, c)
    return None

# ================================
# 1. 참가국 선수 필터링
# ================================
print("\n참가국 선수 필터링 중...")
wc_profiles = profiles[profiles['citizenship'].apply(is_wc_player)].copy()
wc_profiles['primary_nation'] = wc_profiles['citizenship'].apply(extract_primary_nation)
wc_player_ids = wc_profiles['player_id'].tolist()
print(f"✅ 참가국 선수: {len(wc_profiles)}명")

# ================================
# 2. 부상 취약도 지수
# ================================
print("\n부상 취약도 계산 중...")
wc_injuries = injuries[injuries['player_id'].isin(wc_player_ids)].copy()
recent_inj  = wc_injuries[
    wc_injuries['season_name'].isin(['23/24', '24/25'])
].merge(
    wc_profiles[['player_id', 'primary_nation']],
    on='player_id'
)

nation_injury = recent_inj.groupby('primary_nation').agg(
    total_injuries  = ('days_missed', 'count'),
    avg_days_missed = ('days_missed', 'mean'),
    total_days      = ('days_missed', 'sum'),
).reset_index()

# 정규화 (0~1)
max_inj = nation_injury['total_injuries'].max()
max_days = nation_injury['avg_days_missed'].max()

nation_injury['injury_index'] = (
    nation_injury['avg_days_missed'] / max_days * 0.5 +
    nation_injury['total_injuries'] / max_inj * 0.5
).round(3)

print("✅ 부상 취약도 계산 완료!")

# ================================
# 3. 시장가치 기반 팀 전력
# ================================
print("\n시장가치 계산 중...")

# 최신 시장가치만
market['date_unix'] = pd.to_datetime(market['date_unix'])
latest_market = market.sort_values('date_unix').groupby('player_id').last().reset_index()

wc_market = latest_market[
    latest_market['player_id'].isin(wc_player_ids)
].merge(
    wc_profiles[['player_id', 'primary_nation']],
    on='player_id'
)

# 국가별 TOP23 평균 시장가치
def top23_avg(group):
    return group.nlargest(23, 'value')['value'].mean()

nation_market = wc_market.groupby('primary_nation').apply(
    top23_avg
).reset_index()
nation_market.columns = ['primary_nation', 'top23_market_value']

# 정규화
max_val = nation_market['top23_market_value'].max()
nation_market['market_strength'] = (
    nation_market['top23_market_value'] / max_val
).round(4)

print("✅ 시장가치 계산 완료!")

# ================================
# 리그 수준 가중치
# ================================
LEAGUE_WEIGHTS = {
    # 빅5 리그 (1.0)
    'Premier League':    1.0,
    'LaLiga':            1.0,
    'Bundesliga':        1.0,
    'Serie A':           1.0,
    'Ligue 1':           1.0,
    # 2군 유럽 (0.85)
    'Eredivisie':        0.85,
    'Primeira Liga':     0.85,
    'Pro League':        0.85,
    'Super Lig':         0.85,
    'Süper Lig':         0.85,
    'Scottish Premiership': 0.80,
    'Championship':      0.75,
    # 남미 (0.80)
    'Série A':           0.80,
    'Liga Profesional':  0.80,
    'Primera División':  0.80,
    # UEFA 기타 (0.75)
    'Ekstraklasa':       0.75,
    'Czech Liga':        0.75,
    'Jupiler Pro League':0.75,
    # 유럽 컵 (0.90)
    'Champions League':  0.90,
    'Europa League':     0.85,
    'Conference League': 0.80,
    # 아시아 (0.60)
    'MLS':               0.65,
    'K League 1':        0.60,
    'K League 2':        0.50,
    'J1 League':         0.60,
    'Saudi Pro League':  0.55,
    'UAE Pro League':    0.50,
    'Chinese Super League': 0.50,
    # 약한 리그 (0.35)
    'Ligue Professionnelle 1': 0.35,  # 알제리
    'Persian Gulf Pro League': 0.45,  # 이란
    'Qatar Stars League':      0.35,  # 카타르
    'Egyptian Premier League': 0.45,
    'Saudi Pro League':        0.55,
}

def get_league_weight(competition_name):
    """리그 수준 가중치 반환"""
    if pd.isna(competition_name):
        return 0.5
    for league, weight in LEAGUE_WEIGHTS.items():
        if league.lower() in str(competition_name).lower():
            return weight
    # 기본값: 리그 이름으로 추정
    name = str(competition_name).lower()
    if any(x in name for x in ['champions', 'europa', 'conference']):
        return 0.85
    elif any(x in name for x in ['premier', 'primera', 'serie', 'liga', 'bundesliga']):
        return 0.75
    elif any(x in name for x in ['second', '2', 'championship', 'division']):
        return 0.55
    elif any(x in name for x in ['cup', 'copa', 'coupe', 'pokal']):
        return 0.70
    return 0.50

# ================================
# 4. 최근 폼 지수 (수정)
# ================================
print("\n최근 폼 계산 중... (리그 가중치 + 출전시간 500분 기준)")

wc_perf = perf[
    (perf['player_id'].isin(wc_player_ids)) &
    (perf['season_name'].isin(recent_seasons))
].merge(
    wc_profiles[['player_id', 'primary_nation', 'position']],
    on='player_id'
)

# 골키퍼 제외
field = wc_perf[
    ~wc_perf['position'].str.contains(
        'Goalkeeper|keeper', na=False, case=False
    )
].copy()

# 리그 가중치 추가
field['league_weight'] = field['competition_name'].apply(get_league_weight)

# 가중 골/어시스트
field['weighted_goals'] = field['goals'] * field['league_weight']
field['weighted_ast']   = field['assists'] * field['league_weight']

# 선수별 합산
player_form = field.groupby(['player_id', 'primary_nation']).agg(
    총출전시간       = ('minutes_played', 'sum'),
    가중골           = ('weighted_goals', 'sum'),
    가중어시스트     = ('weighted_ast', 'sum'),
).reset_index()

# ✅ 출전시간 500분 이상만
player_form = player_form[player_form['총출전시간'] >= 500]

# 선수별 공격 기여도
player_form['weighted_contribution'] = (
    player_form['가중골'] + player_form['가중어시스트']
)

# 국가별 TOP 23 평균
def top23_form(group):
    return group.nlargest(23, 'weighted_contribution')['weighted_contribution'].mean()

nation_form = player_form.groupby('primary_nation').apply(
    top23_form
).reset_index()
nation_form.columns = ['primary_nation', 'form_score']

# 정규화
max_form = nation_form['form_score'].max()
nation_form['form_index'] = (
    nation_form['form_score'] / max_form
).round(4)

print("✅ 폼 지수 계산 완료!")
print(nation_form.sort_values('form_index', ascending=False).head(10).to_string())

# ================================
# 5. 종합 지수 계산
# ================================
print("\n종합 지수 계산 중...")

# 모든 지수 합치기
summary = nation_market.merge(
    nation_form[['primary_nation', 'form_index']],  # attack_contribution 제거!
    on='primary_nation', how='left'
).merge(
    nation_injury[['primary_nation', 'injury_index', 'avg_days_missed']],
    on='primary_nation', how='left'
)

summary = summary.fillna(0)

# 종합 팀 강도
summary['overall_strength'] = (
    summary['market_strength'] * 0.40 +
    summary['form_index']      * 0.35 +
    (1 - summary['injury_index']) * 0.25
).round(4)

summary = summary.sort_values('overall_strength', ascending=False)

print("\n" + "="*60)
print("  2026 월드컵 참가국 종합 강도 지수")
print("="*60)
print(f"{'팀':<30} {'시장가치':>8} {'폼':>8} {'부상':>8} {'종합':>8}")
print("-"*60)
for _, row in summary.iterrows():
    print(f"{row['primary_nation']:<30} "
          f"{row['market_strength']:>8.3f} "
          f"{row['form_index']:>8.3f} "
          f"{row['injury_index']:>8.3f} "
          f"{row['overall_strength']:>8.3f}")

# ================================
# 6. config.py에 추가할 딕셔너리 출력
# ================================
print("\n\n# ===== config.py에 추가할 코드 =====")
print("TEAM_MARKET_STRENGTH = {")
for _, row in summary.iterrows():
    print(f"    '{row['primary_nation']}': {row['market_strength']},")
print("}")

print("\nTEAM_FORM_INDEX = {")
for _, row in summary.iterrows():
    print(f"    '{row['primary_nation']}': {row['form_index']},")
print("}")

print("\nTEAM_INJURY_INDEX = {")
for _, row in summary.iterrows():
    print(f"    '{row['primary_nation']}': {row['injury_index']},")
print("}")

print("\nTEAM_OVERALL_STRENGTH = {")
for _, row in summary.iterrows():
    print(f"    '{row['primary_nation']}': {row['overall_strength']},")
print("}")

