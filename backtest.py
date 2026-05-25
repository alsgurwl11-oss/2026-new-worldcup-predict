# ================================
# backtest.py - 백테스트 함수 모듈
# ================================
import pandas as pd
import numpy as np
from predict import ensemble_predict

BACKTEST_NAME_MAP = {
    'Korea Republic': 'South Korea',
    'IR Iran':        'Iran',
    'USA':            'United States',
}

BACKTEST_TOURNAMENTS = {
    '2022': {
        'name':       '2022 카타르 월드컵',
        'champion':   'Argentina',
        'top4':       ['Argentina', 'France', 'Croatia', 'Morocco'],
    },
    '2018': {
        'name':       '2018 러시아 월드컵',
        'champion':   'France',
        'top4':       ['France', 'Croatia', 'Belgium', 'England'],
    },
}

# --------------------------------
# 2022 월드컵 사전 배당률 (미국식 머니라인)
# 출처: William Hill / Ladbrokes / BetMGM (2022년 11월 기준)
# --------------------------------
BACKTEST_ODDS_2022 = {
    'Brazil':        400,
    'Argentina':     500,
    'France':        650,
    'England':       700,
    'Spain':         800,
    'Germany':       1000,
    'Netherlands':   1200,
    'Portugal':      1500,
    'Belgium':       1600,
    'Denmark':       3000,
    'Uruguay':       4000,
    'Croatia':       4000,
    'Poland':        4000,
    'Senegal':       5000,
    'Switzerland':   5000,
    'Mexico':        5000,
    'United States': 10000,
    'Wales':         10000,
    'Japan':         15000,
    'South Korea':   15000,
    'Australia':     15000,
    'Morocco':       15000,
    'Ecuador':       15000,
    'Canada':        20000,
    'Serbia':        20000,
    'Iran':          30000,
    'Ghana':         30000,
    'Tunisia':       30000,
    'Cameroon':      50000,
    'Saudi Arabia':  50000,
    'Costa Rica':    50000,
    'Qatar':         100000,
}

# --------------------------------
# 2018 월드컵 사전 배당률
# 출처: 주요 북메이커 (2018년 6월 기준)
# --------------------------------
BACKTEST_ODDS_2018 = {
    'Brazil':        400,
    'Germany':       500,
    'Spain':         600,
    'France':        700,
    'Argentina':     700,
    'England':       1000,
    'Belgium':       1000,
    'Portugal':      1200,
    'Uruguay':       2000,
    'Colombia':      2500,
    'Croatia':       3000,
    'Poland':        3000,
    'Switzerland':   5000,
    'Mexico':        5000,
    'Denmark':       5000,
    'Russia':        8000,
    'Sweden':        8000,
    'Senegal':       10000,
    'Japan':         10000,
    'United States': 15000,
    'South Korea':   15000,
    'Australia':     15000,
    'Morocco':       20000,
    'Egypt':         20000,
    'Iceland':       20000,
    'Peru':          20000,
    'Iran':          30000,
    'Costa Rica':    30000,
    'Serbia':        30000,
    'Nigeria':       30000,
    'Tunisia':       50000,
    'Panama':        50000,
    'Saudi Arabia':  50000,
}


def run_backtest(year, hist, team_cache, h2h_cache,
                 continent_winrate, model, top_features):

    # 연도별 배당률 임시 적용
    import config
    original_odds = config.BETTING_ODDS.copy()

    if str(year) == '2022':
        config.BETTING_ODDS = {**original_odds, **BACKTEST_ODDS_2022}
    elif str(year) == '2018':
        config.BETTING_ODDS = {**original_odds, **BACKTEST_ODDS_2018}

    wc_year = hist[hist['Year'] == int(year)].copy()
    wc_year = wc_year.dropna(subset=['home_score', 'away_score'])

    correct = total = 0
    match_details = []

    for _, row in wc_year.iterrows():
        home = BACKTEST_NAME_MAP.get(row['home_team'], row['home_team'])
        away = BACKTEST_NAME_MAP.get(row['away_team'], row['away_team'])
        round_name = row.get('Round', 'Group stage')

        if row['home_score'] > row['away_score']:   actual = 'home_win'
        elif row['home_score'] < row['away_score']: actual = 'away_win'
        else:                                        actual = 'draw'

        try:
            pred = ensemble_predict(
                home, away,
                team_cache, h2h_cache,
                continent_winrate, model, top_features
            )
            probs = {
                'home_win': pred['home_win'],
                'draw':     pred['draw'],
                'away_win': pred['away_win'],
            }
            predicted  = max(probs, key=probs.get)
            confidence = round(probs[predicted], 1)
            is_correct = predicted == actual
            total += 1
            if is_correct: correct += 1

            match_details.append({
                'home':       home,
                'away':       away,
                'round':      round_name,
                'actual':     actual,
                'predicted':  predicted,
                'confidence': confidence,
                'correct':    is_correct,
            })
        except:
            continue

    # 원래 배당률로 복원
    config.BETTING_ODDS = original_odds

    info = BACKTEST_TOURNAMENTS.get(str(year), {})
    high_conf      = [m for m in match_details if m['confidence'] >= 50]
    group_matches  = [m for m in match_details if 'Group' in str(m['round'])]
    knockout_matches = [m for m in match_details if 'Group' not in str(m['round'])]

    return {
        'tournament':         info.get('name', f'{year} 월드컵'),
        'total_accuracy':     round(correct/total*100, 1) if total > 0 else 0,
        'total_matches':      total,
        'group_accuracy':     round(sum(m['correct'] for m in group_matches)/len(group_matches)*100, 1) if group_matches else 0,
        'knockout_accuracy':  round(sum(m['correct'] for m in knockout_matches)/len(knockout_matches)*100, 1) if knockout_matches else 0,
        'high_conf_accuracy': round(sum(m['correct'] for m in high_conf)/len(high_conf)*100, 1) if high_conf else 0,
        'high_conf_count':    len(high_conf),
        'champion_actual':    info.get('champion', ''),
        'top4_actual':        info.get('top4', []),
        'match_details':      match_details,
    }


def run_all_backtests(hist, team_cache, h2h_cache,
                      continent_winrate, model, top_features):
    results = {}
    for year in ['2022', '2018']:
        results[year] = run_backtest(
            year, hist, team_cache, h2h_cache,
            continent_winrate, model, top_features
        )
    return results