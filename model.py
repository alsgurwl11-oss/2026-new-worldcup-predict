# ================================
# model.py - 데이터 로딩 및 모델 학습
# ================================

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from config import (
    NAME_MAP, CONTINENT_MAP, HOST_MAP, PREV_CHAMPIONS,
    SOUTH_AMERICA_HOSTS, EUROPE_HOSTS, GROUPS_2026,
    XGB_PARAMS, DATA_FILES, PREDICT_DATE,
    TEAM_STRENGTH_FC25, TEAM_STRENGTH_NORMALIZED,TEAM_OVERALL_STRENGTH,
    TEAM_INJURY_INDEX,
    TEAM_FORM_INDEX,FIFA_RANKING_2026,
)

# ================================
# 1. 레이블 인코더
# ================================
le = LabelEncoder()
le.fit(['UEFA', 'CONMEBOL', 'CONCACAF', 'AFC', 'CAF', 'OFC', 'OTHER'])

# ================================
# 2. 데이터 로딩
# ================================
def load_match_data():
    """역대 경기 결과 데이터 로딩"""
    df = pd.read_csv(DATA_FILES['results'])
    df = df.dropna(subset=['home_score', 'away_score'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    df=df[df['date'] >= '1992-01-01'].copy().reset_index(drop=True)
    df['result'] = df.apply(_get_result, axis=1)
    print(f"✅ 경기 데이터 로딩 완료: {len(df):,}경기")
    return df

def load_ranking_data():
    """FIFA 랭킹 데이터 로딩"""
    r1 = pd.read_csv(DATA_FILES['ranking_1'])
    r2 = pd.read_csv(DATA_FILES['ranking_2'])
    r3 = pd.read_csv(DATA_FILES['ranking_3'])
    ranking = pd.concat([r1, r2, r3], ignore_index=True)
    ranking['rank_date'] = pd.to_datetime(ranking['rank_date'])
    ranking = ranking.sort_values('rank_date').reset_index(drop=True)
    print(f"✅ FIFA 랭킹 데이터 로딩 완료: {len(ranking):,}행")
    return ranking

def _get_result(row):
    """경기 결과 변환: 홈승=1, 무=0, 홈패=-1"""
    if row['home_score'] > row['away_score']:   return 1
    elif row['home_score'] < row['away_score']: return -1
    else:                                        return 0

# ================================
# 3. 팀 정보 함수들
# ================================
def get_continent(team):
    """팀의 대륙 반환"""
    return CONTINENT_MAP.get(team, 'OTHER')

def get_host_continent_penalty(team_cont, date):
    """개최 대륙 패널티 계산"""
    year = date.year
    if team_cont == 'UEFA' and year in SOUTH_AMERICA_HOSTS:   return -0.1
    if team_cont == 'CONMEBOL' and year in EUROPE_HOSTS:      return -0.1
    return 0.0

def get_fc25_strength(team):
    """FC25 선수 능력치 기반 팀 강도"""
    return TEAM_STRENGTH_NORMALIZED.get(team, 0.75)

def get_fc25_top23(team):
    """FC25 TOP23 평균 능력치"""
    return TEAM_STRENGTH_FC25.get(team, {}).get('top23', 65.0)

def get_fc25_top11(team):
    """FC25 TOP11 평균 능력치"""
    return TEAM_STRENGTH_FC25.get(team, {}).get('top11', 68.0)

def get_fifa_rank(team, date, ranking):
    # 2026년 예측할 때만 하드코딩 적용
    if date.year >= 2025 and team in FIFA_RANKING_2026:
        return FIFA_RANKING_2026[team]
    # 과거 경기는 CSV 방식
    mapped = NAME_MAP.get(team, team)
    past = ranking[
        (ranking['country_full'] == mapped) &
        (ranking['rank_date'] <= date)
    ]
    return int(past.iloc[-1]['rank']) if len(past) > 0 else 100

def get_fifa_points(team, date, ranking):
    """특정 날짜 기준 FIFA 포인트 반환"""
    # 2025년 이전은 CSV 방식
    if date.year < 2025:
        mapped = NAME_MAP.get(team, team)
        past = ranking[
            (ranking['country_full'] == mapped) &
            (ranking['rank_date'] <= date)
        ]
        return float(past.iloc[-1]['total_points']) if len(past) > 0 else 500
    # 2025년 이후는 CSV 최신값 사용
    mapped = NAME_MAP.get(team, team)
    past = ranking[ranking['country_full'] == mapped]
    return float(past.iloc[-1]['total_points']) if len(past) > 0 else 500

def get_team_stats(team, date, df, n=10):
    """최근 n경기 팀 통계 반환"""
    past = df[
        ((df['home_team'] == team) | (df['away_team'] == team)) &
        (df['date'] < date)
    ].tail(n)

    if len(past) == 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    wins = draws = goals_for = goals_against = 0

    for _, row in past.iterrows():
        if row['home_team'] == team:
            gf, ga = row['home_score'], row['away_score']
            if row['result'] == 1:   wins += 1
            elif row['result'] == 0: draws += 1
        else:
            gf, ga = row['away_score'], row['home_score']
            if row['result'] == -1:  wins += 1
            elif row['result'] == 0: draws += 1
        goals_for += gf
        goals_against += ga

    total = len(past)
    return (
        wins / total,
        draws / total,
        goals_for / total,
        goals_against / total,
        (wins * 3 + draws) / total
    )

def get_recent_form(team, date, df, n=5):
    """최근 n경기 폼 점수 반환 (0~1)"""
    past = df[
        ((df['home_team'] == team) | (df['away_team'] == team)) &
        (df['date'] < date)
    ].tail(n)

    if len(past) == 0:
        return 0.0

    points = 0
    for _, row in past.iterrows():
        if row['home_team'] == team:
            if row['result'] == 1:   points += 3
            elif row['result'] == 0: points += 1
        else:
            if row['result'] == -1:  points += 3
            elif row['result'] == 0: points += 1

    return points / (n * 3)

def get_h2h(home, away, date, df, n=10):
    """두 팀의 역대 상대전적 반환"""
    past = df[
        (((df['home_team'] == home) & (df['away_team'] == away)) |
         ((df['home_team'] == away) & (df['away_team'] == home))) &
        (df['date'] < date)
    ].tail(n)

    if len(past) == 0:
        return 0.33, 0.33, 0.33

    home_wins = draws = away_wins = 0

    for _, row in past.iterrows():
        if row['home_team'] == home:
            if row['result'] == 1:   home_wins += 1
            elif row['result'] == 0: draws += 1
            else:                    away_wins += 1
        else:
            if row['result'] == -1:  home_wins += 1
            elif row['result'] == 0: draws += 1
            else:                    away_wins += 1

    total = len(past)
    return home_wins/total, draws/total, away_wins/total

def get_worldcup_experience(team, date, wc_df):
    """월드컵 경험치 반환 (0~1)"""
    past = wc_df[
        ((wc_df['home_team'] == team) | (wc_df['away_team'] == team)) &
        (wc_df['date'] < date)
    ]
    return min(len(past), 30) / 30

# ================================
# 4. 대륙간 상성 계산
# ================================
def calculate_continent_winrate(df):
    """역대 데이터 기반 대륙간 승률 계산"""
    df = df.copy()
    df['home_cont'] = df['home_team'].apply(get_continent)
    df['away_cont'] = df['away_team'].apply(get_continent)

    conts             = ['UEFA', 'CONMEBOL', 'CONCACAF', 'AFC', 'CAF', 'OFC', 'OTHER']
    continent_winrate = {}

    for hc in conts:
        for ac in conts:
            if hc == ac:
                continent_winrate[(hc, ac)] = 0.33
                continue
            filtered = df[
                (df['home_cont'] == hc) & (df['away_cont'] == ac)
            ]
            continent_winrate[(hc, ac)] = (
                float((filtered['result'] == 1).mean())
                if len(filtered) >= 5 else 0.33
            )

    print("✅ 대륙간 상성 계산 완료")
    return continent_winrate

# ================================
# 5. 피처 생성
# ================================
def build_features(wc_df, df, ranking, continent_winrate):
    """월드컵 경기 데이터로 피처 생성"""
    print(f"피처 생성 중... ({len(wc_df)}경기) ☕")
    features = []

    for idx, row in wc_df.iterrows():
        home = row['home_team']
        away = row['away_team']
        date = row['date']

        h_wr, h_dr, h_gf, h_ga, h_pts = get_team_stats(home, date, df)
        a_wr, a_dr, a_gf, a_ga, a_pts = get_team_stats(away, date, df)
        h_form    = get_recent_form(home, date, df)
        a_form    = get_recent_form(away, date, df)
        h_rank    = get_fifa_rank(home, date, ranking)
        a_rank    = get_fifa_rank(away, date, ranking)
        h_fpoints = get_fifa_points(home, date, ranking)
        a_fpoints = get_fifa_points(away, date, ranking)
        h2h_home, h2h_draw, h2h_away = get_h2h(home, away, date, df)
        h_cont    = get_continent(home)
        a_cont    = get_continent(away)
        cont_adv  = continent_winrate.get((h_cont, a_cont), 0.33)
        h_exp     = get_worldcup_experience(home, date, wc_df)
        a_exp     = get_worldcup_experience(away, date, wc_df)
        h_host    = 1 if HOST_MAP.get(home, 0) == date.year else 0
        a_host    = 1 if HOST_MAP.get(away, 0) == date.year else 0
        h_def     = 1 if PREV_CHAMPIONS.get(date.year, '') == home else 0
        a_def     = 1 if PREV_CHAMPIONS.get(date.year, '') == away else 0
        h_penalty = get_host_continent_penalty(h_cont, date)
        a_penalty = get_host_continent_penalty(a_cont, date)

        # FC25 선수 능력치
        h_fc25     = get_fc25_strength(home)
        a_fc25     = get_fc25_strength(away)
        h_top23    = get_fc25_top23(home)
        a_top23    = get_fc25_top23(away)
        h_top11    = get_fc25_top11(home)
        a_top11    = get_fc25_top11(away)

        features.append({
            # FIFA 랭킹 관련
            'fpoints_diff':      h_fpoints - a_fpoints,
            'rank_diff':         a_rank - h_rank,

            # 경기 환경
            'is_neutral':        int(row.get('neutral', False)),
            'home_is_host':      h_host,
            'away_is_host':      a_host,

            # 대륙 관련
            'cont_advantage':    cont_adv,
            'host_cont_penalty': h_penalty - a_penalty,

            # 상대전적
            'h2h_advantage':     h2h_home - h2h_away,
            'h2h_home_wr':       h2h_home,

            # 월드컵 경험
            'home_wc_exp':       h_exp,
            'away_wc_exp':       a_exp,
            'exp_diff':          h_exp - a_exp,

            # 최근 폼
            'form_diff':         h_form - a_form,
            'home_form':         h_form,
            'away_form':         a_form,

            # 득실 관련
            'gf_diff':           h_gf - a_gf,
            'ga_diff':           h_ga - a_ga,
            'home_gf':           h_gf,
            'away_gf':           a_gf,

            # 징크스
            'home_defending':    h_def,
            'away_defending':    a_def,

            # FC25 선수 능력치 (NEW!)
            'fc25_strength_diff': h_fc25 - a_fc25,
            'home_fc25_strength': h_fc25,
            'away_fc25_strength': a_fc25,
            'top23_diff':         h_top23 - a_top23,
            'top11_diff':         h_top11 - a_top11,

            # Transfermarkt 데이터 기반 피처
            'home_overall_strength': TEAM_OVERALL_STRENGTH.get(home, 0.35),
            'away_overall_strength': TEAM_OVERALL_STRENGTH.get(away, 0.35),
            'overall_strength_diff': TEAM_OVERALL_STRENGTH.get(home, 0.35) - TEAM_OVERALL_STRENGTH.get(away, 0.35),
            'home_injury_index':     TEAM_INJURY_INDEX.get(home, 0.3),
            'away_injury_index':     TEAM_INJURY_INDEX.get(away, 0.3),
            'home_form_index':       TEAM_FORM_INDEX.get(home, 0.4),
            'away_form_index':       TEAM_FORM_INDEX.get(away, 0.4),
            'form_index_diff':       TEAM_FORM_INDEX.get(home, 0.4) - TEAM_FORM_INDEX.get(away, 0.4),
        })
        

        if idx % 100 == 0:
            print(f"  진행중... {idx}/{len(wc_df)}")

    print(f"✅ 피처 생성 완료: {len(features[0])}개 피처")
    return pd.DataFrame(features)

# ================================
# 6. 팀 캐시 생성
# ================================
def build_team_cache(df, ranking, wc_df):
    """예측 속도 향상을 위한 팀 데이터 사전 계산"""
    print("팀 데이터 캐싱 중...")
    date       = pd.Timestamp(PREDICT_DATE)
    all_teams  = list(set(
        team for teams in GROUPS_2026.values() for team in teams
    ))
    team_cache = {}

    for team in all_teams:
        h_wr, h_dr, h_gf, h_ga, h_pts = get_team_stats(team, date, df)
        cont = get_continent(team)
        team_cache[team] = {
            'wr':           h_wr,
            'dr':           h_dr,
            'gf':           h_gf,
            'ga':           h_ga,
            'pts':          h_pts,
            'form':         get_recent_form(team, date, df),
            'rank':         get_fifa_rank(team, date, ranking),
            'fpoints':      get_fifa_points(team, date, ranking),
            'exp':          get_worldcup_experience(team, date, wc_df),
            'cont':         cont,
            'penalty':      get_host_continent_penalty(cont, date),
            'is_host_2026': 1 if HOST_MAP.get(team, 0) == 2026 else 0,
            # FC25 추가
            'fc25_strength': get_fc25_strength(team),
            'fc25_top23':    get_fc25_top23(team),
            'fc25_top11':    get_fc25_top11(team),
        } 
        print(f"  {team:<30} 랭킹: {team_cache[team]['rank']}위  폼: {team_cache[team]['form']:.2f}")

    print("✅ 팀 캐싱 완료!")
    return team_cache

def build_h2h_cache(df):
    """조별리그 매칭 H2H 사전 계산"""
    print("H2H 캐싱 중...")
    date      = pd.Timestamp(PREDICT_DATE)
    h2h_cache = {}

    for group_name, teams in GROUPS_2026.items():
        for i in range(len(teams)):
            for j in range(i+1, len(teams)):
                home, away = teams[i], teams[j]
                h2h_cache[(home, away)] = get_h2h(home, away, date, df)

    print("✅ H2H 캐싱 완료!")
    return h2h_cache

# ================================
# 7. 모델 학습
# ================================
def train_model(feat_df, wc_df):
    """XGBoost 모델 학습"""
    top_features = list(feat_df.columns)
    X            = feat_df[top_features]
    y            = wc_df['result']
    label_map    = {-1: 0, 0: 1, 1: 2}
    y_encoded    = y.map(label_map)

    model = XGBClassifier(**XGB_PARAMS)
    model.fit(X, y_encoded)

    # 피처 중요도 출력
    importance = pd.Series(
        model.feature_importances_,
        index=top_features
    ).sort_values(ascending=False)

    print("\n✅ 모델 학습 완료!")
    print("--- 피처 중요도 TOP 10 ---")
    print(importance.head(10))

    return model, top_features

# ================================
# 8. 모델 저장/로딩
# ================================
def save_model(model, top_features, continent_winrate, team_cache, h2h_cache):
    """학습된 모델과 캐시 저장"""
    with open(DATA_FILES['model'], 'wb') as f:
        pickle.dump({
            'model':             model,
            'top_features':      top_features,
            'continent_winrate': continent_winrate,
            'team_cache':        team_cache,
            'h2h_cache':         h2h_cache,
        }, f)
    print(f"✅ 모델 저장 완료! ({DATA_FILES['model']})")

def load_model():
    """저장된 모델 로딩"""
    with open(DATA_FILES['model'], 'rb') as f:
        saved = pickle.load(f)
    print("✅ 모델 로딩 완료!")
    return (
        saved['model'],
        saved['top_features'],
        saved['continent_winrate'],
        saved['team_cache'],
        saved['h2h_cache'],
    )

def model_exists():
    """저장된 모델 파일 존재 여부"""
    return os.path.exists(DATA_FILES['model'])

# ================================
# 9. 초기화 함수 (app.py에서 호출)
# ================================
def initialize():
    """전체 초기화 - 모델 로딩 또는 학습"""

    # 데이터 로딩은 항상 필요
    df      = load_match_data()
    ranking = load_ranking_data()

# 수정 후
    HIGH_QUALITY = [
    'FIFA World Cup',
    'FIFA World Cup qualification',
    'UEFA Euro',
    'UEFA Euro qualification',
    'Copa América',
    'African Cup of Nations',
    'AFC Asian Cup',
    'UEFA Nations League',
    'CONCACAF Nations League',
    'Gold Cup',
    ]
    wc_df = df[df['tournament'].isin(HIGH_QUALITY)].copy().reset_index(drop=True)
    print(f"✅ 월드컵 경기: {len(wc_df)}경기")

    if model_exists():
        print("\n저장된 모델 불러오는 중... (빠름!) 🚀")
        model, top_features, continent_winrate, team_cache, h2h_cache = load_model()
    else:
        print("\n첫 실행 - 모델 학습 중... (5~10분 소요) ☕")
        continent_winrate = calculate_continent_winrate(df)
        feat_df           = build_features(wc_df, df, ranking, continent_winrate)
        model, top_features = train_model(feat_df, wc_df)
        team_cache        = build_team_cache(df, ranking, wc_df)
        h2h_cache         = build_h2h_cache(df)
        save_model(model, top_features, continent_winrate, team_cache, h2h_cache)

    return model, top_features, continent_winrate, team_cache, h2h_cache, df, ranking, wc_df