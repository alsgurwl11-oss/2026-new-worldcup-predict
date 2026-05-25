import pandas as pd
df = pd.read_csv('data/wc_historical.csv')
wc22 = df[df['Year']==2022].dropna(subset=['home_score','away_score'])
draws = wc22[wc22['home_score']==wc22['away_score']]
print(f'2022 전체 경기: {len(wc22)}개')
print(f'2022 무승부 경기: {len(draws)}개')
print(draws[['home_team','away_team','home_score','away_score','Round']])

# check_draws.py에 추가
import sys
sys.path.append('.')
from model import initialize
from predict import ensemble_predict

m, tf, cw, tc, h2h, df2, r, wc = initialize()

NAME_MAP = {'Korea Republic': 'South Korea', 'IR Iran': 'Iran', 'USA': 'United States'}

correct_draws = 0
for _, row in draws.iterrows():
    home = NAME_MAP.get(row['home_team'], row['home_team'])
    away = NAME_MAP.get(row['away_team'], row['away_team'])
    try:
        pred = ensemble_predict(home, away, tc, h2h, cw, m, tf)
        predicted = max({'home_win': pred['home_win'], 'draw': pred['draw'], 'away_win': pred['away_win']}, key=lambda k: {'home_win': pred['home_win'], 'draw': pred['draw'], 'away_win': pred['away_win']}[k])
        if predicted == 'draw':
            correct_draws += 1
            print(f"OK {home} vs {away} → 무승부 예측 성공!")
        else:
            print(f"X  {home} vs {away} → {predicted} 예측 (실제: 무승부)")
    except:
        continue

print(f"\n무승부 적중: {correct_draws}/{len(draws)}개")

from upset_model import calculate_uvi

for _, row in draws.iterrows():
    home = NAME_MAP.get(row['home_team'], row['home_team'])
    away = NAME_MAP.get(row['away_team'], row['away_team'])
    try:
        pred = ensemble_predict(home, away, tc, h2h, cw, m, tf)
        
        # UVI 확인
        home_str = tc.get(home, {}).get('fpoints', 500)
        away_str = tc.get(away, {}).get('fpoints', 500)
        fav = home if home_str >= away_str else away
        und = away if home_str >= away_str else home
        uvi_result = calculate_uvi(fav, und, tc)
        uvi = uvi_result['uvi']
        
        predicted = max(pred, key=lambda k: pred[k] if k in ['home_win','draw','away_win'] else -1)
        print(f"UVI:{uvi:.2f} draw:{pred['draw']:.1f}% | {home} vs {away} → {predicted}")
    except Exception as e:
        print(f"에러: {e}")
        continue