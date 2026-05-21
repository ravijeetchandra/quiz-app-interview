function getCurrentUser() {
    const data = localStorage.getItem('user');
    return data ? JSON.parse(data) : null;
}

function isAuthenticated() {
    return !!localStorage.getItem('access_token');
}

function handleLogout() {
    API.logout().then(() => {
        window.location.href = BASE_PATH + '/';
    });
}

function updateNav() {
    const user = getCurrentUser();
    const loginLink = document.getElementById('navLogin');
    const registerLink = document.getElementById('navRegister');
    const dashboardLink = document.getElementById('navDashboard');
    const logoutBtn = document.getElementById('navLogout');

    if (isAuthenticated()) {
        if (loginLink) loginLink.style.display = 'none';
        if (registerLink) registerLink.style.display = 'none';
        if (dashboardLink) dashboardLink.style.display = 'inline-block';
        if (logoutBtn) logoutBtn.style.display = 'inline-block';
    } else {
        if (loginLink) loginLink.style.display = 'inline-block';
        if (registerLink) registerLink.style.display = 'inline-block';
        if (dashboardLink) dashboardLink.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = 'none';
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('loginError');
    const btn = document.getElementById('loginBtn');
    const rememberMe = document.getElementById('rememberMe')?.checked ?? true;

    if (!email || !password) {
        errorEl.textContent = 'Please fill in all fields';
        return;
    }

    errorEl.textContent = '';
    btn.disabled = true;
    btn.querySelector('.btn-text').style.display = 'none';
    btn.querySelector('.btn-loader').style.display = 'inline';

    try {
        await API.login({ email, password, remember_me: rememberMe });
        showToast('Welcome back!', 'Login successful', 'success');
        window.location.href = BASE_PATH + '/';
    } catch (err) {
        errorEl.textContent = err.message || 'Login failed. Please try again.';
    } finally {
        btn.disabled = false;
        btn.querySelector('.btn-text').style.display = 'inline';
        btn.querySelector('.btn-loader').style.display = 'none';
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const displayName = document.getElementById('displayName').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const errorEl = document.getElementById('registerError');
    const btn = document.getElementById('registerBtn');

    if (!email || !password || !confirmPassword) {
        errorEl.textContent = 'Please fill in all required fields';
        return;
    }

    if (password !== confirmPassword) {
        errorEl.textContent = 'Passwords do not match';
        return;
    }

    if (password.length < 8) {
        errorEl.textContent = 'Password must be at least 8 characters';
        return;
    }

    errorEl.textContent = '';
    btn.disabled = true;
    btn.querySelector('.btn-text').style.display = 'none';
    btn.querySelector('.btn-loader').style.display = 'inline';

    try {
        await API.register({ email, password, display_name: displayName || undefined });
        window.location.href = BASE_PATH + '/';
    } catch (err) {
        errorEl.textContent = err.message || 'Registration failed. Please try again.';
    } finally {
        btn.disabled = false;
        btn.querySelector('.btn-text').style.display = 'inline';
        btn.querySelector('.btn-loader').style.display = 'none';
    }
}

async function handleForgotPassword(e) {
    e.preventDefault();
    const email = document.getElementById('email').value.trim();
    const errorEl = document.getElementById('forgotError');
    const successEl = document.getElementById('forgotSuccess');
    const btn = document.getElementById('forgotBtn');

    if (!email) {
        errorEl.textContent = 'Please enter your email';
        return;
    }

    errorEl.textContent = '';
    successEl.style.display = 'none';
    btn.disabled = true;
    btn.querySelector('.btn-text').style.display = 'none';
    btn.querySelector('.btn-loader').style.display = 'inline';

    try {
        const res = await API.forgotPassword(email);
        if (res.reset_token) {
            successEl.innerHTML = `Reset link generated! <a href="reset-password.html?token=${res.reset_token}">Click here to reset</a>`;
        } else {
            successEl.textContent = 'If that email is registered, a reset link has been sent.';
        }
        successEl.style.display = 'block';
    } catch (err) {
        errorEl.textContent = err.message || 'Something went wrong. Please try again.';
    } finally {
        btn.disabled = false;
        btn.querySelector('.btn-text').style.display = 'inline';
        btn.querySelector('.btn-loader').style.display = 'none';
    }
}

async function handleResetPassword(e) {
    e.preventDefault();
    const token = document.getElementById('resetToken').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const errorEl = document.getElementById('resetError');
    const successEl = document.getElementById('resetSuccess');
    const btn = document.getElementById('resetBtn');

    if (!password || !confirmPassword) {
        errorEl.textContent = 'Please fill in all fields';
        return;
    }

    if (password !== confirmPassword) {
        errorEl.textContent = 'Passwords do not match';
        return;
    }

    if (password.length < 8) {
        errorEl.textContent = 'Password must be at least 8 characters';
        return;
    }

    errorEl.textContent = '';
    successEl.style.display = 'none';
    btn.disabled = true;
    btn.querySelector('.btn-text').style.display = 'none';
    btn.querySelector('.btn-loader').style.display = 'inline';

    try {
        await API.resetPassword(token, password);
        successEl.innerHTML = 'Password reset successful! <a href="login.html">Log in now</a>';
        successEl.style.display = 'block';
        document.getElementById('password').value = '';
        document.getElementById('confirmPassword').value = '';
    } catch (err) {
        errorEl.textContent = err.message || 'Reset failed. The link may be expired.';
    } finally {
        btn.disabled = false;
        btn.querySelector('.btn-text').style.display = 'inline';
        btn.querySelector('.btn-loader').style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateNav();

    const loginForm = document.getElementById('loginForm');
    if (loginForm) loginForm.addEventListener('submit', handleLogin);

    const registerForm = document.getElementById('registerForm');
    if (registerForm) registerForm.addEventListener('submit', handleRegister);

    const forgotForm = document.getElementById('forgotPasswordForm');
    if (forgotForm) forgotForm.addEventListener('submit', handleForgotPassword);

    const resetForm = document.getElementById('resetPasswordForm');
    if (resetForm) {
        const params = new URLSearchParams(window.location.search);
        const token = params.get('token');
        if (token) {
            document.getElementById('resetToken').value = token;
        }
        resetForm.addEventListener('submit', handleResetPassword);
    }

    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
        toggle.textContent = theme === 'dark' ? '☀️' : '🌙';
        toggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            toggle.textContent = next === 'dark' ? '☀️' : '🌙';
        });
    }

    const mobileBtn = document.getElementById('mobileMenuBtn');
    if (mobileBtn) {
        mobileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelector('.nav-links').classList.toggle('open');
        });
    }

    document.addEventListener('click', (e) => {
        const nav = document.querySelector('.nav-links');
        if (nav && nav.classList.contains('open') && !nav.contains(e.target) && e.target !== mobileBtn) {
            nav.classList.remove('open');
        }
    });

    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            const nav = document.querySelector('.nav-links');
            if (nav) nav.classList.remove('open');
        });
    });
});
