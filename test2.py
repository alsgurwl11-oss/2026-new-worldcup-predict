echo import pandas as pd > check_fc26.py
echo df = pd.read_csv('data/FC26_20250921.csv', low_memory=False) >> check_fc26.py
echo print('shape:', df.shape) >> check_fc26.py
echo print(df.columns.tolist()) >> check_fc26.py
echo son = df[df['short_name'].str.contains('Son', na=False)] >> check_fc26.py
echo print(son[['short_name', 'nationality_name', 'club_name', 'overall', 'player_positions']].head()) >> check_fc26.py
python check_fc26.py