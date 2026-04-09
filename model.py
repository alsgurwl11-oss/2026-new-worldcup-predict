import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

# ================================
# 1. 데이터 불러오기
# ================================
df = pd.read_csv('results.csv')
df = df.dropna(subset=['home_score', 'away_score'])
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

def get_result(row):
    if row['home_score'] > row['away_score']:   return 1
    elif row['home_score'] < row['away_score']: return -1
    else:                                        return 0

df['result'] = df.apply(get_result, axis=1)
print(f"전체 경기 데이터: {len(df)}경기")

wc = df[df['tournament'] == 'FIFA World Cup'].copy()
wc = wc.reset_index(drop=True)
print(f"월드컵 경기: {len(wc)}경기")

# ================================
# 2. FIFA 랭킹 데이터
# ================================
r1 = pd.read_csv('fifa_ranking-2023-07-20.csv')
r2 = pd.read_csv('fifa_ranking-2024-04-04.csv')
r3 = pd.read_csv('fifa_ranking-2024-06-20.csv')
ranking = pd.concat([r1, r2, r3], ignore_index=True)
ranking['rank_date'] = pd.to_datetime(ranking['rank_date'])
ranking = ranking.sort_values('rank_date').reset_index(drop=True)
print(f"FIFA 랭킹 데이터: {len(ranking)}행")

# ================================
# 3. 팀 이름 매핑
# ================================
name_map = {
    'South Korea':            'Korea Republic',
    'United States':          'USA',
    'Ivory Coast':            "Côte d'Ivoire",
    'Bosnia and Herzegovina': 'Bosnia-Herzegovina',
    'Cape Verde':             'Cape Verde',
    'Trinidad and Tobago':    'Trinidad and Tobago',
}

# ================================
# 4. 대륙 정보
# ================================
continent_map = {
    'Brazil': 'CONMEBOL', 'Argentina': 'CONMEBOL', 'Uruguay': 'CONMEBOL',
    'Colombia': 'CONMEBOL', 'Chile': 'CONMEBOL', 'Paraguay': 'CONMEBOL',
    'Peru': 'CONMEBOL', 'Ecuador': 'CONMEBOL', 'Bolivia': 'CONMEBOL',
    'Venezuela': 'CONMEBOL',
    'Germany': 'UEFA', 'France': 'UEFA', 'Spain': 'UEFA', 'Italy': 'UEFA',
    'England': 'UEFA', 'Netherlands': 'UEFA', 'Portugal': 'UEFA',
    'Belgium': 'UEFA', 'Croatia': 'UEFA', 'Poland': 'UEFA',
    'Switzerland': 'UEFA', 'Denmark': 'UEFA', 'Sweden': 'UEFA',
    'Norway': 'UEFA', 'Austria': 'UEFA', 'Czech Republic': 'UEFA',
    'Serbia': 'UEFA', 'Hungary': 'UEFA', 'Romania': 'UEFA',
    'Russia': 'UEFA', 'Ukraine': 'UEFA', 'Wales': 'UEFA',
    'Scotland': 'UEFA', 'Turkey': 'UEFA', 'Greece': 'UEFA',
    'Bosnia and Herzegovina': 'UEFA',
    'South Korea': 'AFC', 'Japan': 'AFC', 'Australia': 'AFC',
    'Iran': 'AFC', 'Saudi Arabia': 'AFC', 'China': 'AFC',
    'Qatar': 'AFC', 'Iraq': 'AFC',
    'Mexico': 'CONCACAF', 'United States': 'CONCACAF', 'Canada': 'CONCACAF',
    'Costa Rica': 'CONCACAF', 'Honduras': 'CONCACAF', 'Jamaica': 'CONCACAF',
    'Panama': 'CONCACAF', 'Trinidad and Tobago': 'CONCACAF',
    'Cameroon': 'CAF', 'Nigeria': 'CAF', 'Ghana': 'CAF',
    'Senegal': 'CAF', 'Morocco': 'CAF', 'Egypt': 'CAF',
    'Ivory Coast': 'CAF', 'Algeria': 'CAF', 'Tunisia': 'CAF',
    'South Africa': 'CAF', 'Angola': 'CAF', 'Togo': 'CAF',
}

def get_continent(team):
    return continent_map.get(team, 'OTHER')

le = LabelEncoder()
le.fit(['UEFA', 'CONMEBOL', 'CONCACAF', 'AFC', 'CAF', 'OTHER'])

# ================================
# 5. 개최국 정보
# ================================
host_map = {
    'Uruguay': 1930, 'Italy': 1934, 'France': 1938,
    'Brazil': 1950, 'Switzerland': 1954, 'Sweden': 1958,
    'Chile': 1962, 'England': 1966, 'Mexico': 1970,
    'Germany': 1974, 'Argentina': 1978, 'Spain': 1982,
    'Mexico': 1986, 'Italy': 1990, 'United States': 1994,
    'France': 1998, 'South Korea': 2002, 'Japan': 2002,
    'Germany': 2006, 'South Africa': 2010, 'Brazil': 2014,
    'Russia': 2018, 'Qatar': 2022,
}

def is_host(team, date):
    return int(host_map.get(team, 0) == date.year)

# ================================
# 6. 대륙간 상성 계산
# ================================
print("대륙간 상성 계산 중...")
df['home_cont'] = df['home_team'].apply(get_continent)
df['away_cont'] = df['away_team'].apply(get_continent)

continent_winrate = {}
conts = ['UEFA', 'CONMEBOL', 'CONCACAF', 'AFC', 'CAF', 'OTHER']
for hc in conts:
    for ac in conts:
        if hc == ac:
            continent_winrate[(hc, ac)] = 0.33
            continue
        filtered = df[
            (df['home_cont'] == hc) &
            (df['away_cont'] == ac)
        ]
        if len(filtered) < 5:
            continent_winrate[(hc, ac)] = 0.33
        else:
            continent_winrate[(hc, ac)] = (filtered['result'] == 1).mean()

def get_continent_advantage(home_cont, away_cont):
    return continent_winrate.get((home_cont, away_cont), 0.33)

# ================================
# 7. 전 대회 우승팀 징크스
# ================================
prev_champions = {
    1934: 'Uruguay',   1938: 'Italy',     1950: 'Italy',
    1954: 'Uruguay',   1958: 'Germany',   1962: 'Brazil',
    1966: 'Brazil',    1970: 'England',   1974: 'Brazil',
    1978: 'Germany',   1982: 'Argentina', 1986: 'Italy',
    1990: 'Argentina', 1994: 'Germany',   1998: 'Brazil',
    2002: 'France',    2006: 'Brazil',    2010: 'Italy',
    2014: 'Spain',     2018: 'Germany',   2022: 'France',
}

def is_defending_champion(team, date):
    return int(prev_champions.get(date.year, '') == team)

# ================================
# 8. 대륙 개최 패널티
# ================================
south_america_hosts = [1930, 1950, 1962, 1978, 2014]
europe_hosts = [1934, 1938, 1954, 1958, 1966, 1974, 1982, 1990, 1998, 2006]

def get_host_continent_penalty(team_cont, date):
    year = date.year
    if team_cont == 'UEFA' and year in south_america_hosts:
        return -0.1
    if team_cont == 'CONMEBOL' and year in europe_hosts:
        return -0.1
    return 0.0

# ================================
# 9. 핵심 함수들
# ================================
def get_fifa_rank(team, date):
    mapped = name_map.get(team, team)
    past = ranking[
        (ranking['country_full'] == mapped) &
        (ranking['rank_date'] <= date)
    ]
    if len(past) == 0:
        return 100
    return past.iloc[-1]['rank']

def get_fifa_points(team, date):
    mapped = name_map.get(team, team)
    past = ranking[
        (ranking['country_full'] == mapped) &
        (ranking['rank_date'] <= date)
    ]
    if len(past) == 0:
        return 500
    return past.iloc[-1]['total_points']

def get_team_stats(team, date, n=10):
    past = df[
        ((df['home_team'] == team) | (df['away_team'] == team)) &
        (df['date'] < date)
    ].tail(n)
    if len(past) == 0:
        return 0, 0, 0, 0, 0
    wins = draws = 0
    goals_for = goals_against = 0
    for _, row in past.iterrows():
        if row['home_team'] == team:
            gf, ga = row['home_score'], row['away_score']
            if row['result'] == 1:    wins += 1
            elif row['result'] == 0:  draws += 1
        else:
            gf, ga = row['away_score'], row['home_score']
            if row['result'] == -1:   wins += 1
            elif row['result'] == 0:  draws += 1
        goals_for += gf
        goals_against += ga
    total = len(past)
    return (wins/total, draws/total,
            goals_for/total, goals_against/total,
            (wins*3 + draws)/total)

def get_recent_form(team, date, n=5):
    past = df[
        ((df['home_team'] == team) | (df['away_team'] == team)) &
        (df['date'] < date)
    ].tail(n)
    if len(past) == 0:
        return 0
    points = 0
    for _, row in past.iterrows():
        if row['home_team'] == team:
            if row['result'] == 1:    points += 3
            elif row['result'] == 0:  points += 1
        else:
            if row['result'] == -1:   points += 3
            elif row['result'] == 0:  points += 1
    return points / (n * 3)

def get_h2h(home, away, date, n=10):
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
            if row['result'] == 1:    home_wins += 1
            elif row['result'] == 0:  draws += 1
            else:                     away_wins += 1
        else:
            if row['result'] == -1:   home_wins += 1
            elif row['result'] == 0:  draws += 1
            else:                     away_wins += 1
    total = len(past)
    return home_wins/total, draws/total, away_wins/total

def get_worldcup_experience(team, date):
    past = wc[
        ((wc['home_team'] == team) | (wc['away_team'] == team)) &
        (wc['date'] < date)
    ]
    return min(len(past), 30) / 30

# ================================
# 10. 피처 만들기
# ================================
print("\n피처 생성 중... (5~10분 소요 ☕)")

features = []
for idx, row in wc.iterrows():
    home = row['home_team']
    away = row['away_team']
    date = row['date']

    h_wr, h_dr, h_gf, h_ga, h_pts = get_team_stats(home, date)
    a_wr, a_dr, a_gf, a_ga, a_pts = get_team_stats(away, date)
    h_form    = get_recent_form(home, date)
    a_form    = get_recent_form(away, date)
    h_rank    = get_fifa_rank(home, date)
    a_rank    = get_fifa_rank(away, date)
    h_fpoints = get_fifa_points(home, date)
    a_fpoints = get_fifa_points(away, date)
    h2h_home, h2h_draw, h2h_away = get_h2h(home, away, date)
    h_cont    = get_continent(home)
    a_cont    = get_continent(away)
    cont_adv  = get_continent_advantage(h_cont, a_cont)
    h_exp     = get_worldcup_experience(home, date)
    a_exp     = get_worldcup_experience(away, date)
    h_host    = is_host(home, date)
    h_def     = is_defending_champion(home, date)
    h_penalty = get_host_continent_penalty(h_cont, date)
    a_penalty = get_host_continent_penalty(a_cont, date)

    features.append({
        'fpoints_diff':      h_fpoints - a_fpoints,
        'rank_diff':         a_rank - h_rank,
        'is_neutral':        int(row.get('neutral', False)),
        'cont_advantage':    cont_adv,
        'h2h_advantage':     h2h_home - h2h_away,
        'home_wc_exp':       h_exp,
        'away_wc_exp':       a_exp,
        'exp_diff':          h_exp - a_exp,
        'form_diff':         h_form - a_form,
        'gf_diff':           h_gf - a_gf,
        'ga_diff':           h_ga - a_ga,
        'home_is_host':      h_host,
        'h2h_home_wr':       h2h_home,
        'home_defending':    h_def,
        'host_cont_penalty': h_penalty - a_penalty,
    })

    if idx % 100 == 0:
        print(f"  진행중... {idx}/{len(wc)}")

feat_df = pd.DataFrame(features)
print(f"피처 생성 완료! 피처 수: {len(feat_df.columns)}개")

# ================================
# 11. 학습/테스트 분리
# ================================
top_features = list(feat_df.columns)
X = feat_df[top_features]
y = wc['result']

label_map = {-1: 0, 0: 1, 1: 2}
y_encoded = y.map(label_map)

split = int(len(X) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y_encoded[:split], y_encoded[split:]

print(f"\n학습 데이터: {len(X_train)}경기")
print(f"테스트 데이터: {len(X_test)}경기")

# ================================
# 12. 모델 학습
# ================================
lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train, y_train)
lr_acc = accuracy_score(y_test, lr.predict(X_test))

xgb = XGBClassifier(
    n_estimators=200,
    max_depth=3,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=3,
    random_state=42,
    eval_metric='mlogloss',
    verbosity=0
)
xgb.fit(X_train, y_train)
xgb_acc = accuracy_score(y_test, xgb.predict(X_test))

cv_scores = cross_val_score(xgb, X, y_encoded, cv=5, scoring='accuracy')

# ================================
# 13. 결과 출력
# ================================
print(f"\n--- 모델 비교 ---")
print(f"로지스틱 회귀: {lr_acc:.1%}")
print(f"XGBoost:      {xgb_acc:.1%}")
print(f"\n--- 교차검증 (5폴드) ---")
print(f"평균 정확도: {cv_scores.mean():.1%}")
print(f"표준편차:   {cv_scores.std():.1%}")

print(f"\n--- 피처 중요도 TOP 10 ---")
importance = pd.Series(
    xgb.feature_importances_,
    index=top_features
).sort_values(ascending=False)
print(importance.head(10))

# ================================
# 14. 팀 데이터 캐싱
# ================================
print("\n팀 데이터 캐싱 중...")

all_teams = [
    'Mexico', 'South Korea', 'South Africa', 'Czech Republic',
    'Canada', 'Bosnia and Herzegovina', 'Qatar', 'Switzerland',
    'Brazil', 'Morocco', 'Haiti', 'Scotland',
    'United States', 'Paraguay', 'Australia', 'Turkey',
    'Germany', 'Curacao', 'Ivory Coast', 'Ecuador',
    'Netherlands', 'Japan', 'Sweden', 'Tunisia',
    'Belgium', 'Egypt', 'Iran', 'New Zealand',
    'Spain', 'Cape Verde', 'Saudi Arabia', 'Uruguay',
    'France', 'Senegal', 'Norway', 'Iraq',
    'Argentina', 'Algeria', 'Austria', 'Jordan',
    'Portugal', 'Uzbekistan', 'Colombia',
    'England', 'Croatia', 'Ghana', 'Panama',
]

date = pd.Timestamp('2024-06-20')

team_cache = {}
for team in all_teams:
    h_wr, h_dr, h_gf, h_ga, h_pts = get_team_stats(team, date)
    team_cache[team] = {
        'wr':      h_wr,
        'dr':      h_dr,
        'gf':      h_gf,
        'ga':      h_ga,
        'pts':     h_pts,
        'form':    get_recent_form(team, date),
        'rank':    get_fifa_rank(team, date),
        'fpoints': get_fifa_points(team, date),
        'exp':     get_worldcup_experience(team, date),
        'cont':    get_continent(team),
        'penalty': get_host_continent_penalty(get_continent(team), date),
    }
    print(f"  {team} (랭킹: {team_cache[team]['rank']}위)")

print("캐싱 완료!")

# ================================
# 15. H2H 캐싱
# ================================
print("\nH2H 캐싱 중...")

groups_2026 = {
    'A': ['Mexico', 'South Korea', 'South Africa', 'Czech Republic'],
    'B': ['Canada', 'Bosnia and Herzegovina', 'Qatar', 'Switzerland'],
    'C': ['Brazil', 'Morocco', 'Haiti', 'Scotland'],
    'D': ['United States', 'Paraguay', 'Australia', 'Turkey'],
    'E': ['Germany', 'Curacao', 'Ivory Coast', 'Ecuador'],
    'F': ['Netherlands', 'Japan', 'Sweden', 'Tunisia'],
    'G': ['Belgium', 'Egypt', 'Iran', 'New Zealand'],
    'H': ['Spain', 'Cape Verde', 'Saudi Arabia', 'Uruguay'],
    'I': ['France', 'Senegal', 'Norway', 'Iraq'],
    'J': ['Argentina', 'Algeria', 'Austria', 'Jordan'],
    'K': ['Portugal', 'Uzbekistan', 'Colombia', 'Iraq'],
    'L': ['England', 'Croatia', 'Ghana', 'Panama'],
}

h2h_cache = {}
for group_name, teams in groups_2026.items():
    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            home, away = teams[i], teams[j]
            h2h_cache[(home, away)] = get_h2h(home, away, date)

print("H2H 캐싱 완료!")

# ================================
# 16. 경기 확률 계산 함수
# ================================
def get_match_probs_fast(home, away, neutral=True):
    hc = team_cache[home]
    ac = team_cache[away]

    if (home, away) in h2h_cache:
        h2h_home, h2h_draw, h2h_away = h2h_cache[(home, away)]
    elif (away, home) in h2h_cache:
        h2h_away, h2h_draw, h2h_home = h2h_cache[(away, home)]
    else:
        h2h_home = h2h_draw = h2h_away = 0.33

    h_cont  = hc['cont']
    a_cont  = ac['cont']
    cont_adv = get_continent_advantage(h_cont, a_cont)

    feat = pd.DataFrame([{
        'fpoints_diff':      hc['fpoints'] - ac['fpoints'],
        'rank_diff':         ac['rank'] - hc['rank'],
        'is_neutral':        int(neutral),
        'cont_advantage':    cont_adv,
        'h2h_advantage':     h2h_home - h2h_away,
        'home_wc_exp':       hc['exp'],
        'away_wc_exp':       ac['exp'],
        'exp_diff':          hc['exp'] - ac['exp'],
        'form_diff':         hc['form'] - ac['form'],
        'gf_diff':           hc['gf'] - ac['gf'],
        'ga_diff':           hc['ga'] - ac['ga'],
        'home_is_host':      0,
        'h2h_home_wr':       h2h_home,
        'home_defending':    0,
        'host_cont_penalty': hc['penalty'] - ac['penalty'],
    }])

    return xgb.predict_proba(feat[top_features])[0]

# ================================
# 17. 조별리그 시뮬레이터
# ================================
def simulate_group_fast(group_name, teams, n_sim=10000):
    matches = []
    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            matches.append((teams[i], teams[j]))

    match_probs = {}
    for home, away in matches:
        match_probs[(home, away)] = get_match_probs_fast(home, away)

    rank_count    = {t: [0,0,0,0] for t in teams}
    qualify_count = {t: 0 for t in teams}

    for _ in range(n_sim):
        points = {t: 0 for t in teams}
        gd     = {t: 0 for t in teams}
        gf     = {t: 0 for t in teams}

        for home, away in matches:
            probs    = match_probs[(home, away)]
            home_win = probs[2]
            draw     = probs[1]

            rand = np.random.random()
            if rand < home_win:
                points[home] += 3
                hg = max(1, int(np.random.poisson(1.5)))
                ag = max(0, int(np.random.poisson(0.8)))
            elif rand < home_win + draw:
                points[home] += 1
                points[away] += 1
                hg = int(np.random.poisson(1.0))
                ag = hg
            else:
                points[away] += 3
                hg = max(0, int(np.random.poisson(0.8)))
                ag = max(1, int(np.random.poisson(1.5)))

            gd[home] += hg - ag
            gd[away] += ag - hg
            gf[home] += hg
            gf[away] += ag

        sorted_teams = sorted(
            teams,
            key=lambda t: (points[t], gd[t], gf[t]),
            reverse=True
        )

        for rank, team in enumerate(sorted_teams):
            rank_count[team][rank] += 1
            if rank < 2:
                qualify_count[team] += 1

    print(f"\n{'='*52}")
    print(f"  {group_name}조 결과 ({n_sim:,}번 시뮬레이션)")
    print(f"{'='*52}")
    print(f"{'팀':<25} {'1위':>5} {'2위':>5} {'3위':>5} {'4위':>5} {'32강':>5}")
    print(f"{'-'*52}")

    sorted_by_rank = sorted(teams, key=lambda t: team_cache[t]['rank'])
    for team in sorted_by_rank:
        r1 = rank_count[team][0] / n_sim * 100
        r2 = rank_count[team][1] / n_sim * 100
        r3 = rank_count[team][2] / n_sim * 100
        r4 = rank_count[team][3] / n_sim * 100
        q  = qualify_count[team] / n_sim * 100
        print(f"{team:<25} {r1:>4.0f}% {r2:>4.0f}% {r3:>4.0f}% {r4:>4.0f}% {q:>4.0f}%")

    return qualify_count, n_sim

# ================================
# 18. 전체 시뮬레이션 실행
# ================================
print("\n\n" + "="*52)
print("  2026 FIFA 월드컵 조별리그 시뮬레이션")
print("="*52)

all_qualify = {}

for group_name, teams in groups_2026.items():
    qualify_count, n_sim = simulate_group_fast(group_name, teams)
    for team, count in qualify_count.items():
        all_qualify[team] = count / n_sim * 100

# ================================
# 19. 32강 진출 확률 순위
# ================================
print("\n\n" + "="*52)
print("  전체 32강 진출 확률 순위")
print("="*52)

sorted_qualify = sorted(
    all_qualify.items(),
    key=lambda x: x[1],
    reverse=True
)

for i, (team, prob) in enumerate(sorted_qualify, 1):
    bar = '█' * int(prob / 10)
    print(f"{i:>2}. {team:<25} {prob:>5.1f}% {bar}")

print("\n--- 한국 분석 ---")
korea_prob = all_qualify.get('South Korea', 0)
print(f"한국 32강 진출 확률: {korea_prob:.1f}%")
if korea_prob >= 70:
    print("→ 32강 진출 유력! 😊")
elif korea_prob >= 50:
    print("→ 32강 진출 가능성 있음 🤔")
else:
    print("→ 쉽지 않은 상황 😅")