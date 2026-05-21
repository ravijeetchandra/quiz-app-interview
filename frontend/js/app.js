document.addEventListener('DOMContentLoaded', () => {
    const user = getCurrentUser();

    const welcomeMsg = document.getElementById('welcomeMsg');
    const welcomeName = document.getElementById('welcomeName');
    const signupBtn = document.getElementById('signupBtn');
    const ctaSection = document.querySelector('.cta-section');

    if (isAuthenticated() && user) {
        if (welcomeMsg) welcomeMsg.style.display = 'block';
        if (welcomeName) welcomeName.textContent = user.display_name || user.email || 'User';
        if (signupBtn) signupBtn.style.display = 'none';
        if (ctaSection) ctaSection.style.display = 'none';

        const heroEl = document.querySelector('.hero-stats');
        if (heroEl) {
            API.getDashboard().then(data => {
                const totalEl = document.getElementById('totalQuizzes');
                const avgEl = document.getElementById('avgScore');
                if (totalEl) totalEl.textContent = data.total_quizzes;
                if (avgEl) avgEl.textContent = `${Math.round(data.average_score)}%`;
            }).catch(() => {});
        }
    }
});

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, { threshold: 0.15 });

document.querySelectorAll('.reveal').forEach(el => observer.observe(el));