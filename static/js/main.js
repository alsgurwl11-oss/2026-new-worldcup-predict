// ================================
// main.js - 기본 함수 (탭, 경기예측, 조별리그, 32강, 우승예측)
// ================================

// --------------------------------
// 공통 유틸
// --------------------------------
function showTab(name, btn) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    const target = document.getElementById('tab-' + name);
    if (target) target.classList.add('active');
    if (btn) btn.classList.add('active');
}

function probClass(val) {
    return val >= 70 ? 'prob-high' : val >= 40 ? 'prob-mid' : 'prob-low';
}

// --------------------------------
// ① 경기 예측
// --------------------------------
async function predictMatch() {
    const home = document.getElementById('home-team').value;
    const away = document.getElementById('away-team').value;
    if (!home || !away) { alert('팀을 선택해주세요!'); return; }
    if (home === away)  { alert('서로 다른 팀을 선택해주세요!'); return; }

    const res  = await fetch('/api/predict', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({home, away})
    });
    const data = await res.json();

    document.getElementById('match-title').textContent = `${data.home} vs ${data.away}`;
    document.getElementById('home-label').textContent  = data.home;
    document.getElementById('away-label').textContent  = data.away;

    setTimeout(() => {
        document.getElementById('bar-home').style.width = data.home_win + '%';
        document.getElementById('bar-home').textContent = data.home_win + '%';
        document.getElementById('bar-draw').style.width = data.draw + '%';
        document.getElementById('bar-draw').textContent = data.draw + '%';
        document.getElementById('bar-away').style.width = data.away_win + '%';
        document.getElementById('bar-away').textContent = data.away_win + '%';
    }, 100);

    document.getElementById('home-rank').textContent = data.home_rank + '위';
    document.getElementById('away-rank').textContent = data.away_rank + '위';
    document.getElementById('h2h-home').textContent  = data.h2h_home + '%';
    document.getElementById('h2h-away').textContent  = data.h2h_away + '%';
    document.getElementById('result-box').style.display = 'block';
    // 라인업 자동 로딩
    loadLineupAfterPredict(home, away);
}

// --------------------------------
// ② 조별리그 순위
// --------------------------------
async function simulateGroup(group, btn) {
    document.querySelectorAll('.group-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    document.getElementById('group-result').innerHTML = `
        <div class="loading"><div class="spinner"></div><p>${group}조 시뮬레이션 중...</p></div>`;

    const res  = await fetch('/api/simulate_group', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({group})
    });
    const data = await res.json();

    let html = `
        <h3 style="margin-bottom:15px;">${group}조 시뮬레이션 결과</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>팀</th><th>FIFA 랭킹</th><th>1위</th><th>2위</th>
                    <th>3위</th><th>4위</th><th>평균 승점</th><th>32강 진출</th>
                </tr>
            </thead><tbody>`;

    data.result.forEach(team => {
        html += `
            <tr>
                <td><strong>${team.team}</strong></td>
                <td style="color:#aaa">${team.rank}위</td>
                <td>${team.first}%</td>
                <td>${team.second}%</td>
                <td>${team.third}%</td>
                <td>${team.fourth}%</td>
                <td>${team.avg_points}점</td>
                <td>
                    <span class="${probClass(team.qualify)}">${team.qualify}%</span>
                    <div class="qualify-bar">
                        <div class="qualify-fill" style="width:${team.qualify}%"></div>
                    </div>
                </td>
            </tr>`;
    });

    html += '</tbody></table>';
    document.getElementById('group-result').innerHTML = html;
}

// --------------------------------
// ② 조별리그 경기
// --------------------------------
async function loadGroupMatches(group, btn) {
    document.querySelectorAll('.group-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    document.getElementById('group-result').innerHTML = `
        <div class="loading"><div class="spinner"></div><p>${group}조 경기 예측 중...</p></div>`;

    const res  = await fetch('/api/group_matches', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({group})
    });
    const data = await res.json();

    let html = `<h3 style="margin-bottom:15px;">${group}조 경기별 예측</h3>`;

    data.matches.forEach((match, idx) => {
        const homeClass = match.home_win >= match.away_win ? 'prob-high' : 'prob-low';
        const awayClass = match.away_win > match.home_win  ? 'prob-high' : 'prob-low';
        html += `
            <div style="background:#0d0d2e; border-radius:12px; padding:20px; margin-bottom:15px; border:1px solid #333;">
                <div style="text-align:center; margin-bottom:15px; color:#aaa; font-size:0.85em;">경기 ${idx+1}</div>
                <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:15px;">
                    <div style="text-align:center; flex:1;">
                        <div style="font-weight:bold; font-size:1.1em;">${match.home}</div>
                        <div style="color:#aaa; font-size:0.8em;">FIFA ${match.home_rank}위</div>
                    </div>
                    <div style="font-size:1.3em; font-weight:bold; color:#4a4aff; padding:0 15px;">VS</div>
                    <div style="text-align:center; flex:1;">
                        <div style="font-weight:bold; font-size:1.1em;">${match.away}</div>
                        <div style="color:#aaa; font-size:0.8em;">FIFA ${match.away_rank}위</div>
                    </div>
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; text-align:center;">
                    <div style="background:#1a1a3e; border-radius:8px; padding:12px;">
                        <div style="color:#aaa; font-size:0.75em; margin-bottom:5px;">홈팀 승</div>
                        <div class="${homeClass}" style="font-size:1.3em;">${match.home_win}%</div>
                    </div>
                    <div style="background:#1a1a3e; border-radius:8px; padding:12px;">
                        <div style="color:#aaa; font-size:0.75em; margin-bottom:5px;">무승부</div>
                        <div style="font-size:1.3em; color:#ffbb44; font-weight:bold;">${match.draw}%</div>
                    </div>
                    <div style="background:#1a1a3e; border-radius:8px; padding:12px;">
                        <div style="color:#aaa; font-size:0.75em; margin-bottom:5px;">원정팀 승</div>
                        <div class="${awayClass}" style="font-size:1.3em;">${match.away_win}%</div>
                    </div>
                </div>
            </div>`;
    });

    document.getElementById('group-result').innerHTML = html;
}

// --------------------------------
// ③ 32강 확률
// --------------------------------
async function simulateAll() {
    document.getElementById('ranking-result').innerHTML = `
        <div class="loading"><div class="spinner"></div><p>전체 시뮬레이션 중...</p></div>`;

    const res  = await fetch('/api/simulate_all');
    const data = await res.json();

    let allTeams = [];
    Object.values(data).forEach(group => group.forEach(team => allTeams.push(team)));
    allTeams.sort((a, b) => b.qualify - a.qualify);

    let html = `
        <table class="data-table">
            <thead>
                <tr><th>#</th><th>팀</th><th>FIFA 랭킹</th><th>32강 진출 확률</th></tr>
            </thead><tbody>`;

    allTeams.forEach((team, idx) => {
        html += `
            <tr>
                <td class="rank-num">${idx + 1}</td>
                <td>${team.team}</td>
                <td style="color:#aaa">${team.rank}위</td>
                <td>
                    <span class="${probClass(team.qualify)}">${team.qualify}%</span>
                    <div class="qualify-bar">
                        <div class="qualify-fill" style="width:${team.qualify}%"></div>
                    </div>
                </td>
            </tr>`;
    });

    html += '</tbody></table>';
    document.getElementById('ranking-result').innerHTML = html;
}

// --------------------------------
// ④ 우승 예측
// --------------------------------
async function simulateTournament() {
    document.getElementById('tournament-result').innerHTML = `
        <div class="loading"><div class="spinner"></div><p>전체 대회 시뮬레이션 중...</p></div>`;

    const res  = await fetch('/api/tournament');
    const data = await res.json();

    let html = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>#</th><th>팀</th><th>FIFA 랭킹</th>
                    <th>🏆 우승</th><th>결승</th><th>4강</th><th>8강</th>
                </tr>
            </thead><tbody>`;

    data.forEach((team, idx) => {
        const champClass = team.champion >= 10 ? 'prob-high' :
                           team.champion >= 3  ? 'prob-mid'  : 'prob-low';
        const medal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : (idx + 1);
        html += `
            <tr>
                <td class="rank-num">${medal}</td>
                <td><strong>${team.team}</strong></td>
                <td style="color:#aaa">${team.rank}위</td>
                <td>
                    <span class="${champClass}">${team.champion}%</span>
                    <div class="qualify-bar">
                        <div class="qualify-fill" style="width:${Math.min(team.champion * 3, 100)}%"></div>
                    </div>
                </td>
                <td>${team.final}%</td>
                <td>${team.semi}%</td>
                <td>${team.quarter}%</td>
            </tr>`;
    });

    html += '</tbody></table>';
    document.getElementById('tournament-result').innerHTML = html;
}

// --------------------------------
// ⑤ 토너먼트 브라켓 (구버전 탭용)
// --------------------------------
async function loadBracketPrediction() {
    document.getElementById('bracket-result').innerHTML = `
        <div class="loading"><div class="spinner"></div><p>브라켓 시뮬레이션 중...</p></div>`;

    const res = await fetch('/api/bracket');
    const data = await res.json();

    let html = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>#</th><th>팀</th><th>32강</th><th>16강</th>
                    <th>8강</th><th>4강</th><th>결승</th><th>🏆 우승</th>
                    <th>예상 상대 TOP3</th>
                </tr>
            </thead><tbody>`;

    data.forEach((team, idx) => {
        const champClass = team.champion >= 10 ? 'prob-high' :
                           team.champion >= 3  ? 'prob-mid'  : 'prob-low';
        const opps = team.opponents.map(o => `${o.team} (${o.prob}%)`).join(', ');
        html += `
            <tr>
                <td class="rank-num">${idx + 1}</td>
                <td><strong>${team.team}</strong></td>
                <td>${team.r32}%</td>
                <td>${team.r16}%</td>
                <td>${team.qf}%</td>
                <td>${team.sf}%</td>
                <td>${team.final}%</td>
                <td><span class="${champClass}">${team.champion}%</span></td>
                <td style="font-size:0.8em; color:#aaa;">${opps}</td>
            </tr>`;
    });

    html += '</tbody></table>';
    document.getElementById('bracket-result').innerHTML = html;
}

// ================================
// 라인업 UI - main.js 맨 아래에 추가
// ================================

// 포메이션별 선수 위치 (x%, y% - 피치 기준)
const FORMATION_POS = {
    '4-3-3': [
        {slot:'GK',  x:50, y:88},
        {slot:'LB',  x:12, y:70}, {slot:'CB', x:35, y:73},
        {slot:'CB',  x:65, y:73}, {slot:'RB', x:88, y:70},
        {slot:'CM',  x:20, y:50}, {slot:'CM', x:50, y:48}, {slot:'CM', x:80, y:50},
        {slot:'LW',  x:12, y:24}, {slot:'ST', x:50, y:16}, {slot:'RW', x:88, y:24},
    ],
    '4-2-3-1': [
        {slot:'GK',  x:50, y:88},
        {slot:'LB',  x:12, y:72}, {slot:'CB',  x:36, y:75},
        {slot:'CB',  x:64, y:75}, {slot:'RB',  x:88, y:72},
        {slot:'CDM', x:35, y:55}, {slot:'CDM', x:65, y:55},
        {slot:'LM',  x:12, y:35}, {slot:'CAM', x:50, y:35}, {slot:'RM', x:88, y:35},
        {slot:'ST',  x:50, y:14},
    ],
    '4-4-2': [
        {slot:'GK',  x:50, y:88},
        {slot:'LB',  x:12, y:72}, {slot:'CB', x:36, y:75},
        {slot:'CB',  x:64, y:75}, {slot:'RB', x:88, y:72},
        {slot:'LM',  x:12, y:50}, {slot:'CM', x:36, y:50},
        {slot:'CM',  x:64, y:50}, {slot:'RM', x:88, y:50},
        {slot:'ST',  x:35, y:18}, {slot:'ST', x:65, y:18},
    ],
    '3-5-2': [
        {slot:'GK',  x:50, y:88},
        {slot:'CB',  x:22, y:73}, {slot:'CB', x:50, y:75}, {slot:'CB', x:78, y:73},
        {slot:'LWB', x:7,  y:52}, {slot:'CM', x:30, y:50},
        {slot:'CDM', x:50, y:52}, {slot:'CM', x:70, y:50}, {slot:'RWB', x:93, y:52},
        {slot:'ST',  x:35, y:18}, {slot:'ST', x:65, y:18},
    ],
    '5-3-2': [
        {slot:'GK',  x:50, y:88},
        {slot:'LWB', x:7,  y:68}, {slot:'CB', x:27, y:75},
        {slot:'CB',  x:50, y:77}, {slot:'CB', x:73, y:75}, {slot:'RWB', x:93, y:68},
        {slot:'CM',  x:25, y:48}, {slot:'CM', x:50, y:48}, {slot:'CM', x:75, y:48},
        {slot:'ST',  x:35, y:18}, {slot:'ST', x:65, y:18},
    ],
    '4-1-4-1': [
        {slot:'GK',  x:50, y:88},
        {slot:'LB',  x:12, y:72}, {slot:'CB',  x:36, y:75},
        {slot:'CB',  x:64, y:75}, {slot:'RB',  x:88, y:72},
        {slot:'CDM', x:50, y:57},
        {slot:'LM',  x:12, y:38}, {slot:'CM', x:36, y:38},
        {slot:'CM',  x:64, y:38}, {slot:'RM',  x:88, y:38},
        {slot:'ST',  x:50, y:14},
    ],
};

// 현재 라인업 상태
let currentLineup = { home: null, away: null };

// --------------------------------
// 예측 후 라인업 자동 로딩
// (predictMatch() 마지막에 호출)
// --------------------------------
async function loadLineupAfterPredict(home, away) {
    document.getElementById('lineup-section').style.display = 'block';
    document.getElementById('lu-home-name').textContent = home;
    document.getElementById('lu-away-name').textContent = away;
    document.getElementById('lineup-adj').style.display = 'none';

    // 포메이션 셀렉트 초기화
    const homeFormSel = document.getElementById('lu-home-form');
    const awayFormSel = document.getElementById('lu-away-form');

    // 양팀 라인업 API 호출
    const [homeRes, awayRes] = await Promise.all([
        fetch(`/api/lineup/${encodeURIComponent(home)}`),
        fetch(`/api/lineup/${encodeURIComponent(away)}`),
    ]);
    currentLineup.home = await homeRes.json();
    currentLineup.away = await awayRes.json();

    // 기본 포메이션 셀렉트 맞추기
    homeFormSel.value = currentLineup.home.formation || '4-2-3-1';
    awayFormSel.value = currentLineup.away.formation || '4-2-3-1';

    renderPitch('home', currentLineup.home);
    renderPitch('away', currentLineup.away);
    renderStrength('home', currentLineup.home);
    renderStrength('away', currentLineup.away);
}

// --------------------------------
// 피치 렌더링
// --------------------------------
function renderPitch(side, lineup) {
    const pitchEl = document.getElementById(`pitch-${side}`);
    const formation = lineup.formation || '4-2-3-1';
    const positions = FORMATION_POS[formation] || FORMATION_POS['4-2-3-1'];
    const players   = lineup.players || [];

    // 기존 선수 제거 (SVG 유지)
    pitchEl.querySelectorAll('.player-dot').forEach(el => el.remove());

    positions.forEach((pos, idx) => {
        const player = players[idx];
        if (!player) return;

        const dot = document.createElement('div');
        dot.className = 'player-dot';
        dot.style.left = pos.x + '%';
        dot.style.top  = pos.y + '%';

        const ovr = player.overall || 70;
        const ovrColor = ovr >= 85 ? '#ffbb44' : ovr >= 80 ? '#00ff88' : ovr >= 75 ? '#4a4aff' : '#aaa';
        const shortName = (player.name || '').split(' ').pop() || player.name || '';

        dot.innerHTML = `
            <div class="player-circle" style="border-color:${ovrColor};">
                <span style="color:${ovrColor};font-size:0.8em;">${ovr}</span>
            </div>
            <div class="player-name">${shortName}</div>`;

        dot.title = `${player.name} (OVR ${ovr}) | ${pos.slot}`;
        pitchEl.appendChild(dot);
    });
}

// --------------------------------
// 강도 카드 렌더링
// --------------------------------
function renderStrength(side, lineup) {
    const el = document.getElementById(`lu-${side}-strength`);
    const atk = Math.round((lineup.attack_str  || 0) * 100);
    const mid = Math.round((lineup.mid_str     || 0) * 100);
    const def = Math.round((lineup.defense_str || 0) * 100);
    const avg = lineup.avg_overall || 70;

    el.innerHTML = `
        <div class="str-card">
            <div class="str-label">⚔️ 공격</div>
            <div class="str-val">${atk}</div>
        </div>
        <div class="str-card">
            <div class="str-label">🔄 미드필드</div>
            <div class="str-val">${mid}</div>
        </div>
        <div class="str-card">
            <div class="str-label">🛡️ 수비</div>
            <div class="str-val">${def}</div>
        </div>
        <div style="grid-column:1/-1;text-align:center;color:#aaa;font-size:0.8em;margin-top:4px;">
            평균 오버롤: <strong style="color:#fff;">${avg}</strong>
        </div>`;
}

// --------------------------------
// 포메이션 변경 시 재구성
// --------------------------------
async function changeFormation(side) {
    const formation = document.getElementById(`lu-${side}-form`).value;
    const teamName  = document.getElementById(`lu-${side}-name`).textContent;
    if (!teamName) return;

    const res  = await fetch(`/api/lineup/${encodeURIComponent(teamName)}?formation=${formation}`);
    const data = await res.json();
    currentLineup[side] = data;

    renderPitch(side, data);
    renderStrength(side, data);
}

// --------------------------------
// 라인업 적용 재예측
// --------------------------------
async function predictWithLineup() {
    const home = document.getElementById('lu-home-name').textContent;
    const away = document.getElementById('lu-away-name').textContent;
    if (!home || !away) return;

    const homeForm = document.getElementById('lu-home-form').value;
    const awayForm = document.getElementById('lu-away-form').value;

    const res = await fetch('/api/predict_with_lineup', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            home, away,
            home_formation: homeForm,
            away_formation: awayForm,
            home_players: null,
            away_players: null,
        })
    });
    const data = await res.json();

    // 확률 바 업데이트
    setTimeout(() => {
        document.getElementById('bar-home').style.width = data.home_win + '%';
        document.getElementById('bar-home').textContent = data.home_win + '%';
        document.getElementById('bar-draw').style.width = data.draw + '%';
        document.getElementById('bar-draw').textContent = data.draw + '%';
        document.getElementById('bar-away').style.width = data.away_win + '%';
        document.getElementById('bar-away').textContent = data.away_win + '%';
    }, 100);

    // 보정 정보 표시
    const adj  = data.adjustment || {};
    const sign  = adj.total_home_adj >= 0 ? '+' : '';
    const color = adj.total_home_adj >= 0 ? '#00ff88' : '#ff7777';
    const formBonus = adj.formation_bonus || 0;
    const formText = formBonus > 0
        ? `${homeForm} → ${awayForm} 상성: 홈팀 유리 (참고용)`
        : formBonus < 0
        ? `${homeForm} → ${awayForm} 상성: 원정팀 유리 (참고용)`
        : '포메이션 상성: 중립';

    document.getElementById('lineup-adj').style.display = 'block';
    document.getElementById('lineup-adj').innerHTML = `
        <h4 style="margin-bottom:10px;color:#4aff4a;">📊 라인업 보정 결과</h4>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;font-size:0.85em;">
            <div style="text-align:center;">
                <div style="color:#aaa;margin-bottom:3px;">라인업 강도 보정</div>
                <div style="color:${color};font-weight:bold;font-size:1.1em;">${sign}${adj.home_boost || 0}%p</div>
            </div>
            <div style="text-align:center;">
                <div style="color:#aaa;margin-bottom:3px;">총 보정값</div>
                <div style="color:${color};font-weight:bold;font-size:1.3em;">${sign}${adj.total_home_adj || 0}%p</div>
            </div>
            <div style="text-align:center;">
                <div style="color:#aaa;margin-bottom:3px;">공격/수비 보정</div>
                <div style="color:${color};font-weight:bold;font-size:1.1em;">${sign}${adj.att_bonus || 0}%p</div>
            </div>
        </div>
        <div style="margin-top:10px;padding:8px;background:#0d0d0d;border-radius:6px;font-size:0.8em;color:#888;">
            ⚠️ ${formText}
        </div>`;

    document.getElementById('result-box').style.display = 'block';
}
// ================================
// 베팅픽 최적조합 - main.js 맨 아래에 추가
// ================================

let currentRound  = null;
let currentFolder = 5;
let currentUvi    = 100;

function selectRound(round, btn) {
    currentRound = round;
    loadBettingCombo();
}

function setFolder(n, btn) {
    currentFolder = n;
    document.querySelectorAll('.folder-btn').forEach(b => {
        b.style.background = '#2d2d4e';
        b.style.color = '#fff';
    });
    btn.style.background = '#4a4aff';
    if (currentRound) loadBettingCombo();
}

function setUvi(limit, btn) {
    currentUvi = limit;
    document.querySelectorAll('.uvi-btn').forEach(b => {
        b.style.background = '#2d2d4e';
        b.style.color = '#fff';
        b.style.borderColor = '#4aff4a';
    });
    btn.style.background = '#4aff4a';
    btn.style.color = '#000';
    if (currentRound) loadBettingCombo();
}

async function loadBettingCombo() {
    if (!currentRound) return;

    document.getElementById('betting-result').innerHTML =
        `<div class="loading"><div class="spinner"></div>
         <p>${currentRound}라운드 ${currentFolder}폴더 최적 조합 계산 중...</p></div>`;

    const url = `/api/best_combo/${currentRound}?n=${currentFolder}&uvi_limit=${currentUvi}&min_conf=0`;
    const res  = await fetch(url);
    const data = await res.json();

    if (data.error) {
        document.getElementById('betting-result').innerHTML =
            `<div class="card" style="text-align:center;color:#ff7777;">
                <p style="font-size:1.1em;margin-bottom:8px;">⚠️ ${data.error}</p>
                <p style="color:#aaa;font-size:0.85em;">UVI 상한을 높이거나 폴더 수를 줄여보세요</p>
             </div>`;
        return;
    }

    const medals = ['🥇','🥈','🥉','4위','5위'];
    let html = `
    <div style="margin-bottom:12px;padding:10px 15px;background:#0d0d2e;border-radius:8px;
                display:flex;align-items:center;gap:15px;flex-wrap:wrap;font-size:0.85em;">
        <span style="color:#aaa;">📊 ${currentRound}라운드 · ${currentFolder}폴더 · UVI ${currentUvi === 100 ? '전체' : currentUvi+'% 이하'}</span>
        <span style="color:#4aff4a;">C(24,${currentFolder}) = ${combo(24,currentFolder).toLocaleString()}가지 중 TOP5</span>
    </div>`;

    data.forEach((item, idx) => {
        const prob  = item.combo_prob;
        const color = prob >= 30 ? '#00ff88' : prob >= 20 ? '#ffbb44' : '#ff7777';
        const grade = prob >= 30 ? '✅ 안정' : prob >= 20 ? '⚠️ 보통' : '❌ 위험';

        html += `
        <div class="card" style="margin-bottom:15px;border:1px solid ${color}33;">

            <!-- 조합 헤더 -->
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;flex-wrap:wrap;gap:10px;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1.4em;">${medals[idx]}</span>
                    <div>
                        <div style="font-size:0.85em;color:#aaa;">${currentFolder}폴더 조합 ${idx+1}위</div>
                        <div style="font-size:0.8em;color:#555;margin-top:2px;">경기 모두 적중 시</div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:2em;font-weight:bold;color:${color};">${prob}%</div>
                    <div style="font-size:0.8em;color:${color};">${grade}</div>
                </div>
            </div>

            <!-- 확률 바 -->
            <div style="background:#1a1a3e;border-radius:6px;height:8px;margin-bottom:15px;overflow:hidden;">
                <div style="width:${Math.min(prob*2,100)}%;height:100%;
                            background:linear-gradient(90deg,${color},${color}88);border-radius:6px;"></div>
            </div>

            <!-- 경기 리스트 -->
            ${item.matches.map((m, mi) => `
            <div style="display:flex;align-items:center;gap:12px;padding:10px;
                        background:#0d0d2e;border-radius:8px;margin-bottom:8px;flex-wrap:wrap;">
                <span style="color:#4a4aff;font-weight:bold;min-width:20px;">${mi+1}</span>
                <div style="flex:1;min-width:150px;">
                    <div style="font-size:0.9em;font-weight:bold;">
                        ${m.home} <span style="color:#555;">vs</span> ${m.away}
                    </div>
                    <div style="color:#aaa;font-size:0.75em;margin-top:2px;">${m.group}조 · ${m.date}</div>
                </div>
                <div style="background:#1a1a3e;border-radius:6px;padding:5px 12px;text-align:center;">
                    <div style="font-size:0.75em;color:#aaa;margin-bottom:2px;">추천</div>
                    <div style="font-weight:bold;font-size:0.9em;color:#fff;">${m.pick_label}</div>
                </div>
                <div style="text-align:center;min-width:55px;">
                    <div style="font-size:0.7em;color:#aaa;">신뢰도</div>
                    <div style="font-weight:bold;color:${m.confidence>=65?'#00ff88':m.confidence>=55?'#ffbb44':'#aaa'};">
                        ${m.confidence}%
                    </div>
                </div>
                <div style="text-align:center;min-width:55px;">
                    <div style="font-size:0.7em;color:#aaa;">이변지수</div>
                    <div style="font-weight:bold;color:${m.uvi>=50?'#ff4444':m.uvi>=35?'#ffbb44':'#00ff88'};">
                        ${m.uvi}%
                    </div>
                </div>
            </div>`).join('')}

        </div>`;
    });

    // 전체 경기 요약 (접기/펼치기)
    html += await getBettingPicksSummary(currentRound);

    document.getElementById('betting-result').innerHTML = html;
}

// 조합 수 계산 C(n,k)
function combo(n, k) {
    if (k > n) return 0;
    let r = 1;
    for (let i = 0; i < k; i++) r = r * (n - i) / (i + 1);
    return Math.round(r);
}

// 전체 경기 리스트 (참고용)
async function getBettingPicksSummary(round) {
    const res  = await fetch(`/api/betting_picks/${round}`);
    const data = await res.json();

    const rec   = data.filter(m => m.recommended);
    const risky = data.filter(m => !m.recommended && m.uvi >= 35);

    let html = `
    <div class="card" style="border:1px solid #333;margin-top:10px;">
        <h3 style="margin-bottom:15px;color:#aaa;font-size:1em;">📋 전체 경기 요약</h3>`;

    if (rec.length > 0) {
        html += `<div style="margin-bottom:12px;">
            <div style="color:#4aff4a;font-size:0.85em;margin-bottom:8px;">⭐ 추천 (${rec.length}경기)</div>`;
        rec.forEach(m => {
            html += `<div style="display:flex;justify-content:space-between;padding:6px 0;
                                 border-bottom:1px solid #1a1a3e;font-size:0.85em;">
                <span>${m.home} vs ${m.away}</span>
                <span style="color:#4aff4a;font-weight:bold;">${m.pick_label} ${m.confidence}%</span>
            </div>`;
        });
        html += '</div>';
    }

    if (risky.length > 0) {
        html += `<div>
            <div style="color:#ff7777;font-size:0.85em;margin-bottom:8px;">⚡ 이변주의 (${risky.length}경기)</div>`;
        risky.forEach(m => {
            html += `<div style="display:flex;justify-content:space-between;padding:6px 0;
                                 border-bottom:1px solid #1a1a3e;font-size:0.85em;color:#aaa;">
                <span>${m.home} vs ${m.away}</span>
                <span>UVI ${m.uvi}%</span>
            </div>`;
        });
        html += '</div>';
    }

    html += '</div>';
    return html;
}