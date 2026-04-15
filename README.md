# ⚽ 2026 FIFA 월드컵 AI 승부예측기

> XGBoost + Opta + 배당률 + ELO 앙상블 기반 2026 북중미 월드컵 예측 웹앱

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-orange)

---

## 📌 프로젝트 개요

2026 FIFA 북중미 월드컵(48개국) 경기 결과를 AI로 예측하는 풀스택 웹 애플리케이션입니다.  
역대 국제경기 데이터 47,000+ 경기와 FC25 선수 능력치를 학습해 경기 결과를 예측합니다.

---

## 🧠 예측 모델 구조

### 앙상블 방식 (4가지 소스 결합)

| 소스 | 가중치 | 설명 |
|------|--------|------|
| XGBoost ML 모델 | 20% | 역대 경기 데이터 기반 머신러닝 |
| Opta 예측값 | 20% | 전문 스포츠 데이터 분석사 예측 |
| 배당률 역산 | 35% | ESPN 실시간 배당률 확률 변환 |
| ELO 레이팅 | 25% | Opta 강도 기반 ELO 계산 |

> 가중치는 2018/2022 월드컵 백테스트 그리드 서치로 최적화
> 배당률이 가장 높은 가중치 → 전문 베터 집단지성이 가장 정확

### ML 모델 피처 (34개)

| 카테고리 | 피처 |
|----------|------|
| FIFA 랭킹 | FIFA 포인트 차이, 랭킹 차이 |
| 경기 환경 | 중립경기장, 개최국 여부 |
| 대륙 | 대륙간 상성, 개최대륙 패널티 |
| 상대전적 | H2H 승률, H2H 어드밴티지 |
| 월드컵 경험 | 역대 월드컵 출전 경험치 |
| 최근 폼 | 최근 5경기 폼, 폼 차이 |
| 득실 | 평균 득점/실점 차이 |
| 징크스 | 디펜딩 챔피언 징크스 |
| FC25 능력치 | TOP23/TOP11 평균 능력치 차이 |
| Transfermarkt | 시장가치 강도, 부상 취약도, 폼 지수 |

---

## 🌟 주요 기능

### ⚽ 경기 예측
- 임의의 두 팀 선택 후 승/무/패 확률 예측
- FIFA 랭킹, H2H 상대전적 표시
- 앙상블 소스별 상세 확률 제공

### 📊 조별리그 시뮬레이션
- A~L조 각 조별 순위 확률 시뮬레이션 (3,000회)
- 평균 승점, 32강 진출 확률 계산
- 조별 경기 예측 (6경기 개별 확률)

### 📈 32강 진출 확률
- 전체 47개국 32강 진출 확률 순위
- 색상으로 직관적 표시 (초록/노랑/빨강)

### 🏆 우승팀 예측
- 전체 대회 시뮬레이션 (300회)
- 우승/결승/4강/8강 진출 확률

### 🗓️ 토너먼트 브라켓
- 라운드별 진출 확률
- 예상 상대팀 TOP3

### 🇰🇷 한국 시나리오
- 한국 라운드별 진출 확률
- 예상 상대팀 TOP8 분석

---

## 📁 프로젝트 구조
2026-new-worldcup-predict/
├── app.py          # Flask 서버 (라우트만 담당)
├── config.py       # 설정값 (대진표, 배당률, Opta 등)
├── model.py        # 데이터 로딩 및 모델 학습
├── predict.py      # 앙상블 예측 함수
├── simulate.py     # 시뮬레이션 함수
├── templates/
│   └── index.html  # 프론트엔드 (6개 탭)
├── results.csv          # 역대 국제경기 결과
├── fifa_ranking-*.csv   # FIFA 랭킹 데이터
└── players_info.csv     # FC25 선수 능력치

---

## 🛠️ 설치 및 실행

### 1. 레포지토리 클론
```bash
git clone https://github.com/alsgurwl11-oss/2026-new-worldcup-predict.git
cd 2026-new-worldcup-predict
```

### 2. 가상환경 생성
```bash
conda create -n worldcup python=3.11
conda activate worldcup
```

### 3. 라이브러리 설치
```bash
pip install flask xgboost scikit-learn pandas numpy openpyxl
```

### 4. 데이터 파일 준비
아래 파일들을 프로젝트 폴더에 넣어주세요:

| 파일 | 출처 |
|------|------|
| results.csv | [Kaggle - international football results](https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017) |
| fifa_ranking-*.csv | [Kaggle - FIFA World Ranking](https://www.kaggle.com/datasets/cashncarry/fifaworldranking) |
| players_info.csv | [Kaggle - FC25 Player Ratings](https://www.kaggle.com/datasets) |

### 5. 서버 실행
```bash
python app.py
```

### 6. 브라우저 접속
http://127.0.0.1:5000
> ⚠️ 첫 실행 시 모델 학습에 5~10분 소요됩니다.  
> 이후 실행부터는 model.pkl 로딩으로 즉시 시작됩니다.

---

## 📊 데이터 출처

| 데이터 | 출처 | 기간 |
|--------|------|------|
| 국제경기 결과 | Kaggle (martj42) | 1872~2024 |
| FIFA 랭킹 | Kaggle (cashncarry) | 2023~2024 |
| FC25 선수 능력치 | Kaggle | 2024년 기준 |
| Opta 우승 확률 | The Analyst | 2025년 기준 |
| 배당률 | ESPN | 2026년 4월 기준 |

---

## 🔧 기술 스택

**Backend**
- Python 3.11
- Flask 3.0
- XGBoost 2.0
- scikit-learn
- pandas / numpy

**Frontend**
- HTML5 / CSS3 / JavaScript
- 순수 바닐라 JS (프레임워크 없음)

---

## 📈 모델 성능

| 대회 | 정확도 |
|------|--------|
| 2022 카타르 월드컵 백테스트 | 60.9% |
| 2018 러시아 월드컵 백테스트 | 48.4% |
| 평균 | 54.7% |

### 라운드별 정확도 (2022)
| 라운드 | 정확도 |
|--------|--------|
| 4강 | 100% |
| 16강 | 75% |
| 조별리그 | 62.5% |
| 8강 | 25% |

> 이론적 상한선: 65~66% (축구 특성상 랜덤 요소 30~40%)
---

## 👨‍💻 개발자

- **개발**: 스포츠 데이터 분석 취업 준비생
- **목적**: 포트폴리오 프로젝트
- **기간**: 2026년 4월

---
### ⚡ 이변 경보 (UVI)
- 데이터 기반 이변 취약성 지수 계산
- xG 차이, 슈팅 효율, 점유율 역설, 라운드별 이변율 분석
- 4단계 신뢰도: ✅ 높음 / 🟡 가능 / 🔴 주의 / ⚡ 경보
- 역대 월드컵 분석: 8강 이변율 37.5%, 조별 21.9%

---
## 📝 TODO

### 완료
- [x] 백테스트 시스템 구축 (2022: 60.9%)
- [x] 앙상블 가중치 최적화
- [x] Transfermarkt 데이터 통합
- [x] UVI 이변 경보 시스템
- [x] requirements.txt 추가

### 진행 예정
- [ ] Railway 배포 (인터넷 공개)
- [ ] 데이터 누수 수정
- [ ] 테스트 코드 추가
- [ ] 월드컵 개막 후 실시간 업데이트
