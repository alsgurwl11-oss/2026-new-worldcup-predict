# ================================
# motivation.py - PL 실험 교훈 기반 보정 모듈
# ================================
# 추가된 피처:
#   1. 동기부여 지수     - 이미 통과/탈락/반드시이겨야
#   2. 로테이션 감지     - 조별 3차전 확정팀 주전 아낌
#   3. xG 피드백 루프   - 이전 경기 운/불운 → 다음 경기 보정
#   4. 언오버 자동 전환  - 1x2 신뢰도 낮으면 오버언더로 전환
# ================================

from config import MOTIVATION_CONFIG, OVER_UNDER_CONFIG, FEEDBACK_CONFIG, ROTATION_CONFIG


# ================================
# 1. 동기부여 지수
# ================================

def calculate_motivation_index(team_context: dict) -> float:
    """
    팀 상황별 동기부여 지수 계산

    PL 교훈:
    - 빌라 케이스: 챔스 확정됐어도 자존심으로 맨시티 이김 → pride_factor
    - 토트넘 케이스: 강등탈출 경기 수비집중 1-0 → must_win은 오히려 언더 유발

    반환: -1.0 ~ +1.0 사이 정규화된 보정값
    """
    cfg = MOTIVATION_CONFIG
    score = 0

    if team_context.get('already_qualified'):
        score += cfg['already_qualified']   # -2: 이미 16강 → 동기 하락

    if team_context.get('already_eliminated'):
        score += cfg['already_eliminated']  # -3: 탈락 확정 → 의욕 없음

    if team_context.get('must_win'):
        score += cfg['must_win']            # +3: 반드시 이겨야 → 최고 동기

    if team_context.get('pride_factor'):
        score += cfg['pride_factor']        # +1: 강팀 자존심 (순위와 무관)

    # -5 ~ +4 범위 → -1.0 ~ +1.0 으로 정규화
    normalized = score / 5.0
    return round(max(-1.0, min(1.0, normalized)), 3)


def apply_motivation_to_probs(home_prob, draw_prob, away_prob,
                               home_context: dict, away_context: dict) -> tuple:
    """
    동기부여 지수를 확률에 반영

    원리: 동기 높은 팀 승률 소폭 상승, 상대 승률 소폭 하락
    강하게 적용하면 과적합 → scale 0.05로 제한
    """
    cfg = MOTIVATION_CONFIG
    home_mi = calculate_motivation_index(home_context)
    away_mi = calculate_motivation_index(away_context)

    # 동기 차이 → 확률 보정 (scale: 10점 차이 = 5% 변화)
    mi_diff = home_mi - away_mi
    adjustment = mi_diff * cfg['scale']

    new_home = home_prob + adjustment
    new_away = away_prob - adjustment

    # 최솟값 보장 (음수 방지)
    new_home = max(0.05, new_home)
    new_away = max(0.05, new_away)

    # 재정규화
    total = new_home + draw_prob + new_away
    return new_home / total, draw_prob / total, new_away / total


# ================================
# 2. 로테이션 감지
# ================================

def detect_rotation_risk(team: str, match_day: int,
                          team_context: dict, team_cache: dict) -> dict:
    """
    조별리그 3차전에서 16강 확정팀 로테이션 가능성 판단

    PL 교훈:
    - 맨유 로테이션인데 브라이튼 원정 3-0 대승
    - 즉, 로테이션 팀 결과는 예측불가 → 신뢰도 낮춤

    반환:
        rotation_detected: bool
        xg_penalty: float (xG에 곱할 계수, 1.0 = 페널티 없음)
        confidence_penalty: float (1x2 신뢰도에 뺄 값)
    """
    cfg = ROTATION_CONFIG

    # 기본값: 로테이션 없음
    result = {
        'rotation_detected': False,
        'xg_penalty': 1.0,
        'confidence_penalty': 0.0,
        'reason': ''
    }

    # 조건 1: 3차전이 아니면 패스
    if match_day != cfg['match_day']:
        return result

    # 조건 2: 이미 16강 통과한 팀만
    if not team_context.get('already_qualified'):
        return result

    # 조건 3: 강팀(랭킹 20위 이내)만 로테이션 가능성 있음
    rank = team_cache.get(team, {}).get('rank', 99)
    if rank > cfg['strong_team_threshold']:
        return result

    # 로테이션 감지됨
    result['rotation_detected'] = True
    result['xg_penalty'] = 1 + cfg['lineup_penalty']        # 0.85 (15% 감소)
    result['confidence_penalty'] = cfg['confidence_penalty'] # -0.10
    result['reason'] = f"{team} 3차전 16강확정 → 로테이션 가능성 (랭킹 {rank}위)"

    return result


# ================================
# 3. xG 피드백 루프
# ================================

def calculate_xg_feedback_modifier(prev_xg: float, prev_actual: float) -> float:
    """
    이전 경기 xG vs 실제 득점 비교 → 다음 경기 기대값 보정

    PL 교훈:
    - 미토마 없는 브라이튼: xG는 나왔을 텐데 득점 못함 → 다음엔 상향 여지
    - 반대로 운 좋게 많이 넣은 팀 → 다음엔 하향 보정

    예시:
    - prev_xg=1.8, actual=0.5 → modifier = +0.15 (운 없었음)
    - prev_xg=0.8, actual=2.0 → modifier = -0.10 (운 좋았음)
    - prev_xg=1.5, actual=1.5 → modifier = 0.0 (정상)
    """
    cfg = FEEDBACK_CONFIG
    diff = prev_xg - prev_actual  # 양수 = 불운(xG > 실제득점), 음수 = 행운

    if diff > cfg['xg_luck_threshold']:
        # 불운: xG보다 훨씬 못 넣음 → 다음 경기 기대값 상향
        modifier = cfg['xg_modifier_up']
    elif diff < -cfg['xg_luck_threshold']:
        # 행운: xG보다 많이 넣음 → 다음 경기 기대값 하향
        modifier = cfg['xg_modifier_down']
    else:
        # 정상 범위
        modifier = 0.0

    return round(max(-cfg['max_modifier'], min(cfg['max_modifier'], modifier)), 3)


def apply_xg_feedback(base_xg: float, modifier: float) -> float:
    """피드백 modifier를 xG에 적용"""
    return round(max(0.3, min(3.5, base_xg + modifier)), 2)


# ================================
# 4. 언오버 자동 전환
# ================================

def get_1x2_confidence(home_prob: float, draw_prob: float, away_prob: float) -> float:
    """
    1x2 신뢰도 계산: 가장 높은 확률값

    0.60 미만 → 어느 결과도 확신하기 어려운 경기
    PL 교훈: 이런 경기는 언오버로 전환이 더 적중률 높음 (GW37 검증)
    """
    return max(home_prob, draw_prob, away_prob)


def get_over_under_recommendation(home_xg: float, away_xg: float,
                                   round_name: str = 'Group',
                                   home_context: dict = None,
                                   away_context: dict = None) -> dict:
    """
    오버/언더 추천 계산

    월드컵 기준선:
    - 조별리그: 2.0 (평균 2.6골/경기, PL 2.5보다 낮게 설정)
    - 토너먼트: 2.5 (긴장감으로 저득점 경향)

    PL 교훈: GW38 오버 역사적 패턴이 5:5로 빗나감
    → 역사적 패턴에 과의존 금지, xG 기반으로만 판단
    """
    cfg = OVER_UNDER_CONFIG
    home_context = home_context or {}
    away_context = away_context or {}

    # 라운드별 기준선 선택
    is_group = round_name == 'Group'
    threshold = cfg['group_stage_line'] if is_group else cfg['knockout_line']

    expected_total = home_xg + away_xg

    # 동기부여 기반 득점 조정
    # 절박한 팀(must_win)은 수비집중 → 언더 유발 (토트넘 케이스)
    if home_context.get('must_win') or away_context.get('must_win'):
        expected_total *= 0.92  # 8% 하향 보정
    # 탈락 확정팀이 있으면 공격적으로 나올 수도 있음
    elif home_context.get('already_eliminated') or away_context.get('already_eliminated'):
        expected_total *= 1.05  # 5% 상향 (체면치레 공격)

    # 조별리그 오버 약간 유리 보정 (월드컵 구조상)
    if is_group:
        expected_total += cfg['group_over_adjustment']

    # 오버/언더 판단
    over_prob = round(expected_total / (expected_total + threshold) * 100, 1)
    under_prob = round(100 - over_prob, 1)

    is_over = expected_total > threshold

    return {
        'recommendation': 'OVER' if is_over else 'UNDER',
        'line': threshold,
        'expected_total': round(expected_total, 2),
        'over_prob': over_prob,
        'under_prob': under_prob,
        'confidence': round(max(over_prob, under_prob), 1),
        'reason': _build_ou_reason(expected_total, threshold, is_group,
                                    home_context, away_context),
    }


def _build_ou_reason(expected: float, line: float, is_group: bool,
                      home_ctx: dict, away_ctx: dict) -> str:
    """언오버 추천 근거 텍스트 생성"""
    parts = []

    if expected > line:
        parts.append(f"예상 총득점 {expected:.1f} > 기준선 {line}")
    else:
        parts.append(f"예상 총득점 {expected:.1f} < 기준선 {line}")

    if is_group:
        parts.append("조별리그(오버 유리)")

    if home_ctx.get('must_win') or away_ctx.get('must_win'):
        parts.append("절박팀 수비집중 → 언더 유인")

    if home_ctx.get('already_eliminated') or away_ctx.get('already_eliminated'):
        parts.append("탈락확정팀 공격적 플레이 가능")

    return " / ".join(parts)


# ================================
# 5. 종합 보정 (predict.py에서 호출)
# ================================

def apply_all_adjustments(home: str, away: str,
                           home_prob: float, draw_prob: float, away_prob: float,
                           home_xg: float, away_xg: float,
                           match_context: dict,
                           team_cache: dict,
                           round_name: str = 'Group') -> dict:
    """
    모든 보정을 한 번에 적용하는 통합 함수

    predict.py의 ensemble_predict()에서 이 함수 하나만 호출

    match_context 구조:
    {
        'match_day': 1~3,          # 조별리그 몇 차전
        'home': {                  # 홈팀 상황
            'already_qualified': False,
            'already_eliminated': False,
            'must_win': True,
            'pride_factor': False,
            'prev_xg': 1.5,        # 이전 경기 xG (없으면 None)
            'prev_actual': 1.0,    # 이전 경기 실제 득점 (없으면 None)
        },
        'away': { ... }            # 어웨이팀 동일 구조
    }
    """
    home_ctx = match_context.get('home', {})
    away_ctx = match_context.get('away', {})
    match_day = match_context.get('match_day', 1)

    # --- A. 동기부여 보정 ---
    adj_home, adj_draw, adj_away = apply_motivation_to_probs(
        home_prob, draw_prob, away_prob, home_ctx, away_ctx
    )

    # --- B. 로테이션 감지 ---
    home_rot = detect_rotation_risk(home, match_day, home_ctx, team_cache)
    away_rot = detect_rotation_risk(away, match_day, away_ctx, team_cache)

    # 로테이션 xG 페널티 적용
    adj_home_xg = home_xg * home_rot['xg_penalty']
    adj_away_xg = away_xg * away_rot['xg_penalty']

    # 로테이션 신뢰도 페널티 → 1x2 확률 중심화 (0.33에 가깝게)
    home_conf_pen = home_rot['confidence_penalty'] + away_rot['confidence_penalty']
    if home_conf_pen < 0:
        adj_home = adj_home + home_conf_pen * (adj_home - 0.33)
        adj_away = adj_away + home_conf_pen * (adj_away - 0.33)
        total = adj_home + adj_draw + adj_away
        adj_home, adj_draw, adj_away = adj_home/total, adj_draw/total, adj_away/total

    # --- C. xG 피드백 루프 ---
    home_prev_xg = home_ctx.get('prev_xg')
    home_prev_actual = home_ctx.get('prev_actual')
    if home_prev_xg is not None and home_prev_actual is not None:
        modifier = calculate_xg_feedback_modifier(home_prev_xg, home_prev_actual)
        adj_home_xg = apply_xg_feedback(adj_home_xg, modifier)

    away_prev_xg = away_ctx.get('prev_xg')
    away_prev_actual = away_ctx.get('prev_actual')
    if away_prev_xg is not None and away_prev_actual is not None:
        modifier = calculate_xg_feedback_modifier(away_prev_xg, away_prev_actual)
        adj_away_xg = apply_xg_feedback(adj_away_xg, modifier)

    # --- D. 언오버 자동 전환 판단 ---
    confidence_1x2 = get_1x2_confidence(adj_home, adj_draw, adj_away)
    cfg = OVER_UNDER_CONFIG
    auto_switch = confidence_1x2 < cfg['confidence_threshold']

    ou_result = get_over_under_recommendation(
        adj_home_xg, adj_away_xg,
        round_name, home_ctx, away_ctx
    )

    # --- 최종 결과 반환 ---
    return {
        # 보정된 1x2 확률
        'home_prob':       round(adj_home, 4),
        'draw_prob':       round(adj_draw, 4),
        'away_prob':       round(adj_away, 4),

        # 보정된 xG
        'home_xg':         round(adj_home_xg, 2),
        'away_xg':         round(adj_away_xg, 2),

        # 언오버 자동 전환 여부
        'auto_switch_ou':  auto_switch,
        'confidence_1x2':  round(confidence_1x2, 3),
        'over_under':      ou_result,

        # 디버그용 상세 정보
        'debug': {
            'home_motivation': calculate_motivation_index(home_ctx),
            'away_motivation': calculate_motivation_index(away_ctx),
            'home_rotation':   home_rot['rotation_detected'],
            'away_rotation':   away_rot['rotation_detected'],
            'home_rotation_reason': home_rot['reason'],
            'away_rotation_reason': away_rot['reason'],
        }
    }