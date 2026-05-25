# ================================
# optuna_tune.py - XGBoost 하이퍼파라미터 자동 최적화
# ================================
import optuna
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import cross_val_score
from model import (
    load_match_data, load_ranking_data,
    calculate_continent_winrate, build_features,
    build_team_cache, build_h2h_cache
)
from config import GROUPS_2026

optuna.logging.set_verbosity(optuna.logging.WARNING)

print("데이터 로딩 중...")
df      = load_match_data()
ranking = load_ranking_data()

HIGH_QUALITY = [
    'FIFA World Cup', 'FIFA World Cup qualification',
    'UEFA Euro', 'UEFA Euro qualification',
    'Copa América', 'African Cup of Nations',
    'AFC Asian Cup', 'UEFA Nations League',
    'CONCACAF Nations League', 'Gold Cup',
]
wc_df = df[df['tournament'].isin(HIGH_QUALITY)].copy().reset_index(drop=True)

continent_winrate = calculate_continent_winrate(df)
feat_df = build_features(wc_df, df, ranking, continent_winrate)

label_map = {-1: 0, 0: 1, 1: 2}
X = feat_df
y = wc_df['result'].map(label_map)

print(f"학습 데이터: {len(X)}경기, {len(X.columns)}개 피처")

def objective(trial):
    params = {
        'n_estimators':     trial.suggest_int('n_estimators', 200, 1000),
        'max_depth':        trial.suggest_int('max_depth', 2, 6),
        'learning_rate':    trial.suggest_float('learning_rate', 0.01, 0.1),
        'subsample':        trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'gamma':            trial.suggest_float('gamma', 0, 0.5),
        'reg_alpha':        trial.suggest_float('reg_alpha', 0, 1.0),
        'reg_lambda':       trial.suggest_float('reg_lambda', 0.5, 2.0),
        'nthread':          1,
        'random_state':     42,
        'eval_metric':      'mlogloss',
        'verbosity':        0,
    }

    model = XGBClassifier(**params)
    scores = cross_val_score(model, X, y, cv=5, scoring='accuracy', n_jobs=1)
    return scores.mean()

print("\nOptuna 최적화 시작... (약 30~60분)")
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100, show_progress_bar=True)

print(f"\n{'='*50}")
print(f"최적 정확도: {study.best_value*100:.2f}%")
print(f"최적 파라미터:")
for k, v in study.best_params.items():
    print(f"  {k}: {v}")

print(f"\n# config.py XGB_PARAMS 교체:")
print(f"XGB_PARAMS = {{")
for k, v in study.best_params.items():
    if isinstance(v, float):
        print(f"    '{k}': {round(v, 4)},")
    else:
        print(f"    '{k}': {v},")
print(f"    'nthread': 1,")
print(f"    'random_state': 42,")
print(f"    'eval_metric': 'mlogloss',")
print(f"    'verbosity': 0,")
print(f"}}")