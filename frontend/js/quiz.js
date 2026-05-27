let mode = 'resume';
let quizState = {
    questions: [],
    currentIndex: 0,
    answers: [],
    timer: null,
    timeLeft: 0,
    questionStartTime: null,
    fileText: '',
    fileName: '',
    quizSessionId: null,
    config: {},
};

const OPTION_KEYS = ['A', 'B', 'C', 'D'];
const QUIZ_SAVE_KEY = 'quiz_saved_state';

function tryRestoreQuiz() {
    const saved = localStorage.getItem(QUIZ_SAVE_KEY);
    if (!saved) return false;

    try {
        const state = JSON.parse(saved);
        if (!state.quizSessionId || !state.questions || !state.questions.length) {
            localStorage.removeItem(QUIZ_SAVE_KEY);
            return false;
        }
        if (confirm('You have an unfinished quiz. Would you like to resume it?')) {
            quizState = state;
            document.getElementById('setupPhase').style.display = 'none';
            document.getElementById('quizPhase').style.display = 'block';
            showQuestion(state.currentIndex);
            return true;
        } else {
            localStorage.removeItem(QUIZ_SAVE_KEY);
            sessionStorage.removeItem('retryFileText');
            sessionStorage.removeItem('retryFileName');
            sessionStorage.removeItem('retryConfig');
            sessionStorage.removeItem('retryMode');
            return false;
        }
    } catch {
        localStorage.removeItem(QUIZ_SAVE_KEY);
        return false;
    }
}

function saveQuizState() {
    try {
        const state = {
            questions: quizState.questions,
            currentIndex: quizState.currentIndex,
            answers: quizState.answers,
            fileText: quizState.fileText,
            fileName: quizState.fileName,
            quizSessionId: quizState.quizSessionId,
            config: quizState.config,
        };
        localStorage.setItem(QUIZ_SAVE_KEY, JSON.stringify(state));
    } catch {}
}

function clearSavedQuiz() {
    localStorage.removeItem(QUIZ_SAVE_KEY);
}

function setMode(newMode) {
    mode = newMode;
    document.getElementById('modeResume').classList.toggle('mode-active', mode === 'resume');
    document.getElementById('modeTopic').classList.toggle('mode-active', mode === 'topic');
    document.getElementById('topicSection').style.display = mode === 'topic' ? 'block' : 'none';
    document.getElementById('resumeSection').style.display = mode === 'resume' ? 'block' : 'none';
    document.getElementById('setupError').textContent = '';
    const domainSelect = document.getElementById('domain');
    if (mode === 'topic') {
        domainSelect.required = true;
        document.getElementById('fileUpload').value = '';
        document.getElementById('fileInfo').style.display = 'none';
        document.getElementById('fileDropZone').style.display = 'block';
    }
    if (mode === 'resume') {
        domainSelect.required = false;
        domainSelect.value = '';
    }
}

function btnLoading(loading) {
    const btn = document.getElementById('generateBtn');
    btn.disabled = loading;
    btn.querySelector('.btn-text').style.display = loading ? 'none' : 'inline';
    btn.querySelector('.btn-loader').style.display = loading ? 'inline' : 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('retry') === '1') {
        autoRetry();
        return;
    }
    if (tryRestoreQuiz()) return;
    sessionStorage.removeItem('retryFileText');
    sessionStorage.removeItem('retryFileName');
    sessionStorage.removeItem('retryConfig');
    sessionStorage.removeItem('retryMode');
    setMode('resume');
    loadDomains();
    setupFileUpload();
    setupForm();
    setupKeyboardShortcuts();
});

async function loadDomains() {
    try {
        const res = await API.getDomains();
        const select = document.getElementById('domain');
        res.domains.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d;
            opt.textContent = d;
            select.appendChild(opt);
        });
    } catch {
        const select = document.getElementById('domain');
        ['Data Science', 'Frontend Development', 'Backend Development', 'DevOps', 'ML Engineering'].forEach(d => {
            const opt = document.createElement('option');
            opt.value = d;
            opt.textContent = d;
            select.appendChild(opt);
        });
    }
}

function setupFileUpload() {
    const zone = document.getElementById('fileDropZone');
    const input = document.getElementById('fileUpload');

    zone.addEventListener('click', () => input.click());
    zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            input.files = e.dataTransfer.files;
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
    input.addEventListener('change', () => {
        if (input.files.length) handleFileSelect(input.files[0]);
    });

    document.getElementById('removeFile').addEventListener('click', () => {
        input.value = '';
        document.getElementById('fileInfo').style.display = 'none';
        document.getElementById('fileDropZone').style.display = 'block';
        quizState.fileText = '';
        quizState.fileName = '';
    });
}

function handleFileSelect(file) {
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('File exceeds 10MB limit');
        return;
    }
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'doc', 'docx', 'txt'].includes(ext)) {
        showError('Unsupported file type. Use PDF, DOCX, or TXT.');
        return;
    }
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileInfo').style.display = 'flex';
    document.getElementById('fileDropZone').style.display = 'none';
    quizState.fileName = file.name;
}

function setupForm() {
    const slider = document.getElementById('passingPercentage');
    if (slider) {
        slider.addEventListener('input', () => {
            document.getElementById('passingValue').textContent = `${slider.value}%`;
        });
    }

    document.getElementById('setupForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await generateQuiz();
    });
}

async function autoRetry() {
    const configRaw = sessionStorage.getItem('retryConfig');
    if (!configRaw) {
        window.location.href = 'quiz.html';
        return;
    }

    const config = JSON.parse(configRaw);
    const fileText = sessionStorage.getItem('retryFileText') || '';
    const fileName = sessionStorage.getItem('retryFileName') || '';
    const retryMode = sessionStorage.getItem('retryMode') || 'resume';

    quizState.fileText = fileText;
    quizState.fileName = fileName;
    quizState.config = config;
    mode = retryMode;

    document.getElementById('setupPhase').style.display = 'none';
    document.getElementById('quizPhase').style.display = 'none';
    const overlay = document.getElementById('retryLoading');
    overlay.style.display = 'flex';

    const bar = document.getElementById('retryProgressFill');
    const status = document.getElementById('retryStatus');
    const statuses = [
        { pct: 15, text: 'Reading document...' },
        { pct: 35, text: 'Analyzing content...' },
        { pct: 55, text: 'Generating questions...' },
        { pct: 75, text: 'Reviewing answers...' },
        { pct: 90, text: 'Finalizing quiz...' },
    ];
    let step = 0;
    const anim = setInterval(() => {
        if (step < statuses.length) {
            bar.style.width = `${statuses[step].pct}%`;
            status.textContent = statuses[step].text;
            step++;
        } else {
            bar.style.width = '95%';
        }
    }, 800);

    try {
        const quizRes = await API.generateQuiz(config, fileText, fileName);
        clearInterval(anim);
        bar.style.width = '100%';
        status.textContent = 'Ready!';
        await new Promise(r => setTimeout(r, 400));
        overlay.style.display = 'none';
        startQuiz(quizRes);
    } catch (err) {
        clearInterval(anim);
        sessionStorage.removeItem('retryFileText');
        sessionStorage.removeItem('retryFileName');
        sessionStorage.removeItem('retryConfig');
        sessionStorage.removeItem('retryMode');
        overlay.style.display = 'none';
        document.getElementById('setupPhase').style.display = 'block';
        showError('Retry failed: ' + (err.message || 'Please try again.'));
    }
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if (document.getElementById('quizPhase').style.display !== 'block') return;
        if (e.key === 'Enter' && !e.shiftKey) {
            const nextBtn = document.getElementById('nextBtn');
            if (nextBtn && !nextBtn.disabled) {
                submitAnswer();
                e.preventDefault();
            }
        }
        const num = parseInt(e.key);
        if (num >= 1 && num <= 4) {
            const options = document.querySelectorAll('.mcq-option');
            if (options[num - 1]) options[num - 1].click();
        }
    });
}

function showError(msg) {
    const el = document.getElementById('setupError');
    if (el) el.textContent = msg;
}

async function generateQuiz() {
    const domain = document.getElementById('domain').value;
    const fileInput = document.getElementById('fileUpload');
    const mcqCount = parseInt(document.getElementById('mcqCount').value);
    const hasLong = document.getElementById('hasLongQuestions').checked;
    const passing = parseFloat(document.getElementById('passingPercentage').value);

    if (mode === 'topic') {
        if (!domain) { showError('Please select a domain'); return; }
        showError('');

        btnLoading(true);
        try {
            quizState.config = {
                domain,
                mcq_count: mcqCount,
                has_long_questions: hasLong,
                passing_percentage: passing,
                source_type: 'topic',
            };
            quizState.fileText = '';
            quizState.fileName = '';

            const quizRes = await API.generateQuiz(quizState.config);
            startQuiz(quizRes);
        } catch (err) {
            showError(err.message || 'Failed to generate quiz. Please try again.');
        } finally {
            btnLoading(false);
        }
    } else {
        if (!fileInput.files.length) { showError('Please upload a resume'); return; }
        showError('');

        btnLoading(true);
        try {
            const uploadRes = await API.uploadFile(fileInput.files[0], 'auto');

            let detectedDomain = uploadRes.detected_domain;
            if (!detectedDomain || detectedDomain === 'Unknown') {
                detectedDomain = 'General / Other';
            }

            quizState.fileText = uploadRes.full_text || uploadRes.text_preview;
            quizState.fileName = uploadRes.filename;
            quizState.config = {
                domain: detectedDomain,
                mcq_count: mcqCount,
                has_long_questions: hasLong,
                passing_percentage: passing,
                source_type: 'resume',
            };

            const quizRes = await API.generateQuiz(
                quizState.config,
                quizState.fileText,
                uploadRes.filename
            );

            startQuiz(quizRes);
        } catch (err) {
            showError(err.message || 'Failed to generate quiz. Please try again.');
        } finally {
            btnLoading(false);
        }
    }
}

function startQuiz(session) {
    quizState.questions = session.questions;
    quizState.quizSessionId = session.id;
    quizState.currentIndex = 0;
    quizState.answers = new Array(session.questions.length).fill(null).map(() => ({
        question_id: null,
        selected_answer: null,
        time_taken: 0,
        timed_out: false,
    }));

    document.getElementById('setupPhase').style.display = 'none';
    document.getElementById('quizPhase').style.display = 'block';

    showQuestion(0);
}

function showQuestion(index) {
    const q = quizState.questions[index];
    if (!q) return;

    quizState.currentIndex = index;
    quizState.answers[index].question_id = q.id;

    document.getElementById('questionCounter').textContent =
        `Question ${index + 1}/${quizState.questions.length}`;
    document.getElementById('progressFill').style.width =
        `${((index) / quizState.questions.length) * 100}%`;

    const badge = document.getElementById('questionTypeBadge');
    if (q.question_type === 'mcq') {
        badge.textContent = 'MCQ';
        document.getElementById('mcqOptions').style.display = 'flex';
        document.getElementById('longAnswerArea').style.display = 'none';
        document.getElementById('questionCounter').textContent += '  [1-4 to select, Enter to confirm]';
    } else {
        badge.textContent = 'Long Answer';
        document.getElementById('mcqOptions').style.display = 'none';
        document.getElementById('longAnswerArea').style.display = 'block';
        document.getElementById('questionCounter').textContent += '  [Enter to submit]';
    }

    document.getElementById('questionText').textContent = q.question_text;

    if (q.question_type === 'mcq') {
        const options = JSON.parse(q.options || '[]');
        const container = document.getElementById('mcqOptions');
        container.innerHTML = options.map((opt, i) => `
            <div class="mcq-option" data-value="${opt}" onclick="selectOption(this)">
                <span class="option-key">${OPTION_KEYS[i]}</span>
                <span>${opt}</span>
            </div>
        `).join('');
    } else {
        document.getElementById('longAnswerInput').value = '';
    }

    document.getElementById('nextBtnText').textContent =
        index === quizState.questions.length - 1 ? 'Submit Quiz' : 'Next →';

    document.getElementById('nextBtn').disabled = false;

    startTimer(q.time_limit_seconds);
}

function selectOption(el) {
    document.querySelectorAll('.mcq-option').forEach(o => o.classList.remove('selected'));
    el.classList.add('selected');
    quizState.answers[quizState.currentIndex].selected_answer = el.dataset.value;
}

function startTimer(seconds) {
    if (quizState.timer) clearInterval(quizState.timer);

    quizState.timeLeft = seconds;
    quizState.questionStartTime = Date.now();
    updateTimerDisplay();

    quizState.timer = setInterval(() => {
        quizState.timeLeft--;
        updateTimerDisplay();

        if (quizState.timeLeft <= 0) {
            clearInterval(quizState.timer);
            handleTimeout();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const el = document.getElementById('quizTimer');
    const mins = Math.floor(quizState.timeLeft / 60);
    const secs = quizState.timeLeft % 60;
    el.textContent = `⏱️ ${mins}:${secs.toString().padStart(2, '0')}`;

    el.classList.remove('warning', 'danger');
    if (quizState.timeLeft <= 5) el.classList.add('danger');
    else if (quizState.timeLeft <= 15) el.classList.add('warning');
}

function handleTimeout() {
    document.getElementById('timeoutWarning').style.display = 'flex';
    quizState.answers[quizState.currentIndex].timed_out = true;

    setTimeout(() => {
        document.getElementById('timeoutWarning').style.display = 'none';
        advanceQuestion();
    }, 1500);
}

function submitAnswer() {
    const q = quizState.questions[quizState.currentIndex];
    if (!q) return;

    if (quizState.questionStartTime) {
        quizState.answers[quizState.currentIndex].time_taken = (Date.now() - quizState.questionStartTime) / 1000;
    }

    if (q.question_type === 'mcq') {
        const selected = quizState.answers[quizState.currentIndex].selected_answer;
        if (!selected && !quizState.answers[quizState.currentIndex].timed_out) {
            alert('Please select an answer');
            return;
        }
    } else if (q.question_type === 'long') {
        const input = document.getElementById('longAnswerInput');
        const answer = input.value.trim();
        if (!answer && !quizState.answers[quizState.currentIndex].timed_out) {
            alert('Please type your answer');
            return;
        }
        quizState.answers[quizState.currentIndex].selected_answer = answer || '';
    }

    if (quizState.timer) clearInterval(quizState.timer);
    document.getElementById('nextBtn').disabled = true;
    saveQuizState();
    advanceQuestion();
}

function advanceQuestion() {
    const next = quizState.currentIndex + 1;
    if (next >= quizState.questions.length) {
        finishQuiz();
    } else {
        showQuestion(next);
    }
}

async function finishQuiz() {
    try {
        const result = await API.submitQuiz(quizState.quizSessionId, quizState.answers);
        localStorage.setItem('lastQuizResult', JSON.stringify(result));
        sessionStorage.setItem('retryFileText', quizState.fileText);
        sessionStorage.setItem('retryFileName', quizState.fileName);
        sessionStorage.setItem('retryConfig', JSON.stringify(quizState.config));
        sessionStorage.setItem('retryMode', mode);
        clearSavedQuiz();
        if (typeof showToast === 'function') {
            showToast('Quiz submitted!', 'Redirecting to results...', 'success', 2000);
        }
        setTimeout(() => { window.location.href = 'results.html'; }, 500);
    } catch (err) {
        if (typeof showToast === 'function') {
            showToast('Submission failed', err.message, 'error');
        } else {
            alert('Failed to submit quiz: ' + err.message);
        }
        document.getElementById('nextBtn').disabled = false;
    }
}
