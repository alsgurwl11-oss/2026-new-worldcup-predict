from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
import pickle
import os

app = Flask(__name__)

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

wc = df[df['tournament'] == 'FIFA World Cup'].copy()
wc = wc.reset_index(drop=True)

# ================================
# 2. FIFA 랭킹 데이터
# ================================
r1 = pd.read_csv('fifa_ranking-2023-07-20.csv')
r2 = pd.read_csv('fifa_ranking-2024-04-04.csv')
r3 = pd.read_csv('fifa_ranking-2024-06-20.csv')
ranking = pd.concat([r1, r2, r3], ignore_index=True)
ranking['rank_date'] = pd.to_datetime(ranking['rank_date'])
ranking = ranking.sort_values('rank_date').reset_index(drop=True)

# ================================
# 3. 설정값
# ================================
name_map = {
    'South Korea':            'Korea Republic',
    'United States':          'USA',
    'Ivory Coast':            "Côte d'Ivoire",
    'Bosnia and Herzegovina': 'Bosnia-Herzegovina',
    'Cape Verde':             'Cape Verde',
    'Trinidad and Tobago':    'Trinidad and Tobago',
}

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

prev_champions = {
    1934: 'Uruguay',   1938: 'Italy',     1950: 'Italy',
    1954: 'Uruguay',   1958: 'Germany',   1962: 'Brazil',
    1966: 'Brazil',    1970: 'England',   1974: 'Brazil',
    1978: 'Germany',   1982: 'Argentina', 1986: 'Italy',
    1990: 'Argentina', 1994: 'Germany',   1998: 'Brazil',
    2002: 'France',    2006: 'Brazil',    2010: 'Italy',
    2014: 'Spain',     2018: 'Germany',   2022: 'France',
}

south_america_hosts = [1930, 1950, 1962, 1978, 2014]
europe_hosts = [1934, 1938, 1954, 1958, 1966, 1974, 1982, 1990, 1998, 2006]

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

le = LabelEncoder()
le.fit(['UEFA', 'CONMEBOL', 'CONCACAF', 'AFC', 'CAF', 'OTHER'])

# ================================
# 4. 함수들
# ================================
def get_continent(team):
    return continent_map.get(team, 'OTHER')

def get_host_continent_penalty(team_cont, date):
    year = date.year
    if team_cont == 'UEFA' and year in south_america_hosts:
        return -0.1
    if team_cont == 'CONMEBOL' and year in europe_hosts:
        return -0.1
    return 0.0

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
# 5. 모델 학습 or 로딩
# ================================
if os.path.exists('model.pkl'):
    print("저장된 모델 불러오는 중... (빠름!)")
    with open('model.pkl', 'rb') as f:
        saved = pickle.load(f)
    xgb          = saved['model']
    top_features = saved['top_features']
    continent_winrate = saved['continent_winrate']
    team_cache   = saved['team_cache']
    h2h_cache    = saved['h2h_cache']
    print("모델 로딩 완료!")

else:
    print("모델 학습 중... (첫 실행은 시간이 걸려요 ☕)")

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
                (df['home_cont'] == hc) & (df['away_cont'] == ac)
            ]
            continent_winrate[(hc, ac)] = (
                (filtered['result'] == 1).mean()
                if len(filtered) >= 5 else 0.33
            )

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
        cont_adv  = continent_winrate.get((h_cont, a_cont), 0.33)
        h_exp     = get_worldcup_experience(home, date)
        a_exp     = get_worldcup_experience(away, date)
        h_host    = 1 if host_map.get(home, 0) == date.year else 0
        h_def     = 1 if prev_champions.get(date.year, '') == home else 0
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
            print(f"  피처 생성 중... {idx}/{len(wc)}")

    feat_df      = pd.DataFrame(features)
    top_features = list(feat_df.columns)
    X            = feat_df[top_features]
    y            = wc['result']
    label_map    = {-1: 0, 0: 1, 1: 2}
    y_encoded    = y.map(label_map)

    xgb = XGBClassifier(
        n_estimators=200, max_depth=3, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        random_state=42, eval_metric='mlogloss', verbosity=0
    )
    xgb.fit(X, y_encoded)
    print("모델 학습 완료!")

    # 팀 캐싱
    print("팀 데이터 캐싱 중...")
    date = pd.Timestamp('2024-06-20')
    all_teams = list(set(
        team for teams in groups_2026.values() for team in teams
    ))

    team_cache = {}
    for team in all_teams:
        h_wr, h_dr, h_gf, h_ga, h_pts = get_team_stats(team, date)
        team_cache[team] = {
            'wr': h_wr, 'dr': h_dr, 'gf': h_gf,
            'ga': h_ga, 'pts': h_pts,
            'form':    get_recent_form(team, date),
            'rank':    get_fifa_rank(team, date),
            'fpoints': get_fifa_points(team, date),
            'exp':     get_worldcup_experience(team, date),
            'cont':    get_continent(team),
            'penalty': get_host_continent_penalty(get_continent(team), date),
        }

    h2h_cache = {}
    for group_name, teams in groups_2026.items():
        for i in range(len(teams)):
            for j in range(i+1, len(teams)):
                home, away = teams[i], teams[j]
                h2h_cache[(home, away)] = get_h2h(home, away, date)

    # 모델 저장
    with open('model.pkl', 'wb') as f:
        pickle.dump({
            'model':            xgb,
            'top_features':     top_features,
            'continent_winrate':continent_winrate,
            'team_cache':       team_cache,
            'h2h_cache':        h2h_cache,
        }, f)
    print("모델 저장 완료! 다음부터는 빠르게 시작돼요 😊")

# ================================
# 6. 예측 함수
# ================================
def get_match_probs_fast(home, away, neutral=True):
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

    h_cont   = hc['cont']
    a_cont   = ac['cont']
    cont_adv = continent_winrate.get((h_cont, a_cont), 0.33)

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

    return xgb.predict_proba(feat[top_features])[0].tolist()

# ================================
# 7. 조별리그 시뮬레이션
# ================================
def simulate_group_fast(teams, n_sim=5000):
    matches = []
    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            matches.append((teams[i], teams[j]))

    match_probs = {
        (h, a): get_match_probs_fast(h, a)
        for h, a in matches
    }

    rank_count    = {t: [0,0,0,0] for t in teams}
    qualify_count = {t: 0 for t in teams}
    points_total  = {t: 0 for t in teams}

    for _ in range(n_sim):
        points = {t: 0 for t in teams}
        gd     = {t: 0 for t in teams}
        gf     = {t: 0 for t in teams}

        for home, away in matches:
            probs    = match_probs[(home, away)]
            home_win = probs[2]
            draw     = probs[1]
            rand     = np.random.random()

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
            points_total[team] += points[team]
            if rank < 2:
                qualify_count[team] += 1

    result = []
    for team in teams:
        result.append({
            'team':       team,
            'rank':       team_cache[team]['rank'],
            'first':      round(rank_count[team][0] / n_sim * 100, 1),
            'second':     round(rank_count[team][1] / n_sim * 100, 1),
            'third':      round(rank_count[team][2] / n_sim * 100, 1),
            'fourth':     round(rank_count[team][3] / n_sim * 100, 1),
            'qualify':    round(qualify_count[team] / n_sim * 100, 1),
            'avg_points': round(points_total[team] / n_sim, 1),
        })

    result.sort(key=lambda x: x['qualify'], reverse=True)
    return result

# ================================
# 8. 토너먼트 시뮬레이션
# ================================
def simulate_tournament(n_sim=3000):
    """전체 대회 시뮬레이션 - 조별리그부터 결승까지"""

    champion_count = {}
    final_count    = {}
    semi_count     = {}
    quarter_count  = {}

    for _ in range(n_sim):
        # 조별리그 시뮬레이션
        group_results = {}
        third_place   = []

        for group_name, teams in groups_2026.items():
            matches = [
                (teams[i], teams[j])
                for i in range(len(teams))
                for j in range(i+1, len(teams))
            ]
            match_probs = {
                (h, a): get_match_probs_fast(h, a)
                for h, a in matches
            }

            points = {t: 0 for t in teams}
            gd     = {t: 0 for t in teams}
            gf_d   = {t: 0 for t in teams}

            for home, away in matches:
                probs    = match_probs[(home, away)]
                home_win = probs[2]
                draw     = probs[1]
                rand     = np.random.random()

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

                gd[home]  += hg - ag
                gd[away]  += ag - hg
                gf_d[home]+= hg
                gf_d[away]+= ag

            sorted_teams = sorted(
                teams,
                key=lambda t: (points[t], gd[t], gf_d[t]),
                reverse=True
            )

            group_results[group_name] = sorted_teams
            third_place.append({
                'team':   sorted_teams[2],
                'points': points[sorted_teams[2]],
                'gd':     gd[sorted_teams[2]],
                'gf':     gf_d[sorted_teams[2]],
            })

        # 3위팀 8개 선발
        third_place.sort(
            key=lambda x: (x['points'], x['gd'], x['gf']),
            reverse=True
        )
        qualified_thirds = [t['team'] for t in third_place[:8]]

        # 32강 대진 (단순화)
        r32_matches = []
        for group_name, sorted_teams in group_results.items():
            first  = sorted_teams[0]
            second = sorted_teams[1]
            # 1위는 다른 조 2위와 매칭
            r32_matches.append((first, second))

        # 토너먼트 진행 함수
        def play_match(team1, team2):
            probs = get_match_probs_fast(team1, team2)
            rand  = np.random.random()
            if rand < probs[2]:
                return team1
            elif rand < probs[2] + probs[1]:
                # 무승부 → 승부차기 (50/50)
                return team1 if np.random.random() < 0.5 else team2
            else:
                return team2

        # 32강
        r16_teams = []
        for t1, t2 in r32_matches:
            r16_teams.append(play_match(t1, t2))

        # 16강
        qf_teams = []
        for i in range(0, len(r16_teams), 2):
            if i+1 < len(r16_teams):
                qf_teams.append(play_match(r16_teams[i], r16_teams[i+1]))

        # 8강
        sf_teams = []
        for i in range(0, len(qf_teams), 2):
            if i+1 < len(qf_teams):
                winner = play_match(qf_teams[i], qf_teams[i+1])
                sf_teams.append(winner)
                quarter_count[qf_teams[i]]   = quarter_count.get(qf_teams[i], 0) + 1
                quarter_count[qf_teams[i+1]] = quarter_count.get(qf_teams[i+1], 0) + 1

        # 4강
        f_teams = []
        for i in range(0, len(sf_teams), 2):
            if i+1 < len(sf_teams):
                winner = play_match(sf_teams[i], sf_teams[i+1])
                f_teams.append(winner)
                semi_count[sf_teams[i]]   = semi_count.get(sf_teams[i], 0) + 1
                semi_count[sf_teams[i+1]] = semi_count.get(sf_teams[i+1], 0) + 1

        # 결승
        if len(f_teams) >= 2:
            champion = play_match(f_teams[0], f_teams[1])
            champion_count[champion] = champion_count.get(champion, 0) + 1
            final_count[f_teams[0]]  = final_count.get(f_teams[0], 0) + 1
            final_count[f_teams[1]]  = final_count.get(f_teams[1], 0) + 1

    # 결과 정리
    all_teams = list(set(
        team for teams in groups_2026.values() for team in teams
    ))

    result = []
    for team in all_teams:
        result.append({
            'team':      team,
            'rank':      team_cache.get(team, {}).get('rank', 99),
            'champion':  round(champion_count.get(team, 0) / n_sim * 100, 1),
            'final':     round(final_count.get(team, 0) / n_sim * 100, 1),
            'semi':      round(semi_count.get(team, 0) / n_sim * 100, 1),
            'quarter':   round(quarter_count.get(team, 0) / n_sim * 100, 1),
        })

    result.sort(key=lambda x: x['champion'], reverse=True)
    return result

# ================================
# 9. Flask 라우트
# ================================
@app.route('/')
def index():
    return render_template('index.html', groups=groups_2026)

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    home = data.get('home')
    away = data.get('away')

    if not home or not away:
        return jsonify({'error': '팀을 선택해주세요'}), 400

    probs  = get_match_probs_fast(home, away)
    h_rank = team_cache.get(home, {}).get('rank', 'N/A')
    a_rank = team_cache.get(away, {}).get('rank', 'N/A')

    if (home, away) in h2h_cache:
        h2h = h2h_cache[(home, away)]
    elif (away, home) in h2h_cache:
        h2h_r = h2h_cache[(away, home)]
        h2h   = (h2h_r[2], h2h_r[1], h2h_r[0])
    else:
        h2h = (0.33, 0.33, 0.33)

    return jsonify({
        'home':      home,
        'away':      away,
        'home_win':  round(probs[2] * 100, 1),
        'draw':      round(probs[1] * 100, 1),
        'away_win':  round(probs[0] * 100, 1),
        'home_rank': h_rank,
        'away_rank': a_rank,
        'h2h_home':  round(h2h[0] * 100, 1),
        'h2h_draw':  round(h2h[1] * 100, 1),
        'h2h_away':  round(h2h[2] * 100, 1),
    })

@app.route('/api/simulate_group', methods=['POST'])
def simulate_group_api():
    data       = request.json
    group_name = data.get('group')

    if group_name not in groups_2026:
        return jsonify({'error': '조를 선택해주세요'}), 400

    teams  = groups_2026[group_name]
    result = simulate_group_fast(teams)
    return jsonify({'group': group_name, 'result': result})

@app.route('/api/simulate_all', methods=['GET'])
def simulate_all():
    all_results = {}
    for group_name, teams in groups_2026.items():
        all_results[group_name] = simulate_group_fast(teams, n_sim=3000)
    return jsonify(all_results)

@app.route('/api/tournament', methods=['GET'])
def tournament():
    result = simulate_tournament(n_sim=2000)
    return jsonify(result)

if __name__ == '__main__':
    print("Flask 서버 시작!")
    print("http://127.0.0.1:5000 접속하세요")
    app.run(debug=True)