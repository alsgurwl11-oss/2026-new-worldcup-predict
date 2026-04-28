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