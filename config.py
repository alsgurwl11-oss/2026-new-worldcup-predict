# ================================
# config.py - 모든 설정값 관리
# ================================

# --------------------------------
# 2026 월드컵 조별 대진표
# --------------------------------
GROUPS_2026 = {
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

# 전체 참가팀 리스트
ALL_TEAMS = list(set(
    team for teams in GROUPS_2026.values() for team in teams
))

# --------------------------------
# 팀 이름 매핑 (결과 CSV → FIFA 랭킹 CSV)
# --------------------------------
NAME_MAP = {
    'South Korea':            'Korea Republic',
    'United States':          'USA',
    'Ivory Coast':            "Côte d'Ivoire",
    'Bosnia and Herzegovina': 'Bosnia-Herzegovina',
    'Cape Verde':             'Cape Verde',
    'Trinidad and Tobago':    'Trinidad and Tobago',
}

# --------------------------------
# 대륙 정보
# --------------------------------
CONTINENT_MAP = {
    # CONMEBOL
    'Brazil': 'CONMEBOL', 'Argentina': 'CONMEBOL', 'Uruguay': 'CONMEBOL',
    'Colombia': 'CONMEBOL', 'Chile': 'CONMEBOL', 'Paraguay': 'CONMEBOL',
    'Peru': 'CONMEBOL', 'Ecuador': 'CONMEBOL', 'Bolivia': 'CONMEBOL',
    'Venezuela': 'CONMEBOL',
    # UEFA
    'Germany': 'UEFA', 'France': 'UEFA', 'Spain': 'UEFA', 'Italy': 'UEFA',
    'England': 'UEFA', 'Netherlands': 'UEFA', 'Portugal': 'UEFA',
    'Belgium': 'UEFA', 'Croatia': 'UEFA', 'Poland': 'UEFA',
    'Switzerland': 'UEFA', 'Denmark': 'UEFA', 'Sweden': 'UEFA',
    'Norway': 'UEFA', 'Austria': 'UEFA', 'Czech Republic': 'UEFA',
    'Serbia': 'UEFA', 'Hungary': 'UEFA', 'Romania': 'UEFA',
    'Russia': 'UEFA', 'Ukraine': 'UEFA', 'Wales': 'UEFA',
    'Scotland': 'UEFA', 'Turkey': 'UEFA', 'Greece': 'UEFA',
    'Bosnia and Herzegovina': 'UEFA',
    # AFC
    'South Korea': 'AFC', 'Japan': 'AFC', 'Australia': 'AFC',
    'Iran': 'AFC', 'Saudi Arabia': 'AFC', 'China': 'AFC',
    'Qatar': 'AFC', 'Iraq': 'AFC', 'Uzbekistan': 'AFC',
    # CONCACAF
    'Mexico': 'CONCACAF', 'United States': 'CONCACAF', 'Canada': 'CONCACAF',
    'Costa Rica': 'CONCACAF', 'Honduras': 'CONCACAF', 'Jamaica': 'CONCACAF',
    'Panama': 'CONCACAF', 'Trinidad and Tobago': 'CONCACAF',
    'Curacao': 'CONCACAF', 'Haiti': 'CONCACAF',
    # CAF
    'Cameroon': 'CAF', 'Nigeria': 'CAF', 'Ghana': 'CAF',
    'Senegal': 'CAF', 'Morocco': 'CAF', 'Egypt': 'CAF',
    'Ivory Coast': 'CAF', 'Algeria': 'CAF', 'Tunisia': 'CAF',
    'South Africa': 'CAF', 'Angola': 'CAF', 'Togo': 'CAF',
    'Cape Verde': 'CAF',
    # OFC
    'New Zealand': 'OFC',
}

# --------------------------------
# 역대 개최국
# --------------------------------
HOST_MAP = {
    'Uruguay': 1930, 'Italy': 1934, 'France': 1938,
    'Brazil': 1950, 'Switzerland': 1954, 'Sweden': 1958,
    'Chile': 1962, 'England': 1966, 'Mexico': 1970,
    'Germany': 1974, 'Argentina': 1978, 'Spain': 1982,
    'Mexico': 1986, 'Italy': 1990, 'United States': 1994,
    'France': 1998, 'South Korea': 2002, 'Japan': 2002,
    'Germany': 2006, 'South Africa': 2010, 'Brazil': 2014,
    'Russia': 2018, 'Qatar': 2022,
    # 2026 개최국
    'Mexico': 2026, 'United States': 2026, 'Canada': 2026,
}

# --------------------------------
# 역대 우승국 (징크스용)
# --------------------------------
PREV_CHAMPIONS = {
    1934: 'Uruguay',   1938: 'Italy',     1950: 'Italy',
    1954: 'Uruguay',   1958: 'Germany',   1962: 'Brazil',
    1966: 'Brazil',    1970: 'England',   1974: 'Brazil',
    1978: 'Germany',   1982: 'Argentina', 1986: 'Italy',
    1990: 'Argentina', 1994: 'Germany',   1998: 'Brazil',
    2002: 'France',    2006: 'Brazil',    2010: 'Italy',
    2014: 'Spain',     2018: 'Germany',   2022: 'France',
}

# --------------------------------
# 대륙 개최 패널티
# --------------------------------
SOUTH_AMERICA_HOSTS = [1930, 1950, 1962, 1978, 2014]
EUROPE_HOSTS        = [1934, 1938, 1954, 1958, 1966, 1974, 1982, 1990, 1998, 2006]

# --------------------------------
# Opta 2026 월드컵 우승 확률
# 출처: theanalyst.com (2025년 기준)
# --------------------------------
OPTA_WIN_PROB = {
    'Spain':                  0.170,
    'France':                 0.141,
    'England':                0.118,
    'Argentina':              0.087,
    'Brazil':                 0.082,
    'Portugal':               0.065,
    'Germany':                0.058,
    'Netherlands':            0.045,
    'Belgium':                0.032,
    'Uruguay':                0.018,
    'Colombia':               0.015,
    'Mexico':                 0.013,
    'United States':          0.009,
    'Japan':                  0.009,
    'Morocco':                0.008,
    'Senegal':                0.007,
    'Ecuador':                0.006,
    'Croatia':                0.006,
    'Austria':                0.005,
    'South Korea':            0.003,
    'Switzerland':            0.003,
    'Canada':                 0.003,
    'Norway':                 0.003,
    'Australia':              0.002,
    'Iran':                   0.002,
    'Turkey':                 0.002,
    'Scotland':               0.002,
    'Algeria':                0.002,
    'Sweden':                 0.001,
    'Qatar':                  0.001,
    'Saudi Arabia':           0.001,
    'Ghana':                  0.001,
    'South Africa':           0.001,
    'Czech Republic':         0.001,
    'Paraguay':               0.001,
    'Ivory Coast':            0.001,
    'Egypt':                  0.001,
    'New Zealand':            0.0001,
    'Tunisia':                0.0001,
    'Haiti':                  0.0001,
    'Panama':                 0.0001,
    'Jordan':                 0.0001,
    'Uzbekistan':             0.0001,
    'Curacao':                0.0001,
    'Cape Verde':             0.0001,
    'Bosnia and Herzegovina': 0.0001,
    'Iraq':                   0.0001,
}

# --------------------------------
# 배당률 (미국식 머니라인, ESPN 기준 2026년 4월)
# +450 = 100달러 베팅시 450달러 수익
# --------------------------------
BETTING_ODDS = {
    'Spain':                  450,
    'France':                 600,
    'England':                600,
    'Argentina':              850,
    'Brazil':                 850,
    'Portugal':               1100,
    'Germany':                1400,
    'Netherlands':            2000,
    'Belgium':                3500,
    'Colombia':               4000,
    'Norway':                 2800,
    'Japan':                  5000,
    'United States':          6500,
    'Mexico':                 7000,
    'Uruguay':                8000,
    'Canada':                 20000,
    'South Korea':            30000,
    'Morocco':                15000,
    'Ecuador':                25000,
    'Senegal':                20000,
    'Croatia':                25000,
    'Austria':                30000,
    'Switzerland':            25000,
    'Australia':              40000,
    'Turkey':                 40000,
    'Iran':                   50000,
    'Scotland':               50000,
    'Algeria':                60000,
    'Qatar':                  80000,
    'Saudi Arabia':           80000,
    'Ghana':                  100000,
    'South Africa':           150000,
    'Czech Republic':         100000,
    'Paraguay':               100000,
    'Ivory Coast':            100000,
    'Egypt':                  100000,
    'Sweden':                 80000,
    'Iraq':                   200000,
    'New Zealand':            500000,
    'Tunisia':                300000,
    'Haiti':                  500000,
    'Panama':                 300000,
    'Jordan':                 500000,
    'Uzbekistan':             500000,
    'Curacao':                1000000,
    'Cape Verde':             500000,
    'Bosnia and Herzegovina': 200000,
}

# --------------------------------
# 앙상블 가중치
# 백테스트 후 최적화 예정
# --------------------------------
ENSEMBLE_WEIGHTS = {
    'ml':      0.35,  # XGBoost 모델
    'opta':    0.30,  # Opta 예측값
    'betting': 0.25,  # 배당률 역산
    'elo':     0.10,  # ELO 레이팅
}

# --------------------------------
# 시뮬레이션 기본 횟수
# --------------------------------
SIM_CONFIG = {
    'group':      3000,  # 조별리그
    'all_groups': 2000,  # 전체 조별리그
    'tournament': 300,   # 토너먼트
    'bracket':    300,   # 브라켓
    'korea':      300,   # 한국 시나리오
}

# --------------------------------
# XGBoost 하이퍼파라미터
# --------------------------------
XGB_PARAMS = {
    'n_estimators':    200,
    'max_depth':       3,
    'learning_rate':   0.05,
    'subsample':       0.8,
    'colsample_bytree':0.8,
    'min_child_weight':3,
    'random_state':    42,
    'eval_metric':     'mlogloss',
    'verbosity':       0,
}

# --------------------------------
# 데이터 파일 경로
# --------------------------------
DATA_FILES = {
    'results':    'results.csv',
    'ranking_1':  'fifa_ranking-2023-07-20.csv',
    'ranking_2':  'fifa_ranking-2024-04-04.csv',
    'ranking_3':  'fifa_ranking-2024-06-20.csv',
    'model':      'model.pkl',
}

# --------------------------------
# 예측 기준 날짜
# --------------------------------
PREDICT_DATE = '2024-06-20'

# --------------------------------
# FC25 선수 능력치 기반 팀 전력
# 출처: FC25 players_info.csv
# TOP23: 상위 23명 평균 / TOP11: 상위 11명 평균
# --------------------------------
TEAM_STRENGTH_FC25 = {
    'France':                 {'top23': 84.65, 'top11': 86.45},
    'England':                {'top23': 84.52, 'top11': 86.55},
    'Brazil':                 {'top23': 84.39, 'top11': 86.64},
    'Germany':                {'top23': 84.30, 'top11': 86.55},
    'Spain':                  {'top23': 84.13, 'top11': 85.55},
    'Argentina':              {'top23': 83.52, 'top11': 85.45},
    'Portugal':               {'top23': 83.52, 'top11': 85.82},
    'Netherlands':            {'top23': 82.17, 'top11': 84.09},
    'Belgium':                {'top23': 80.65, 'top11': 83.18},
    'Uruguay':                {'top23': 79.04, 'top11': 82.00},
    'Switzerland':            {'top23': 78.65, 'top11': 81.82},
    'Croatia':                {'top23': 78.35, 'top11': 80.91},
    'Austria':                {'top23': 78.13, 'top11': 80.55},
    'Morocco':                {'top23': 78.00, 'top11': 80.55},
    'Colombia':               {'top23': 77.48, 'top11': 79.18},
    'Turkey':                 {'top23': 77.43, 'top11': 79.45},
    'Ivory Coast':            {'top23': 77.22, 'top11': 79.00},
    'Egypt':                  {'top23': 76.83, 'top11': 76.83},
    'Japan':                  {'top23': 76.65, 'top11': 79.18},
    'Norway':                 {'top23': 76.52, 'top11': 79.64},
    'Senegal':                {'top23': 76.35, 'top11': 78.64},
    'Sweden':                 {'top23': 76.09, 'top11': 78.73},
    'Algeria':                {'top23': 75.96, 'top11': 78.55},
    'Scotland':               {'top23': 75.87, 'top11': 78.36},
    'Czech Republic':         {'top23': 75.83, 'top11': 77.27},
    'United States':          {'top23': 75.83, 'top11': 77.64},
    'Ghana':                  {'top23': 75.70, 'top11': 77.91},
    'South Korea':            {'top23': 74.61, 'top11': 77.27},
    'Ecuador':                {'top23': 74.26, 'top11': 76.64},
    'Paraguay':               {'top23': 74.00, 'top11': 75.45},
    'Bosnia and Herzegovina': {'top23': 73.22, 'top11': 76.00},
    'Canada':                 {'top23': 72.13, 'top11': 74.91},
    'Mexico':                 {'top23': 71.13, 'top11': 76.27},
    'Australia':              {'top23': 71.09, 'top11': 73.00},
    'Saudi Arabia':           {'top23': 71.04, 'top11': 73.91},
    'Iran':                   {'top23': 70.62, 'top11': 70.62},
    'Tunisia':                {'top23': 69.61, 'top11': 72.45},
    'Panama':                 {'top23': 68.73, 'top11': 68.73},
    'New Zealand':            {'top23': 67.43, 'top11': 69.55},
    'Haiti':                  {'top23': 66.67, 'top11': 66.67},
    'Qatar':                  {'top23': 65.00, 'top11': 68.00},
    'Curacao':                {'top23': 65.00, 'top11': 68.00},
    'Cape Verde':             {'top23': 65.00, 'top11': 68.00},
    'Jordan':                 {'top23': 65.00, 'top11': 68.00},
    'Uzbekistan':             {'top23': 65.00, 'top11': 68.00},
    'Iraq':                   {'top23': 63.78, 'top11': 63.78},
    'South Africa':           {'top23': 62.64, 'top11': 65.64},
}

# 정규화된 팀 강도 (0~1)
# TOP23 평균 기준, 최고팀(프랑스 84.65) 대비 비율
_max_strength = 84.65
TEAM_STRENGTH_NORMALIZED = {
    team: round(vals['top23'] / _max_strength, 4)
    for team, vals in TEAM_STRENGTH_FC25.items()
}
# ================================
# Transfermarkt 데이터 기반 팀 강도
# analysis.py 실행 결과 (2026.04)
# ================================
TEAM_MARKET_STRENGTH = {
    'England': 1.0, 'France': 0.8189, 'Spain': 0.8942,
    'Brazil': 0.717, 'Portugal': 0.5699, 'Argentina': 0.5337,
    'Netherlands': 0.5326, 'Germany': 0.5014, 'Belgium': 0.361,
    'Sweden': 0.3156, 'Norway': 0.3142, 'Colombia': 0.1928,
    'United States': 0.2602, 'Croatia': 0.178, 'Uruguay': 0.1574,
    'Austria': 0.134, 'Senegal': 0.1571, 'Japan': 0.1939,
    'Switzerland': 0.168, 'Czech Republic': 0.1025, 'Mexico': 0.1106,
    'Scotland': 0.1123, 'Canada': 0.1216, 'Ecuador': 0.1686,
    'Bosnia and Herzegovina': 0.0527, 'Ghana': 0.1192, 'Paraguay': 0.0689,
    'South Korea': 0.0856, 'Algeria': 0.0468, 'Jordan': 0.0084,
    'Morocco': 0.057, 'Australia': 0.0383, 'Uzbekistan': 0.0314,
    'Iran': 0.0177, 'Curacao': 0.0027, 'Egypt': 0.0458,
    'Iraq': 0.0046, 'Panama': 0.0188, 'Haiti': 0.0049,
    'Tunisia': 0.0088, 'New Zealand': 0.0127, 'Cape Verde': 0.0061,
    'South Africa': 0.0141, 'Saudi Arabia': 0.0117, 'Qatar': 0.0085,
}

TEAM_FORM_INDEX = {
    'England': 1.0, 'France': 0.8969, 'Spain': 0.7264,
    'Brazil': 0.8283, 'Portugal': 0.711, 'Argentina': 0.7257,
    'Netherlands': 0.6895, 'Germany': 0.8065, 'Belgium': 0.6806,
    'Sweden': 0.5092, 'Norway': 0.5324, 'Colombia': 0.5088,
    'United States': 0.5245, 'Croatia': 0.4825, 'Uruguay': 0.4772,
    'Austria': 0.4745, 'Senegal': 0.4085, 'Japan': 0.4485,
    'Switzerland': 0.4069, 'Czech Republic': 0.4636, 'Mexico': 0.5018,
    'Scotland': 0.5401, 'Canada': 0.3451, 'Ecuador': 0.2844,
    'Bosnia and Herzegovina': 0.3821, 'Ghana': 0.3826, 'Paraguay': 0.2615,
    'South Korea': 0.323, 'Algeria': 0.2788, 'Jordan': 0.1678,
    'Morocco': 0.2238, 'Australia': 0.3201, 'Uzbekistan': 0.1498,
    'Iran': 0.2201, 'Curacao': 0.0478, 'Egypt': 0.2643,
    'Iraq': 0.1366, 'Panama': 0.1917, 'Haiti': 0.1401,
    'Tunisia': 0.1192, 'New Zealand': 0.1724, 'Cape Verde': 0.1146,
    'South Africa': 0.1195, 'Saudi Arabia': 0.1061, 'Qatar': 0.114,
}

TEAM_INJURY_INDEX = {
    'England': 0.585, 'France': 0.591, 'Spain': 0.51,
    'Brazil': 0.528, 'Portugal': 0.352, 'Argentina': 0.413,
    'Netherlands': 0.443, 'Germany': 0.747, 'Belgium': 0.368,
    'Sweden': 0.353, 'Norway': 0.423, 'Colombia': 0.275,
    'United States': 0.428, 'Croatia': 0.315, 'Uruguay': 0.292,
    'Austria': 0.349, 'Senegal': 0.307, 'Japan': 0.431,
    'Switzerland': 0.342, 'Czech Republic': 0.331, 'Mexico': 0.405,
    'Scotland': 0.52, 'Canada': 0.289, 'Ecuador': 0.282,
    'Bosnia and Herzegovina': 0.262, 'Ghana': 0.383, 'Paraguay': 0.216,
    'South Korea': 0.353, 'Algeria': 0.251, 'Jordan': 0.111,
    'Morocco': 0.278, 'Australia': 0.41, 'Uzbekistan': 0.164,
    'Iran': 0.258, 'Curacao': 0.0, 'Egypt': 0.374,
    'Iraq': 0.137, 'Panama': 0.265, 'Haiti': 0.199,
    'Tunisia': 0.192, 'New Zealand': 0.3, 'Cape Verde': 0.242,
    'South Africa': 0.335, 'Saudi Arabia': 0.379, 'Qatar': 0.482,
}

TEAM_OVERALL_STRENGTH = {
    'England': 0.8538, 'France': 0.7437, 'Spain': 0.7344,
    'Brazil': 0.6947, 'Portugal': 0.6388, 'Argentina': 0.6142,
    'Netherlands': 0.5936, 'Germany': 0.5461, 'Belgium': 0.5406,
    'Sweden': 0.4662, 'Norway': 0.4563, 'Colombia': 0.4364,
    'United States': 0.4307, 'Croatia': 0.4113, 'Uruguay': 0.407,
    'Austria': 0.3824, 'Senegal': 0.3791, 'Japan': 0.3768,
    'Switzerland': 0.3741, 'Czech Republic': 0.3705, 'Mexico': 0.3686,
    'Scotland': 0.354, 'Canada': 0.3472, 'Ecuador': 0.3465,
    'Bosnia and Herzegovina': 0.3393, 'Ghana': 0.3358, 'Paraguay': 0.3151,
    'South Korea': 0.309, 'Algeria': 0.3036, 'Jordan': 0.2843,
    'Morocco': 0.2816, 'Australia': 0.2749, 'Uzbekistan': 0.274,
    'Iran': 0.2696, 'Curacao': 0.2678, 'Egypt': 0.2673,
    'Iraq': 0.2654, 'Panama': 0.2584, 'Haiti': 0.2512,
    'Tunisia': 0.2472, 'New Zealand': 0.2404, 'Cape Verde': 0.232,
    'South Africa': 0.2137, 'Saudi Arabia': 0.1971, 'Qatar': 0.1728,
}