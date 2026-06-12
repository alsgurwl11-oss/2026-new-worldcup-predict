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
// 배당 표시 헬퍼 (1번 요구사항)
// odds = {home, draw, away} 또는 null
// --------------------------------
function renderOddsRow(odds, homeName, awayName) {
    if (!odds) return '';
    return `
        <div style="display:flex;justify-content:center;gap:12px;margin-top:8px;font-size:0.78em;color:#aaa;">
            <span style="background:#1a1a3e;border-radius:4px;padding:2px 8px;">
                ${homeName} <strong style="color:#fff;">${odds.home}</strong>
            </span>
            <span style="background:#1a1a3e;border-radius:4px;padding:2px 8px;">
                무 <strong style="color:#ffbb44;">${odds.draw}</strong>
            </span>
            <span style="background:#1a1a3e;border-radius:4px;padding:2px 8px;">
                ${awayName} <strong style="color:#fff;">${odds.away}</strong>
            </span>
        </div>`;
}

// 저배당 뱃지 (3번 요구사항)
function renderLowOddsBadge(isLowOdds, overUnder) {
    if (!isLowOdds) return '';
    const ou = overUnder ? `${overUnder.pick} ${overUnder.line} (${overUnder.prob}%)` : 'O/U 분석 권장';
    return `
        <div style="text-align:center;margin-top:6px;">
            <span style="background:#ff9900;color:#000;border-radius:4px;
                         padding:3px 8px;font-size:0.75em;font-weight:bold;">
                ⚠️ 초저배당 — ${ou}
            </span>
        </div>`;
}

// --------------------------------
// 2번: 배당 계산기 전역 상태
// --------------------------------
let calcSelections = {}; // { 'home_vs_away': { label, odds } }

function toggleCalcPick(key, label, oddsVal, btn) {
    if (calcSelections[key]) {
        delete calcSelections[key];
        btn.style.background = '#1a1a3e';
        btn.style.borderColor = '#333';
    } else {
        calcSelections[key] = { label, odds: oddsVal };
        btn.style.background = '#4a4aff';
        btn.style.borderColor = '#7a7aff';
    }
    updateOddsCalculator();
    addToCart(key, label, oddsVal);
}

function updateOddsCalculator() {
    const keys = Object.keys(calcSelections);
    const box  = document.getElementById('odds-calc-box');
    if (!box) return;

    if (keys.length === 0) {
        box.innerHTML = `<div style="color:#555;font-size:0.85em;text-align:center;padding:10px;">경기를 선택하면 배당이 계산됩니다</div>`;
        return;
    }

    let totalOdds = 1;
    let html = '<div style="font-size:0.82em;margin-bottom:8px;">';
    keys.forEach(k => {
        const s = calcSelections[k];
        totalOdds *= s.odds;
        html += `<div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #1a1a3e;">
            <span style="color:#aaa;">${k}</span>
            <span style="color:#fff;">${s.label} <strong style="color:#4aff4a;">x${s.odds}</strong></span>
        </div>`;
    });
    html += '</div>';

    const color = totalOdds >= 3 ? '#00ff88' : totalOdds >= 2 ? '#ffbb44' : '#aaa';
    html += `
        <div style="background:#0d0d0d;border-radius:6px;padding:10px;text-align:center;margin-top:6px;">
            <div style="color:#aaa;font-size:0.75em;margin-bottom:4px;">${keys.length}폴더 예상 배당</div>
            <div style="font-size:1.8em;font-weight:bold;color:${color};">x${totalOdds.toFixed(2)}</div>
            <div style="color:#555;font-size:0.75em;margin-top:4px;">
                10,000원 베팅 시 → <strong style="color:${color};">${Math.round(totalOdds * 10000).toLocaleString()}원</strong>
            </div>
        </div>
        <button onclick="clearCalc()" style="width:100%;margin-top:8px;padding:6px;
            background:#2a2a4e;border:none;border-radius:6px;color:#aaa;cursor:pointer;font-size:0.8em;">
            선택 초기화
        </button>`;

    box.innerHTML = html;
}

function clearCalc() {
    calcSelections = {};
    document.querySelectorAll('.odds-pick-btn').forEach(b => {
        b.style.background = '#1a1a3e';
        b.style.borderColor = '#333';
    });
    updateOddsCalculator();
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

    const oddsArea = document.getElementById('predict-odds-area');
    if (oddsArea) {
        if (data.odds) {
            oddsArea.innerHTML = renderOddsRow(data.odds, data.home, data.away);
        } else {
            oddsArea.innerHTML = '';
        }
    }

    const lowBadge = document.getElementById('predict-low-odds-badge');
    if (lowBadge) {
        lowBadge.innerHTML = renderLowOddsBadge(data.is_low_odds, data.over_under);
    }

    document.getElementById('result-box').style.display = 'block';
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

    let html = `
        <h3 style="margin-bottom:15px;">${group}조 경기별 예측</h3>
        <div style="background:#0d0d2e;border:1px solid #4a4aff;border-radius:10px;padding:14px;margin-bottom:18px;">
            <div style="font-size:0.85em;color:#4aff4a;font-weight:bold;margin-bottom:8px;">🧮 배당 계산기 — 클릭해서 경기 선택</div>
            <div id="odds-calc-box">
                <div style="color:#555;font-size:0.85em;text-align:center;padding:10px;">경기를 선택하면 배당이 계산됩니다</div>
            </div>
        </div>`;

    data.matches.forEach((match, idx) => {
        const homeClass = match.home_win >= match.away_win ? 'prob-high' : 'prob-low';
        const awayClass = match.away_win > match.home_win  ? 'prob-high' : 'prob-low';
        const odds      = match.odds;
        const matchKey  = `${match.home} vs ${match.away}`;

        let oddsPickHtml = '';
        if (odds) {
            oddsPickHtml = `
                <div style="display:flex;justify-content:center;gap:8px;margin-top:10px;flex-wrap:wrap;">
                    <button class="odds-pick-btn"
                        onclick="toggleCalcPick('${matchKey}','${match.home} 승(x${odds.home})',${odds.home},this)"
                        style="padding:4px 10px;background:#1a1a3e;border:1px solid #333;
                               border-radius:6px;color:#fff;cursor:pointer;font-size:0.78em;">
                        ${match.home} 승 <strong>x${odds.home}</strong>
                    </button>
                    <button class="odds-pick-btn"
                        onclick="toggleCalcPick('${matchKey}','무승부(x${odds.draw})',${odds.draw},this)"
                        style="padding:4px 10px;background:#1a1a3e;border:1px solid #333;
                               border-radius:6px;color:#ffbb44;cursor:pointer;font-size:0.78em;">
                        무 <strong>x${odds.draw}</strong>
                    </button>
                    <button class="odds-pick-btn"
                        onclick="toggleCalcPick('${matchKey}','${match.away} 승(x${odds.away})',${odds.away},this)"
                        style="padding:4px 10px;background:#1a1a3e;border:1px solid #333;
                               border-radius:6px;color:#fff;cursor:pointer;font-size:0.78em;">
                        ${match.away} 승 <strong>x${odds.away}</strong>
                    </button>
                </div>`;
        }

        html += `
            <div style="background:#0d0d2e; border-radius:12px; padding:20px; margin-bottom:15px;
                        border:1px solid ${match.is_low_odds ? '#ff9900' : '#333'};">
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
                ${renderOddsRow(odds, match.home, match.away)}
                ${renderLowOddsBadge(match.is_low_odds, null)}
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; text-align:center; margin-top:12px;">
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
                ${oddsPickHtml}
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
// ⑤ 토너먼트 브라켓
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
// 라인업 UI
// ================================

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

let currentLineup = { home: null, away: null };

async function loadLineupAfterPredict(home, away) {
    document.getElementById('lineup-section').style.display = 'block';
    document.getElementById('lu-home-name').textContent = home;
    document.getElementById('lu-away-name').textContent = away;
    document.getElementById('lineup-adj').style.display = 'none';

    const homeFormSel = document.getElementById('lu-home-form');
    const awayFormSel = document.getElementById('lu-away-form');

    const [homeRes, awayRes] = await Promise.all([
        fetch(`/api/lineup/${encodeURIComponent(home)}`),
        fetch(`/api/lineup/${encodeURIComponent(away)}`),
    ]);
    currentLineup.home = await homeRes.json();
    currentLineup.away = await awayRes.json();

    homeFormSel.value = currentLineup.home.formation || '4-2-3-1';
    awayFormSel.value = currentLineup.away.formation || '4-2-3-1';

    renderPitch('home', currentLineup.home);
    renderPitch('away', currentLineup.away);
    renderStrength('home', currentLineup.home);
    renderStrength('away', currentLineup.away);
}

function renderPitch(side, lineup) {
    const pitchEl = document.getElementById(`pitch-${side}`);
    const formation = lineup.formation || '4-2-3-1';
    const positions = FORMATION_POS[formation] || FORMATION_POS['4-2-3-1'];
    const players   = lineup.players || [];

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

    setTimeout(() => {
        document.getElementById('bar-home').style.width = data.home_win + '%';
        document.getElementById('bar-home').textContent = data.home_win + '%';
        document.getElementById('bar-draw').style.width = data.draw + '%';
        document.getElementById('bar-draw').textContent = data.draw + '%';
        document.getElementById('bar-away').style.width = data.away_win + '%';
        document.getElementById('bar-away').textContent = data.away_win + '%';
    }, 100);

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
// 베팅픽 최적조합
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
        <span style="color:#ff9900;font-size:0.8em;">💡 신뢰도×배당가치 기준 정렬 | ⇄ = 언오버 전환픽</span>
    </div>`;

    data.forEach((item, idx) => {
        const prob  = item.combo_prob;
        const color = prob >= 30 ? '#00ff88' : prob >= 20 ? '#ffbb44' : '#ff7777';
        const grade = prob >= 30 ? '✅ 안정' : prob >= 20 ? '⚠️ 보통' : '❌ 위험';

        html += `
        <div class="card" style="margin-bottom:15px;border:1px solid ${color}33;">
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
            <div style="background:#1a1a3e;border-radius:6px;height:8px;margin-bottom:15px;overflow:hidden;">
                <div style="width:${Math.min(prob*2,100)}%;height:100%;
                            background:linear-gradient(90deg,${color},${color}88);border-radius:6px;"></div>
            </div>
            ${item.matches.map((m, mi) => {
                const borderColor = m.is_low_odds ? '#ff9900' : '#1a1a3e';
                const oddsHtml = m.odds
                    ? `<div style="font-size:0.7em;color:#aaa;margin-top:3px;">
                           배당 <span style="color:#fff;">x${m.odds.home || '-'}</span> /
                           <span style="color:#ffbb44;">무 x${m.odds.draw || '-'}</span> /
                           <span style="color:#fff;">x${m.odds.away || '-'}</span>
                       </div>`
                    : '';
                return `
            <div style="display:flex;align-items:center;gap:12px;padding:10px;
                        background:#0d0d2e;border-radius:8px;margin-bottom:8px;
                        border:1px solid ${borderColor};flex-wrap:wrap;">
                <span style="color:#4a4aff;font-weight:bold;min-width:20px;">${mi+1}</span>
                <div style="flex:1;min-width:150px;">
                    <div style="font-size:0.9em;font-weight:bold;">
                        ${m.home} <span style="color:#555;">vs</span> ${m.away}
                    </div>
                    <div style="color:#aaa;font-size:0.75em;margin-top:2px;">${m.group}조 · ${m.date}</div>
                    ${oddsHtml}
                    ${m.is_low_odds ? '<div style="font-size:0.7em;color:#ff9900;margin-top:2px;">⚠️ 초저배당</div>' : ''}
                </div>
                <div style="background:#1a1a3e;border-radius:6px;padding:5px 12px;text-align:center;">
                    <div style="font-size:0.75em;color:#aaa;margin-bottom:2px;">
                        ${m.auto_switched ? '<span style="color:#ff9900;">⇄ 언오버</span>' : '추천'}
                    </div>
                    <div style="font-weight:bold;font-size:0.9em;color:${m.auto_switched ? '#ff9900' : '#fff'};">
                        ${m.pick_label}
                    </div>
                    ${m.edge > 0 && !m.auto_switched ? `<div style="font-size:0.65em;color:#4aff4a;margin-top:2px;">+${m.edge}% 엣지</div>` : ''}
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
            </div>`}).join('')}
        </div>`;
    });

    document.getElementById('betting-result').innerHTML = html;

    // 픽 요약을 맨 위에 추가
    const summaryHtml = await getBettingPicksSummary(currentRound);
    document.getElementById('betting-result').insertAdjacentHTML('afterbegin', summaryHtml);
}

function combo(n, k) {
    if (k > n) return 0;
    let r = 1;
    for (let i = 0; i < k; i++) r = r * (n - i) / (i + 1);
    return Math.round(r);
}

// ================================
// 픽 배당값 계산 헬퍼
// ================================
function getPickOdds(m) {
    // 언오버 픽 → OU 배당 사용
    if (m.auto_switched && m.ou_data && m.ou_data.ou_odds) {
        const rec = m.ou_data.recommendation;
        return rec === 'OVER'
            ? m.ou_data.ou_odds.over
            : m.ou_data.ou_odds.under;
    }
    // 언오버인데 배당 없으면 신뢰도 역산
    if (m.auto_switched) {
        return parseFloat((m.confidence / 100 + 1).toFixed(2));
    }
    // 1x2 픽 → 해당 배당
    if (m.odds) {
        if (m.best_outcome === 'home_win') return m.odds.home;
        if (m.best_outcome === 'away_win') return m.odds.away;
        return m.odds.draw;
    }
    // 배당 없으면 폴백
    return parseFloat((m.confidence / 100 + 1).toFixed(2));
}

async function getBettingPicksSummary(round) {
    const res  = await fetch(`/api/betting_picks/${round}`);
    const data = await res.json();

    // 날짜순 정렬
    const byDate = [...data].sort((a, b) => a.date.localeCompare(b.date));

    let html = `
    <div class="card" style="border:1px solid #4a4aff33;margin-top:15px;">
        <h3 style="margin-bottom:15px;font-size:1em;">
            📋 ${round}라운드 전체 경기 픽
            <span style="color:#aaa;font-size:0.8em;font-weight:normal;margin-left:8px;">
                추천 ${data.filter(m=>m.recommended).length}경기 / 전체 ${data.length}경기
            </span>
        </h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th style="width:30px;">조</th>
                    <th>경기</th>
                    <th>날짜</th>
                    <th style="text-align:center;">홈승</th>
                    <th style="text-align:center;">무</th>
                    <th style="text-align:center;">원정승</th>
                    <th style="text-align:center;">최종 픽</th>
                    <th style="text-align:center;">신뢰도</th>
                    <th style="text-align:center;">이변</th>
                    <th style="text-align:center;">🛒</th>
                </tr>
            </thead>
            <tbody>`;

    byDate.forEach(m => {
        const pickColor = m.recommended ? '#00ff88' : '#aaa';
        const recBadge  = m.recommended
            ? '<span style="color:#00ff88;font-size:0.8em;">✅</span>'
            : '<span style="color:#555;font-size:0.8em;">-</span>';

        const ouBadge = m.auto_switched
            ? `<span style="background:#ff9900;color:#000;border-radius:3px;
                           padding:1px 4px;font-size:0.7em;margin-right:3px;">⇄</span>`
            : '';

        const maxProb = Math.max(m.home_win, m.draw, m.away_win);
        const hStyle  = m.home_win === maxProb ? 'color:#fff;font-weight:bold;' : 'color:#555;';
        const dStyle  = m.draw     === maxProb ? 'color:#ffbb44;font-weight:bold;' : 'color:#555;';
        const aStyle  = m.away_win === maxProb ? 'color:#fff;font-weight:bold;' : 'color:#555;';

        const uviColor = m.uvi >= 50 ? '#ff4444' : m.uvi >= 35 ? '#ffbb44' : '#00ff88';

        // 픽 배당값 계산
        const pickOdds = getPickOdds(m);
        const matchKey = `${m.home} vs ${m.away}`;
        // 픽 라벨에 배당 표시
        const pickLabelWithOdds = pickOdds
            ? `${m.pick_label} <span style="color:#4aff4a;font-size:0.8em;">x${pickOdds}</span>`
            : m.pick_label;

        html += `
            <tr style="border-bottom:1px solid #1a1a2e;cursor:pointer;"
                onclick="addToCart('${matchKey.replace(/'/g,"\\'")}', '${m.pick_label.replace(/'/g,"\\'")}', ${pickOdds})">
                <td style="color:#aaa;font-size:0.85em;">${m.group}</td>
                <td>
                    <span style="font-weight:bold;">${m.home}</span>
                    <span style="color:#555;font-size:0.8em;"> vs </span>
                    <span style="font-weight:bold;">${m.away}</span>
                </td>
                <td style="color:#aaa;font-size:0.8em;white-space:nowrap;">${m.date}</td>
                <td style="text-align:center;${hStyle}">${m.home_win}%</td>
                <td style="text-align:center;${dStyle}">${m.draw}%</td>
                <td style="text-align:center;${aStyle}">${m.away_win}%</td>
                <td style="text-align:center;">
                    ${ouBadge}
                    <span style="color:${pickColor};font-weight:bold;font-size:0.9em;">${m.pick_label}</span>
                    <span style="margin-left:4px;">${recBadge}</span>
                </td>
                <td style="text-align:center;">
                    <span style="color:${m.confidence>=65?'#00ff88':m.confidence>=55?'#ffbb44':'#aaa'};font-weight:bold;">
                        ${m.confidence}%
                    </span>
                </td>
                <td style="text-align:center;">
                    <span style="color:${uviColor};font-weight:bold;font-size:0.85em;">${m.uvi}%</span>
                </td>
                <td style="text-align:center;">
                    <span style="color:#4aff4a;font-size:0.85em;font-weight:bold;">
                        ${pickOdds ? 'x'+pickOdds : '+'}
                    </span>
                </td>
            </tr>`;
    });

    html += `
            </tbody>
        </table>
        <div style="margin-top:10px;display:flex;gap:16px;font-size:0.75em;color:#555;flex-wrap:wrap;">
            <span>✅ = 추천픽 (신뢰도 55%+, 이변 35% 미만)</span>
            <span>⇄ = 언오버 자동전환</span>
            <span style="color:#4aff4a;">행 클릭 → 🛒 카트 추가</span>
        </div>
    </div>`;

    return html;
}

// ================================
// 🛒 플로팅 베팅 카트
// ================================

let cartItems = {};
let cartOpen  = true;

function toggleCart() {
    cartOpen = !cartOpen;
    document.getElementById('cart-body').style.display = cartOpen ? 'block' : 'none';
    document.getElementById('cart-toggle-icon').textContent = cartOpen ? '▲' : '▼';
}

function addToCart(matchKey, label, odds) {
    // 같은 경기 다시 누르면 제거 (토글)
    if (cartItems[matchKey]) {
        removeFromCart(matchKey);
        return;
    }
    cartItems[matchKey] = { label, odds: parseFloat(odds) };
    renderCart();

    // 카트 닫혀있으면 자동으로 열기
    if (!cartOpen) toggleCart();
}

function removeFromCart(matchKey) {
    delete cartItems[matchKey];
    renderCart();
}

function clearCart() {
    cartItems = {};
    renderCart();
}

function renderCart() {
    const keys  = Object.keys(cartItems);
    const count = keys.length;

    document.getElementById('cart-count').textContent = count;
    document.getElementById('cart-count').style.background = count > 0 ? '#4a4aff' : '#333';

    const itemsEl = document.getElementById('cart-items');
    const totalEl = document.getElementById('cart-total');

    if (count === 0) {
        itemsEl.innerHTML = `
            <div style="color:#555;text-align:center;padding:15px;font-size:0.85em;">
                경기 픽을 추가하세요 🎯
            </div>`;
        totalEl.style.display = 'none';
        return;
    }

    let totalOdds = 1;
    let html = '';
    keys.forEach(key => {
        const item = cartItems[key];
        totalOdds *= item.odds;
        html += `
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:6px 0;border-bottom:1px solid #1a1a3e;gap:8px;">
            <div style="flex:1;min-width:0;">
                <div style="font-size:0.78em;color:#aaa;overflow:hidden;
                            text-overflow:ellipsis;white-space:nowrap;">${key}</div>
                <div style="font-size:0.85em;color:#fff;font-weight:bold;">${item.label}</div>
            </div>
            <div style="display:flex;align-items:center;gap:6px;flex-shrink:0;">
                <span style="color:#4aff4a;font-weight:bold;">x${item.odds}</span>
                <button onclick="removeFromCart('${key.replace(/'/g, "\\'")}')"
                    style="background:none;border:none;color:#555;cursor:pointer;
                           font-size:1em;padding:0;line-height:1;">✕</button>
            </div>
        </div>`;
    });
    itemsEl.innerHTML = html;

    totalEl.style.display = 'block';
    const color = totalOdds >= 3 ? '#00ff88' : totalOdds >= 2 ? '#ffbb44' : '#aaa';
    document.getElementById('cart-total-odds').textContent = `x${totalOdds.toFixed(2)}`;
    document.getElementById('cart-total-odds').style.color = color;
    document.getElementById('cart-total-payout').textContent =
        `10,000원 → ${Math.round(totalOdds * 10000).toLocaleString()}원`;
    document.getElementById('cart-total-payout').style.color = color;
}