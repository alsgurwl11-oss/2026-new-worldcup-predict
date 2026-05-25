# ================================
# optimize_weights.py - 가중치 최적화
# ================================
import pandas as pd
import numpy as np
from itertools import product
from model import initialize
from predict import ensemble_predict
import config

print("모델 로딩 중...")
(model, top_features, continent_winrate,
 team_cache, h2h_cache, df, ranking, wc_df) = initialize()

hist = pd.read_csv('data/wc_historical.csv')

BACKTEST_NAME_MAP = {
    'Korea Republic': 'South Korea',
    'IR Iran':        'Iran',
    'USA':            'United States',
}

def backtest(year):
    wc_year = hist[hist['Year'] == year].copy()
    wc_year = wc_year.dropna(subset=['home_score', 'away_score'])
    correct = total = 0

    for _, row in wc_year.iterrows():
        home = BACKTEST_NAME_MAP.get(row['home_team'], row['home_team'])
        away = BACKTEST_NAME_MAP.get(row['away_team'], row['away_team'])

        if row['home_score'] > row['away_score']:   actual = 'home'
        elif row['home_score'] < row['away_score']: actual = 'away'
        else:                                        actual = 'draw'

        try:
            pred = ensemble_predict(
                home, away,
                team_cache, h2h_cache,
                continent_winrate, model, top_features
            )
            probs = {
                'home': pred['home_win'],
                'draw': pred['draw'],
                'away': pred['away_win'],
            }
            if max(probs, key=probs.get) == actual:
                correct += 1
            total += 1
        except:
            continue

    return correct / total * 100 if total > 0 else 0

# ================================
# 현재 가중치 정확도
# ================================
print(f"\n현재 가중치: {config.ENSEMBLE_WEIGHTS}")
acc_22 = backtest(2022)
acc_18 = backtest(2018)
acc_14 = backtest(2014)
print(f"2022: {acc_22:.1f}%")
print(f"2018: {acc_18:.1f}%")
print(f"2014: {acc_14:.1f}%")
print(f"평균: {(acc_22+acc_18+acc_14)/3:.1f}%")

# ================================
# 그리드서치
# ================================
print("\n가중치 최적화 중...")

best_avg = 0
best_weights = None

ml_list  = [round(x * 0.01, 2) for x in range(5, 35)]   # 0.05 ~ 0.34
op_list  = [round(x * 0.01, 2) for x in range(5, 35)]   # 0.05 ~ 0.34
bet_list = [round(x * 0.01, 2) for x in range(20, 55)]  # 0.20 ~ 0.54

count = 0
for ml, opta, bet in product(ml_list, op_list, bet_list):
    elo = round(1.0 - ml - opta - bet, 2)
    if elo < 0.05 or elo > 0.35:
        continue

    config.ENSEMBLE_WEIGHTS = {
        'ml': ml, 'opta': opta,
        'betting': bet, 'elo': elo,
    }

    a22 = backtest(2022)
    a18 = backtest(2018)
    a14 = backtest(2014)
    avg = (a22 + a18 + a14) / 3
    count += 1

    if count % 10 == 0:
        print(f"  진행중... {count}개 조합")

    if avg > best_avg:
        best_avg = avg
        best_weights = {'ml': ml, 'opta': opta, 'betting': bet, 'elo': elo}
        print(f"  새 최고: 평균 {avg:.1f}% (22:{a22:.1f} 18:{a18:.1f} 14:{a14:.1f}) → {best_weights}")

# ================================
# 결과 출력
# ================================
print(f"\n{'='*50}")
print(f"최적 가중치: {best_weights}")
print(f"최고 평균 정확도: {best_avg:.1f}%")
print(f"\n# config.py 교체:")
print(f"ENSEMBLE_WEIGHTS = {{")
for k, v in best_weights.items():
    print(f"    '{k}': {v},")
print(f"}}")