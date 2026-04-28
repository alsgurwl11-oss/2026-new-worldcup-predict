// ================================
// advanced.js - 고급 분석 함수
// ================================

async function loadKoreaScenario() {
    document.getElementById('korea-result').innerHTML = `
        <div class="loading"><div class="spinner"></div><p>한국 시나리오 분석 중...</p></div>`;
    const res  = await fetch('/api/korea_scenario');
    const data = await res.json();
    const r    = data.rounds;
    let html = `
        <div class="card" style="margin-bottom:20px;">
            <h3 style="margin-bottom:15px;">🇰🇷 한국 라운드별 진출 확률</h3>
            <table class="data-table">
                <thead><tr><th>조별 탈락</th><th>32강</th><th>16강</th><th>8강</th><th>4강</th><th>결승</th><th>🏆 우승</th></tr></thead>
                <tbody><tr>
                    <td class="prob-low">${r.group_exit}%</td>
                    <td class="${probClass(r.r32)}">${r.r32}%</td>
                    <td class="${probClass(r.r16)}">${r.r16}%</td>
                    <td class="${probClass(r.qf)}">${r.qf}%</td>
                    <td class="${probClass(r.sf)}">${r.sf}%</td>
                    <td class="${probClass(r.final)}">${r.final}%</td>
                    <td class="${probClass(r.champion)}">${r.champion}%</td>
                </tr></tbody>
            </table>
        </div>
        <div class="card">
            <h3 style="margin-bottom:15px;">⚔️ 한국 예상 상대 TOP 8</h3>
            <table class="data-table">
                <thead><tr><th>#</th><th>상대팀</th><th>만날 확률</th></tr></thead><tbody>`;
    data.likely_opponents.forEach((opp, idx) => {
        html += `<tr>
            <td class="rank-num">${idx+1}</td>
            <td><strong>${opp.team}</strong></td>
            <td><span class="${probClass(opp.prob)}">${opp.prob}%</span>
                <div class="qualify-bar"><div class="qualify-fill" style="width:${opp.prob}%"></div></div></td>
        </tr>`;
    });
    html += '</tbody></table></div>';
    document.getElementById('korea-result').innerHTML = html;
}

async function loadUpsetAnalysis() {
    document.getElementById('upset-result').innerHTML = `
        <div class="loading"><div class="spinner"></div><p>이변 경보 분석 중...</p></div>`;
    const res  = await fetch('/api/upset_analysis');
    const data = await res.json();
    const factorNames = {
        'xg_gap':'xG 박빙','shooting':'슈팅 효율','tactical':'전술 상성',
        'round':'라운드 특성','desperation':'절박도','strength_gap':'전력 차이',
        'injury':'부상 취약도','key_man':'원맨팀',
    };
    let html = `
        <div style="margin-bottom:20px;padding:15px;background:#1a1a2e;border-radius:10px;">
            <h3 style="margin-bottom:10px;">📊 이변 지수(UVI) 설명</h3>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;font-size:0.85em;">
                <div style="background:#0d2d0d;padding:10px;border-radius:8px;text-align:center;"><div style="color:#00ff88;font-weight:bold;">✅ 신뢰도 높음</div><div style="color:#aaa;">UVI 0~20%</div></div>
                <div style="background:#2d2d0d;padding:10px;border-radius:8px;text-align:center;"><div style="color:#ffbb44;font-weight:bold;">🟡 이변 가능</div><div style="color:#aaa;">UVI 20~35%</div></div>
                <div style="background:#2d0d0d;padding:10px;border-radius:8px;text-align:center;"><div style="color:#ff7777;font-weight:bold;">🔴 이변 주의</div><div style="color:#aaa;">UVI 35~50%</div></div>
                <div style="background:#1a0000;padding:10px;border-radius:8px;text-align:center;"><div style="color:#ff0000;font-weight:bold;">⚡ 이변 경보</div><div style="color:#aaa;">UVI 50%+</div></div>
            </div>
        </div>
        <table class="data-table">
            <thead><tr><th>#</th><th>조</th><th>경기</th><th>우세팀</th><th>열세팀</th><th>강팀 승률</th><th>⚡ 이변 지수</th><th>신뢰도</th><th>주요 요인</th></tr></thead>
            <tbody>`;
    data.forEach((match, idx) => {
        const conf = match.confidence;
        const topFactor = Object.entries(match.factors).sort((a,b)=>b[1]-a[1]).slice(0,2)
            .map(([k,v])=>`${factorNames[k]}(${(v*100).toFixed(0)}%)`).join(', ');
        html += `<tr>
            <td class="rank-num">${idx+1}</td>
            <td style="color:#aaa">${match.group}조</td>
            <td style="font-size:0.85em">${match.home} vs ${match.away}</td>
            <td><strong>${match.favorite}</strong><div style="color:#aaa;font-size:0.8em">FIFA ${match.fav_rank}위</div></td>
            <td><strong>${match.underdog}</strong><div style="color:#aaa;font-size:0.8em">FIFA ${match.und_rank}위</div></td>
            <td><span class="${match.fav_win>=60?'prob-high':match.fav_win>=45?'prob-mid':'prob-low'}">${match.fav_win}%</span></td>
            <td><strong style="color:${conf.color};font-size:1.1em">${(match.uvi*100).toFixed(1)}%</strong>
                <div class="qualify-bar" style="margin-top:4px;"><div class="qualify-fill" style="width:${match.uvi*100}%;background:${conf.color}"></div></div></td>
            <td><span style="color:${conf.color};font-weight:bold;font-size:0.85em">${conf.label}</span></td>
            <td style="font-size:0.8em;color:#aaa">${topFactor}</td>
        </tr>`;
    });
    html += '</tbody></table>';
    document.getElementById('upset-result').innerHTML = html;
}

async function predictScoreline() {
    const home  = document.getElementById('sc-home').value;
    const away  = document.getElementById('sc-away').value;
    const round = document.getElementById('sc-round').value;
    if (!home || !away) { alert('팀을 선택해주세요!'); return; }
    if (home === away)  { alert('서로 다른 팀을 선택해주세요!'); return; }
    document.getElementById('scoreline-result').innerHTML =
        `<div class="loading"><div class="spinner"></div><p>스코어 계산 중...</p></div>`;
    const res  = await fetch('/api/scoreline', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({home, away, round})
    });
    const data = await res.json();
    let html = `<div class="card">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:20px;text-align:center;">
            <div style="background:#0d0d2e;border-radius:10px;padding:15px;">
                <div style="font-size:1.1em;font-weight:bold;margin-bottom:5px;">${data.home}</div>
                <div style="color:#4a4aff;font-size:1.5em;font-weight:bold;">xG ${data.home_xg}</div>
            </div>
            <div style="background:#0d0d2e;border-radius:10px;padding:15px;">
                <div style="font-size:1.1em;font-weight:bold;margin-bottom:5px;">${data.away}</div>
                <div style="color:#ff4444;font-size:1.5em;font-weight:bold;">xG ${data.away_xg}</div>
            </div>
        </div>
        <h3 style="margin-bottom:12px;">📊 예상 스코어 TOP 5</h3>`;
    data.top5.forEach((s,idx) => {
        const bw = Math.min(s.prob*4,100);
        html += `<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span style="width:20px;color:#aaa;font-size:0.85em;">${idx+1}위</span>
            <span style="width:50px;font-size:1.1em;font-weight:bold;color:#fff;">${s.score}</span>
            <div style="flex:1;background:#2a2a4e;border-radius:4px;height:20px;">
                <div style="width:${bw}%;height:100%;background:linear-gradient(90deg,#4a4aff,#7a4aff);border-radius:4px;display:flex;align-items:center;padding-left:8px;">
                    <span style="font-size:0.8em;font-weight:bold;">${s.prob}%</span>
                </div>
            </div>
        </div>`;
    });
    html += `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:20px;">
        <div style="background:#1a1a3e;border-radius:8px;padding:10px;text-align:center;"><div style="color:#aaa;font-size:0.75em;margin-bottom:4px;">BTTS</div><div style="font-size:1.1em;font-weight:bold;color:#ffbb44;">${data.btts}%</div></div>
        <div style="background:#1a1a3e;border-radius:8px;padding:10px;text-align:center;"><div style="color:#aaa;font-size:0.75em;margin-bottom:4px;">오버 2.5</div><div style="font-size:1.1em;font-weight:bold;color:#00ff88;">${data.over_25}%</div></div>
        <div style="background:#1a1a3e;border-radius:8px;padding:10px;text-align:center;"><div style="color:#aaa;font-size:0.75em;margin-bottom:4px;">홈 무실점</div><div style="font-size:1.1em;font-weight:bold;">${data.clean_sheet_home}%</div></div>
        <div style="background:#1a1a3e;border-radius:8px;padding:10px;text-align:center;"><div style="color:#aaa;font-size:0.75em;margin-bottom:4px;">원정 무실점</div><div style="font-size:1.1em;font-weight:bold;">${data.clean_sheet_away}%</div></div>
    </div>
    <p style="color:#555;font-size:0.75em;margin-top:12px;text-align:center;">예상 총 득점: ${data.expected_total}골 | 포아송 분포 기반</p>
    </div>`;
    document.getElementById('scoreline-result').innerHTML = html;
}

async function loadGDI() {
    document.getElementById('gdi-result').innerHTML =
        `<div class="loading"><div class="spinner"></div><p>조 난이도 계산 중...</p></div>`;
    const res  = await fetch('/api/group_difficulty');
    const data = await res.json();
    let html = `<table class="data-table">
        <thead><tr><th>#</th><th>조</th><th>난이도</th><th>GDI 점수</th><th>평균 FIFA 포인트</th><th>최약체 강도</th><th>팀 균형도</th><th>팀 목록</th></tr></thead><tbody>`;
    data.forEach(g => {
        html += `<tr>
            <td class="rank-num">${g.difficulty_rank}</td>
            <td><strong>${g.group}조</strong></td>
            <td><span style="font-size:1.1em;">${g.difficulty_label}</span></td>
            <td><strong style="color:${g.gdi>=70?'#ff4444':g.gdi>=50?'#ffbb44':'#00ff88'}">${g.gdi}</strong>
                <div class="qualify-bar"><div class="qualify-fill" style="width:${Math.min(g.gdi,100)}%"></div></div></td>
            <td style="color:#aaa">${g.avg_fpoints}</td>
            <td style="color:#aaa">${g.min_fpoints}</td>
            <td style="color:#aaa">${g.balance}%</td>
            <td style="font-size:0.8em;color:#aaa">${g.team_details.map(t=>`${t.team}(${t.rank}위)`).join(', ')}</td>
        </tr>`;
    });
    html += '</tbody></table>';
    document.getElementById('gdi-result').innerHTML = html;
}

async function loadBacktest(year) {
    document.getElementById('backtest-result').innerHTML =
        `<div class="loading"><div class="spinner"></div><p>${year} 백테스트 실행 중...</p></div>`;
    const res  = await fetch(`/api/backtest/${year}`);
    const data = await res.json();
    if (data.error) {
        document.getElementById('backtest-result').innerHTML = `<p style="color:#ff4444;text-align:center;">${data.error}</p>`;
        return;
    }
    const am = {'home_win':'홈승','draw':'무승부','away_win':'원정승'};
    let html = `<div class="card" style="margin-bottom:20px;">
        <h3 style="margin-bottom:15px;">${data.tournament} 검증 결과</h3>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px;">
            <div class="info-card"><div class="label">전체 적중률</div><div class="value" style="font-size:1.4em;">${data.total_accuracy}%</div><div style="color:#aaa;font-size:0.8em;">${data.total_matches}경기</div></div>
            <div class="info-card"><div class="label">조별리그</div><div class="value">${data.group_accuracy}%</div></div>
            <div class="info-card"><div class="label">토너먼트</div><div class="value">${data.knockout_accuracy}%</div></div>
            <div class="info-card"><div class="label">고신뢰도(50%+)</div><div class="value" style="color:#00ff88;">${data.high_conf_accuracy}%</div><div style="color:#aaa;font-size:0.8em;">${data.high_conf_count}경기</div></div>
        </div>
        <div style="background:#0d0d2e;border-radius:10px;padding:15px;">
            <span>🏆 실제 우승: <strong>${data.champion_actual}</strong></span>
            &nbsp;&nbsp;<span>4강: ${data.top4_actual.join(' / ')}</span>
        </div>
    </div>
    <table class="data-table">
        <thead><tr><th>결과</th><th>홈팀</th><th>원정팀</th><th>라운드</th><th>실제</th><th>예측</th><th>신뢰도</th></tr></thead><tbody>`;
    data.match_details.forEach(m => {
        html += `<tr>
            <td style="font-size:1.1em;">${m.correct?'✅':'❌'}</td>
            <td>${m.home}</td><td>${m.away}</td>
            <td style="color:#aaa;font-size:0.85em;">${m.round}</td>
            <td><strong>${am[m.actual]}</strong></td>
            <td style="color:${m.correct?'#00ff88':'#ff7777'}">${am[m.predicted]}</td>
            <td style="color:#aaa">${m.confidence}%</td>
        </tr>`;
    });
    html += '</tbody></table>';
    document.getElementById('backtest-result').innerHTML = html;
}

let wiFixedResults = [];

async function loadWhatIfMatches() {
    const group = document.getElementById('wi-group').value;
    if (!group) return;
    const res  = await fetch('/api/group_difficulty');
    const data = await res.json();
    const gData = data.find(g => g.group === group);
    if (!gData) return;
    const teams = gData.teams;
    let matchHtml = '<div style="margin-bottom:15px;">';
    for (let i = 0; i < teams.length; i++) {
        for (let j = i+1; j < teams.length; j++) {
            const home = teams[i], away = teams[j];
            matchHtml += `<div style="background:#0d0d2e;border-radius:8px;padding:12px;margin-bottom:10px;">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
                    <span style="font-weight:bold;">${home}</span><span style="color:#aaa;font-size:0.85em;">vs</span><span style="font-weight:bold;">${away}</span>
                </div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;">
                    <button onclick="setWhatIfResult(this,'${home}','${away}','home_win')" style="padding:6px;background:#1a1a3e;border:1px solid #4a4aff;border-radius:6px;color:#fff;cursor:pointer;font-size:0.85em;">${home} 승</button>
                    <button onclick="setWhatIfResult(this,'${home}','${away}','draw')" style="padding:6px;background:#1a1a3e;border:1px solid #4a4aff;border-radius:6px;color:#fff;cursor:pointer;font-size:0.85em;">무승부</button>
                    <button onclick="setWhatIfResult(this,'${home}','${away}','away_win')" style="padding:6px;background:#1a1a3e;border:1px solid #4a4aff;border-radius:6px;color:#fff;cursor:pointer;font-size:0.85em;">${away} 승</button>
                </div>
            </div>`;
        }
    }
    matchHtml += '</div>';
    document.getElementById('wi-matches').innerHTML = matchHtml;
}

function setWhatIfResult(btn, home, away, result) {
    btn.parentElement.querySelectorAll('button').forEach(b => {
        b.style.background = '#1a1a3e'; b.style.borderColor = '#4a4aff';
    });
    btn.style.background = '#4a4aff'; btn.style.borderColor = '#7a7aff';
    wiFixedResults = wiFixedResults.filter(fr => !(fr.home===home && fr.away===away));
    wiFixedResults.push({home, away, result});
}

async function runWhatIf() {
    const group = document.getElementById('wi-group').value;
    if (!group) { alert('조를 선택해주세요!'); return; }
    document.getElementById('whatif-result').innerHTML =
        `<div class="loading"><div class="spinner"></div><p>시나리오 시뮬레이션 중...</p></div>`;
    const res  = await fetch('/api/what_if', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({group, fixed_results: wiFixedResults})
    });
    const data = await res.json();
    if (data.error) {
        document.getElementById('whatif-result').innerHTML = `<p style="color:#ff4444;">${data.error}</p>`;
        return;
    }
    const fixedDesc = wiFixedResults.length > 0
        ? wiFixedResults.map(fr => {
            const m = {'home_win':`${fr.home} 승`,'draw':'무승부','away_win':`${fr.away} 승`};
            return `${fr.home} vs ${fr.away}: ${m[fr.result]}`;
          }).join(' / ')
        : '고정 결과 없음';
    let html = `<div class="card">
        <p style="color:#aaa;font-size:0.85em;margin-bottom:15px;">📌 고정 조건: ${fixedDesc}</p>
        <table class="data-table">
            <thead><tr><th>팀</th><th>FIFA</th><th>기본 확률</th><th>시나리오</th><th>변동</th></tr></thead><tbody>`;
    data.scenario.forEach(s => {
        const dc = s.delta>0?'#00ff88':s.delta<0?'#ff4444':'#aaa';
        const arrow = s.delta>0?'▲':s.delta<0?'▼':'-';
        html += `<tr>
            <td><strong>${s.team}</strong></td>
            <td style="color:#aaa">${s.rank}위</td>
            <td>${s.base_prob}%</td>
            <td><span class="${probClass(s.qualify_prob)}">${s.qualify_prob}%</span>
                <div class="qualify-bar"><div class="qualify-fill" style="width:${s.qualify_prob}%"></div></div></td>
            <td style="color:${dc};font-weight:bold;">${arrow} ${Math.abs(s.delta)}%p</td>
        </tr>`;
    });
    html += `</tbody></table>
        <p style="color:#555;font-size:0.75em;margin-top:10px;">시뮬레이션 ${data.simulations}회 기준</p></div>`;
    document.getElementById('whatif-result').innerHTML = html;
}

// --------------------------------
// ⑫ 예상 대진표 - 양쪽 펼침 브라켓
// --------------------------------
async function loadBracket() {
    document.getElementById('new-bracket-result').innerHTML =
        `<div class="loading"><div class="spinner"></div><p>대진표 분석 중...</p></div>`;

    const res  = await fetch('/api/bracket_prediction');
    const data = await res.json();

    if (data.error) {
        document.getElementById('new-bracket-result').innerHTML =
            `<p style="color:#ff4444;text-align:center;">${data.error}</p>`;
        return;
    }

    const b = data.bracket;
    const H = 720;

    // 경기 카드
    const card = (mid, flip = false) => {
        const m = b[mid];
        if (!m) return '<div style="height:44px;"></div>';
        const hw = m.home_prob >= m.away_prob;
        const hn = m.home ? (m.home.length > 13 ? m.home.substring(0,12)+'…' : m.home) : '';
        const an = m.away ? (m.away.length > 13 ? m.away.substring(0,12)+'…' : m.away) : '';

        const rowL = (name, prob, win) => `
            <div style="display:flex;justify-content:space-between;align-items:center;padding:3px 6px;">
                <span style="font-size:10px;font-weight:${win?600:400};color:${win?'#fff':'#555'};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;">${name}</span>
                <span style="font-size:9px;color:${win?'#00ff88':'#555'};white-space:nowrap;min-width:28px;text-align:right;">${prob}%</span>
            </div>`;
        const rowR = (name, prob, win) => `
            <div style="display:flex;justify-content:space-between;align-items:center;padding:3px 6px;">
                <span style="font-size:9px;color:${win?'#00ff88':'#555'};white-space:nowrap;min-width:28px;">${prob}%</span>
                <span style="font-size:10px;font-weight:${win?600:400};color:${win?'#fff':'#555'};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;text-align:right;">${name}</span>
            </div>`;

        return `
        <div style="background:#0d0d2e;border:0.5px solid #2a2a4e;border-radius:4px;overflow:hidden;">
            <div style="border-bottom:0.5px solid #1a1a3e;">
                ${flip ? rowR(an, m.away_prob, !hw) : rowL(hn, m.home_prob, hw)}
            </div>
            ${flip ? rowR(hn, m.home_prob, hw) : rowL(an, m.away_prob, !hw)}
            <div style="font-size:7px;color:#333;padding:1px 6px;background:#08080f;">${m.venue||''}·${m.date||''}</div>
        </div>`;
    };

    // 라운드 컬럼 (절대 위치)
    const col = (ids, flip = false) => {
        const n = ids.length;
        const slotH = H / n;
        const items = ids.map((id, i) => `
            <div style="position:absolute;top:${i*slotH}px;left:0;right:0;height:${slotH}px;display:flex;align-items:center;padding:2px 0;">
                ${card(id, flip)}
            </div>`).join('');
        return `<div style="position:relative;width:125px;height:${H}px;flex-shrink:0;">${items}</div>`;
    };

    // SVG 브라켓 연결선
    const conn = (n, dir = 'left') => {
        const W = 24;
        const slotH = H / n;
        const lines = [];
        for (let i = 0; i < n/2; i++) {
            const top = slotH*(i*2) + slotH/2;
            const bot = slotH*(i*2+1) + slotH/2;
            const mid = (top+bot)/2;
            if (dir === 'left') {
                lines.push(`<polyline points="0,${top} ${W/2},${top} ${W/2},${bot} 0,${bot}" fill="none" stroke="#2a2a4e" stroke-width="1"/>`);
                lines.push(`<line x1="${W/2}" y1="${mid}" x2="${W}" y2="${mid}" stroke="#2a2a4e" stroke-width="1"/>`);
            } else {
                lines.push(`<polyline points="${W},${top} ${W/2},${top} ${W/2},${bot} ${W},${bot}" fill="none" stroke="#2a2a4e" stroke-width="1"/>`);
                lines.push(`<line x1="${W/2}" y1="${mid}" x2="0" y2="${mid}" stroke="#2a2a4e" stroke-width="1"/>`);
            }
        }
        return `<svg width="${W}" height="${H}" style="flex-shrink:0;">${lines.join('')}</svg>`;
    };

    // SF → 결승 연결선
    const sfLine = (dir = 'left') => `
        <svg width="16" height="${H}" style="flex-shrink:0;">
            <line x1="${dir==='left'?0:16}" y1="${H/2}" x2="${dir==='left'?16:0}" y2="${H/2}" stroke="#4a4aff" stroke-width="1.5"/>
        </svg>`;

    let html = `
    <div style="margin-bottom:12px;padding:10px;background:#0d0d2e;border-radius:8px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
        <span>🏆 예상 우승: <strong style="color:#ffbb44;">${data.champion}</strong></span>
        <span style="color:#aaa;font-size:13px;">준우승: ${data.finalist}</span>
        <span style="color:#aaa;font-size:13px;">3위: ${data.third}</span>
        <span style="color:#555;font-size:11px;">⚠️ 매 실행마다 다를 수 있음</span>
    </div>

    <div style="overflow-x:auto;">

    <!-- 헤더 -->
    <div style="display:flex;align-items:center;min-width:1060px;margin-bottom:6px;">
        <div style="width:125px;text-align:center;font-size:9px;color:#aaa;border-bottom:0.5px solid #333;padding-bottom:3px;">32강</div>
        <div style="width:24px;"></div>
        <div style="width:125px;text-align:center;font-size:9px;color:#aaa;border-bottom:0.5px solid #333;padding-bottom:3px;">16강</div>
        <div style="width:24px;"></div>
        <div style="width:125px;text-align:center;font-size:9px;color:#aaa;border-bottom:0.5px solid #333;padding-bottom:3px;">8강</div>
        <div style="width:24px;"></div>
        <div style="width:125px;text-align:center;font-size:9px;color:#aaa;border-bottom:0.5px solid #333;padding-bottom:3px;">4강</div>
        <div style="width:16px;"></div>
        <div style="width:150px;text-align:center;font-size:9px;color:#ffbb44;border-bottom:0.5px solid #4a4aff;padding-bottom:3px;">🏆 결승 / 🥉 3위전</div>
        <div style="width:16px;"></div>
        <div style="width:125px;text-align:center;font-size:9px;color:#aaa;border-bottom:0.5px solid #333;padding-bottom:3px;">4강</div>
        <div style="width:24px;"></div>
        <div style="width:125px;text-align:center;font-size:9px;color:#aaa;border-bottom:0.5px solid #333;padding-bottom:3px;">8강</div>
        <div style="width:24px;"></div>
        <div style="width:125px;text-align:center;font-size:9px;color:#aaa;border-bottom:0.5px solid #333;padding-bottom:3px;">16강</div>
        <div style="width:24px;"></div>
        <div style="width:125px;text-align:center;font-size:9px;color:#aaa;border-bottom:0.5px solid #333;padding-bottom:3px;">32강</div>
    </div>

    <!-- 브라켓 본체 -->
    <div style="display:flex;align-items:center;min-width:1060px;">
        ${col(['R32_1','R32_2','R32_3','R32_4','R32_5','R32_6','R32_7','R32_8'])}
        ${conn(8,'left')}
        ${col(['R16_1','R16_2','R16_3','R16_4'])}
        ${conn(4,'left')}
        ${col(['QF_1','QF_2'])}
        ${conn(2,'left')}
        ${col(['SF_1'])}
        ${sfLine('left')}

        <!-- 중앙: 결승 + 3위전 -->
        <div style="width:150px;height:${H}px;flex-shrink:0;display:flex;flex-direction:column;align-items:stretch;justify-content:center;gap:20px;padding:0 6px;">
            <div>
                <div style="font-size:9px;color:#ffbb44;text-align:center;margin-bottom:5px;letter-spacing:1px;">🏆 결 승</div>
                ${card('FINAL')}
            </div>
            <div>
                <div style="font-size:9px;color:#555;text-align:center;margin-bottom:5px;">🥉 3위전</div>
                ${card('THIRD')}
            </div>
        </div>

        ${sfLine('right')}
        ${col(['SF_2'],true)}
        ${conn(2,'right')}
        ${col(['QF_3','QF_4'],true)}
        ${conn(4,'right')}
        ${col(['R16_5','R16_6','R16_7','R16_8'],true)}
        ${conn(8,'right')}
        ${col(['R32_9','R32_10','R32_11','R32_12','R32_13','R32_14','R32_15','R32_16'],true)}
    </div>
    </div>

    <div style="margin-top:10px;display:flex;gap:16px;font-size:11px;color:#555;">
        <span>진한 글씨 = 예상 승자</span>
        <span style="color:#00ff88;">초록 % = 승리 확률</span>
    </div>`;

    document.getElementById('new-bracket-result').innerHTML = html;
}