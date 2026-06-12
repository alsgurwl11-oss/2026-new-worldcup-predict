# ================================
# error_analysis.py - 2022 오답노트
# 실행: conda activate worldcup
#       python error_analysis.py
# ================================

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from model import initialize
from predict import ensemble_predict

print("모델 로딩 중... (5~10분 소요) ☕")
model, top_features, continent_winrate, team_cache, h2h_cache, df, ranking, wc_df = initialize()

hist  = pd.read_csv('data/wc_historical.csv')
wc22  = pd.read_csv('data/wc_2022.csv')
hist22 = hist[hist['Year'] == 2022].dropna(subset=['home_score','away_score']).copy()

print(f"2022 경기 수: {len(hist22)}경기 예측 시작...\n")

results = []
for _, row in hist22.iterrows():
    home, away = row['home_team'], row['away_team']
    hs, as_   = float(row['home_score']), float(row['away_score'])
    total_goals = hs + as_

    if hs > as_:   actual = 'home_win'
    elif hs < as_: actual = 'away_win'
    else:           actual = 'draw'

    try:
        pred = ensemble_predict(home, away, team_cache, h2h_cache,
                                continent_winrate, model, top_features)
        probs = {
            'home_win': pred['home_win'],
            'draw':     pred['draw'],
            'away_win': pred['away_win'],
        }
        predicted  = max(probs, key=probs.get)
        confidence = probs[predicted]
        home_prob  = pred['home_win']
        draw_prob  = pred['draw']
        away_prob  = pred['away_win']
    except Exception as e:
        predicted, confidence = 'home_win', 33.3
        home_prob = draw_prob = away_prob = 33.3

    correct = (predicted == actual)

    # 언오버 실제값
    ou_actual = 'OVER' if total_goals > 2.5 else 'UNDER'

    results.append({
        'home':         home,
        'away':         away,
        'round':        row.get('Round', ''),
        'actual':       actual,
        'predicted':    predicted,
        'correct':      correct,
        'confidence':   round(confidence, 1),
        'home_prob':    round(home_prob, 1),
        'draw_prob':    round(draw_prob, 1),
        'away_prob':    round(away_prob, 1),
        'home_goals':   int(hs),
        'away_goals':   int(as_),
        'total_goals':  total_goals,
        'ou_actual':    ou_actual,
    })

df_r = pd.DataFrame(results)
total   = len(df_r)
correct = df_r['correct'].sum()

print("=" * 60)
print("📊 2022 백테스트 결과")
print("=" * 60)
print(f"전체:     {correct}/{total} = {correct/total*100:.1f}%")

grp = df_r[df_r['round'].str.contains('Group', na=False)]
knk = df_r[~df_r['round'].str.contains('Group', na=False)]
print(f"조별리그: {grp['correct'].sum()}/{len(grp)} = {grp['correct'].mean()*100:.1f}%")
print(f"토너먼트: {knk['correct'].sum()}/{len(knk)} = {knk['correct'].mean()*100:.1f}%")

# 신뢰도 구간별
print(f"\n【 신뢰도 구간별 정확도 】")
for lo, hi in [(60,100),(55,60),(50,55),(40,50),(33,40)]:
    sub = df_r[(df_r['confidence'] >= lo) & (df_r['confidence'] < hi)]
    if len(sub) == 0: continue
    acc = sub['correct'].mean()*100
    print(f"  {lo}%~{hi}%: {sub['correct'].sum()}/{len(sub)} = {acc:.1f}%")

# 오답 목록
wrong = df_r[~df_r['correct']].copy()
wrong = wrong.sort_values('confidence', ascending=False)

print(f"\n{'='*60}")
print(f"❌ 오답 목록 ({len(wrong)}경기) - 신뢰도 높은 순")
print(f"{'='*60}")
print(f"{'경기':30s} {'예측':10s} {'실제':10s} {'신뢰도':7s} {'스코어':8s} {'O/U실제'}")
print("-" * 75)
for _, r in wrong.iterrows():
    pred_str   = r['predicted'].replace('home_win', f"{r['home']}승").replace('away_win', f"{r['away']}승").replace('draw','무승부')
    actual_str = r['actual'].replace('home_win', f"{r['home']}승").replace('away_win', f"{r['away']}승").replace('draw','무승부')
    score = f"{r['home_goals']}-{r['away_goals']}"
    print(f"{r['home']} vs {r['away']:15s} {pred_str:12s} {actual_str:12s} {r['confidence']:5.1f}%  {score:6s}  {r['ou_actual']}")

# 오버/언더 정확도
print(f"\n{'='*60}")
print(f"⚽ 언오버 2.5 기준 실제 분포")
print(f"{'='*60}")
over_cnt  = (df_r['ou_actual'] == 'OVER').sum()
under_cnt = (df_r['ou_actual'] == 'UNDER').sum()
print(f"전체: 오버 {over_cnt}({over_cnt/total*100:.1f}%) | 언더 {under_cnt}({under_cnt/total*100:.1f}%)")
print(f"조별리그: 오버 {(grp['ou_actual']=='OVER').sum()}/{len(grp)} ({(grp['ou_actual']=='OVER').mean()*100:.1f}%)")
print(f"토너먼트: 오버 {(knk['ou_actual']=='OVER').sum()}/{len(knk)} ({(knk['ou_actual']=='OVER').mean()*100:.1f}%)")

# 고신뢰도 오답 상세
print(f"\n{'='*60}")
print(f"🔍 고신뢰도(55%+) 오답 상세 분석")
print(f"{'='*60}")
high_wrong = wrong[wrong['confidence'] >= 55]
print(f"총 {len(high_wrong)}경기\n")
for _, r in high_wrong.iterrows():
    print(f"  {r['home']} vs {r['away']} [{r['round']}]")
    print(f"    모델: {r['predicted']} ({r['confidence']}%) | 실제: {r['actual']} ({r['home_goals']}-{r['away_goals']})")
    print(f"    확률: 홈{r['home_prob']}% 무{r['draw_prob']}% 원정{r['away_prob']}%")
    print()

print("분석 완료! 결과를 Claude에게 붙여넣어줘 👆")