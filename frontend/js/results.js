document.addEventListener('DOMContentLoaded', () => {
    const retryBtn = document.getElementById('retrySameBtn');
    if (retryBtn && !sessionStorage.getItem('retryConfig')) {
        retryBtn.style.display = 'none';
    }

    const resultData = localStorage.getItem('lastQuizResult');
    if (!resultData) {
        document.getElementById('resultsLoading').style.display = 'none';
        document.getElementById('resultsContent').innerHTML = `
            <div class="result-hero">
                <h1>No results found</h1>
                <p>Take a quiz first to see your results.</p>
                <a href="quiz.html" class="btn btn-primary">Take Quiz</a>
            </div>
        `;
        document.getElementById('resultsContent').style.display = 'block';
        return;
    }

    const result = JSON.parse(resultData);
    displayResults(result);
    localStorage.removeItem('lastQuizResult');
});

function displayResults(result) {
    document.getElementById('resultsLoading').style.display = 'none';
    document.getElementById('resultsContent').style.display = 'block';

    const pct = Math.round(result.percentage);
    const passed = result.passed;

    document.getElementById('scoreText').textContent = `${pct}%`;

    const ring = document.getElementById('scoreRing');
    const circumference = 565.48;
    const offset = circumference - (pct / 100) * circumference;
    ring.style.strokeDashoffset = offset;
    ring.classList.add(passed ? 'pass' : 'fail');

    document.getElementById('resultDomain').textContent = `${result.domain} — ${result.document_name}`;

    const badge = document.getElementById('resultBadge');
    badge.textContent = passed ? '✅ Passed' : '❌ Failed';
    badge.className = `result-badge ${passed ? 'pass' : 'fail'}`;

    if (!isAuthenticated() && passed) {
        const donation = document.querySelector('.donation-card');
        if (donation) {
            donation.innerHTML = `
                <span class="donation-icon">🎉</span>
                <h3>Great job! Save your progress?</h3>
                <p>Create a free account to track your quiz history, see score trends, and access your dashboard.</p>
                <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;">
                    <a href="register.html" class="btn btn-primary">Create Free Account</a>
                    <a href="donate.html" class="btn btn-outline">Support Us</a>
                </div>
            `;
        }
    }

    document.getElementById('correctCount').textContent =
        result.answer_results.filter(a => a.is_correct).length;
    document.getElementById('totalQuestions').textContent = result.answer_results.length;
    document.getElementById('passingScore').textContent = `${Math.round(result.passing_percentage)}%`;

    const title = document.getElementById('resultTitle');
    if (passed) {
        title.textContent = '🎉 Congratulations! You Passed!';
        launchConfetti();
    } else {
        title.textContent = '💪 Keep Going! You\'ll Get It Next Time!';
    }

    if (result.section_results && result.section_results.length) {
        displaySectionBreakdown(result.section_results);
    }

    displayAnswerReview(result.answer_results);
    showDonationPrompt();

    const dashBtn = document.getElementById('viewDashboardBtn');
    if (dashBtn) {
        dashBtn.style.display = isAuthenticated() ? 'inline-flex' : 'none';
    }
}

function displaySectionBreakdown(sections) {
    const container = document.getElementById('sectionBars');
    container.innerHTML = sections.map(s => {
        const pct = Math.round(s.percentage);
        let cls = 'poor';
        if (pct >= 70) cls = 'good';
        else if (pct >= 40) cls = 'needs-work';
        return `
            <div class="section-bar-item">
                <span class="section-bar-name">${s.section_name}</span>
                <div class="section-bar-track">
                    <div class="section-bar-fill ${cls}" style="width: 0%" data-target="${pct}"></div>
                </div>
                <span class="section-bar-percent">${pct}%</span>
            </div>
        `;
    }).join('');

    requestAnimationFrame(() => {
        document.querySelectorAll('.section-bar-fill').forEach(el => {
            setTimeout(() => { el.style.width = `${el.dataset.target}%`; }, 200);
        });
    });
}

function displayAnswerReview(answers) {
    const container = document.getElementById('answersList');
    container.innerHTML = answers.map(a => {
        let statusHtml = '';
        if (a.question_type === 'mcq') {
            const correct = a.is_correct;
            statusHtml = `
                <div class="your-ans ${correct ? '' : 'wrong-ans'}">Your answer: ${a.your_answer || '(timed out)'}</div>
                <div class="correct-ans">Correct: ${a.correct_answer}</div>
                ${correct ? '' : '<div class="wrong-ans">✗ Incorrect</div>'}
            `;
        } else {
            statusHtml = `
                <div class="your-ans">Your answer: ${a.your_answer || '(no answer)'}</div>
                ${a.score !== null && a.score !== undefined
                    ? `<div class="correct-ans">Score: ${(a.score * 10).toFixed(1)}/10</div>`
                    : ''}
                ${a.strengths ? `<div class="eval-item">💪 Strengths: ${JSON.parse(a.strengths).join(', ')}</div>` : ''}
                ${a.weaknesses ? `<div class="eval-item">📈 Improve: ${JSON.parse(a.weaknesses).join(', ')}</div>` : ''}
                ${a.model_answer ? `<div class="eval-item">📝 Model answer: ${a.model_answer}</div>` : ''}
            `;
        }
        return `
            <div class="answer-review-item">
                <div class="q-type">${a.question_type === 'mcq' ? 'MCQ' : 'Long Answer'} • ${a.time_taken.toFixed(1)}s ${a.timed_out ? '⏰ Timed out' : ''}</div>
                <div class="q-text">${a.question_text}</div>
                ${statusHtml}
            </div>
        `;
    }).join('');
}

function showDonationPrompt() {
    const el = document.getElementById('donationPrompt');
    if (el) el.style.display = 'block';
}

function launchConfetti() {
    const container = document.createElement('div');
    container.className = 'confetti-container';
    document.body.appendChild(container);

    const colors = ['#4361ee', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if (isDark) {
        colors.splice(0, colors.length, '#818cf8', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#f472b6');
    }
    for (let i = 0; i < 60; i++) {
        const piece = document.createElement('div');
        piece.className = 'confetti-piece';
        piece.style.left = `${Math.random() * 100}%`;
        piece.style.background = colors[Math.floor(Math.random() * colors.length)];
        piece.style.width = `${Math.random() * 8 + 4}px`;
        piece.style.height = `${Math.random() * 8 + 4}px`;
        piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
        piece.style.animationDuration = `${Math.random() * 2 + 2}s`;
        piece.style.animationDelay = `${Math.random() * 2}s`;
        container.appendChild(piece);
    }

    setTimeout(() => container.remove(), 5000);
}
