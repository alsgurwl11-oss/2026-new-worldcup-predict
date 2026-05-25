import pandas as pd
df = pd.read_csv('data/FC26_20250921.csv', low_memory=False)

# Korea Republic 있는지 확인
kor_check = df[df['nationality_name'].str.contains('Korea', na=False)]
print("Korea 관련 국가명:", kor_check['nationality_name'].unique())

# 브라질 TOP11 (overall 기준)
bra = df[df['nationality_name'] == 'Brazil'].copy()
bra = bra[~bra['player_positions'].str.contains('GK', na=False)]  # GK 제외
top11 = bra.nlargest(11, 'overall')
print("\n브라질 TOP11:")
print(top11[['short_name', 'overall', 'player_positions', 'pace', 'shooting', 'passing', 'dribbling', 'defending', 'physic']].to_string())