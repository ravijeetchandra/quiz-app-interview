document.addEventListener('DOMContentLoaded', () => {
    if (!isAuthenticated()) {
        document.getElementById('dashboardLoading').style.display = 'none';
        document.getElementById('loginPrompt').style.display = 'block';
        return;
    }
    loadDashboard();
});

async function loadDashboard() {
    try {
        const data = await API.getDashboard();
        document.getElementById('dashboardLoading').style.display = 'none';
        document.getElementById('dashboardContent').style.display = 'block';

        const user = getCurrentUser();
        document.getElementById('dashboardGreeting').textContent =
            `Welcome back, ${user?.display_name || 'User'}! Keep practicing to ace your interviews.`;

        document.getElementById('totalQuizzes').textContent = data.total_quizzes;
        document.getElementById('avgScore').textContent = `${Math.round(data.average_score)}%`;
        document.getElementById('bestScore').textContent = `${Math.round(data.best_score)}%`;

        const streak = calculateStreak(data.recent_quizzes);
        document.getElementById('currentStreak').textContent = streak;

        if (data.score_trend && data.score_trend.length > 1) {
            renderTrendChart(data.score_trend);
        } else {
            document.querySelector('.dashboard-section .chart-container').innerHTML =
                '<p style="text-align:center;color:var(--text-secondary);padding:3rem;">Complete more quizzes to see your trend.</p>';
        }

        if (data.quizzes_by_domain && data.quizzes_by_domain.length) {
            renderDomainBars(data.quizzes_by_domain);
        }

        if (data.recent_quizzes && data.recent_quizzes.length) {
            renderQuizTable(data.recent_quizzes);
        } else {
            document.querySelector('.table-container').innerHTML =
                '<p style="text-align:center;color:var(--text-secondary);padding:2rem;">No quizzes completed yet. <a href="quiz.html">Take your first quiz!</a></p>';
        }
    } catch (err) {
        document.getElementById('dashboardLoading').innerHTML = `
            <p>Failed to load dashboard: ${err.message}</p>
            <button class="btn btn-primary" onclick="location.reload()">Retry</button>
        `;
    }
}

function calculateStreak(quizzes) {
    if (!quizzes || !quizzes.length) return 0;
    let streak = 0;
    for (const q of quizzes) {
        if (q.passed) streak++;
        else break;
    }
    return streak;
}

function formatDate(isoString) {
    if (!isoString) return '-';
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return '-';
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatShortDate(isoString) {
    if (!isoString) return '';
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return '';
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function renderTrendChart(trend) {
    const canvas = document.getElementById('trendCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;

    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = 250 * dpr;
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = '250px';
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = 250;
    const padding = { top: 20, right: 20, bottom: 30, left: 50 };
    const chartW = w - padding.left - padding.right;
    const chartH = h - padding.top - padding.bottom;

    const scores = trend.map(t => t.score);
    const maxScore = Math.max(...scores, 50);
    const minScore = Math.max(0, Math.min(...scores) - 10);

    const style = getComputedStyle(document.body);
    const textColor = style.getPropertyValue('--text').trim();
    const borderColor = style.getPropertyValue('--border').trim();
    const primaryColor = style.getPropertyValue('--primary').trim();
    const successColor = style.getPropertyValue('--success').trim();
    const dangerColor = style.getPropertyValue('--danger').trim();

    ctx.clearRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = borderColor;
    ctx.lineWidth = 0.5;
    ctx.setLineDash([4, 4]);
    for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(w - padding.right, y);
        ctx.stroke();

        const val = Math.round(maxScore - (i / 4) * (maxScore - minScore));
        ctx.fillStyle = textColor;
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`${val}%`, padding.left - 8, y + 4);
    }
    ctx.setLineDash([]);

    // Line
    const points = scores.map((s, i) => ({
        x: padding.left + (i / (scores.length - 1 || 1)) * chartW,
        y: padding.top + (1 - (s - minScore) / (maxScore - minScore)) * chartH,
    }));

    const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH);
    gradient.addColorStop(0, primaryColor + '40');
    gradient.addColorStop(1, primaryColor + '05');

    ctx.beginPath();
    ctx.moveTo(points[0].x, padding.top + chartH);
    for (const p of points) ctx.lineTo(p.x, p.y);
    ctx.lineTo(points[points.length - 1].x, padding.top + chartH);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.strokeStyle = primaryColor;
    ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round';
    ctx.stroke();

    // Dots
    points.forEach((p, i) => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = scores[i] >= 70 ? successColor : dangerColor;
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
    });

    // Labels
    if (trend.length <= 15) {
        ctx.fillStyle = textColor;
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        points.forEach((p, i) => {
            const date = formatShortDate(trend[i].date);
            ctx.fillText(date, p.x, h - padding.bottom + 16);
        });
    }
}

function renderDomainBars(domains) {
    const container = document.getElementById('domainBars');
    container.innerHTML = domains.map(d => {
        const pct = Math.round(d.average);
        let cls = 'poor';
        if (pct >= 70) cls = 'good';
        else if (pct >= 40) cls = 'needs-work';
        return `
            <div class="section-bar-item">
                <span class="section-bar-name">${d.domain}</span>
                <div class="section-bar-track">
                    <div class="section-bar-fill ${cls}" style="width: 0%" data-target="${pct}"></div>
                </div>
                <span class="section-bar-percent">${pct}%</span>
                <span style="font-size:0.75rem;color:var(--text-secondary);width:30px;text-align:right;">${d.count}</span>
            </div>
        `;
    }).join('');

    requestAnimationFrame(() => {
        document.querySelectorAll('#domainBars .section-bar-fill').forEach(el => {
            setTimeout(() => { el.style.width = `${el.dataset.target}%`; }, 300);
        });
    });
}

function renderQuizTable(quizzes) {
    const tbody = document.getElementById('quizTableBody');
    tbody.innerHTML = quizzes.map(q => `
        <tr>
            <td>${formatDate(q.completed_at)}</td>
            <td>${q.domain}</td>
            <td>${q.document_name.length > 25 ? q.document_name.substring(0, 25) + '...' : q.document_name}</td>
            <td><strong>${Math.round(q.percentage)}%</strong></td>
            <td><span class="pass-badge ${q.passed ? 'pass' : 'fail'}">${q.passed ? 'Pass' : 'Fail'}</span></td>
            <td><a href="results.html" class="btn btn-small btn-outline" onclick="viewResult('${q.id}')">View</a></td>
        </tr>
    `).join('');
}

async function viewResult(sessionId) {
    try {
        const result = await API.getQuizResult(sessionId);
        localStorage.setItem('lastQuizResult', JSON.stringify(result));
        window.location.href = 'results.html';
    } catch (err) {
        alert('Failed to load result: ' + err.message);
    }
}
