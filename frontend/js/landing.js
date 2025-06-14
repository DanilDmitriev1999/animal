/**
 * Landing Page functionality
 * Handles auth modal interactions, form submissions, and glassmorphism effects
 */

// Импортируем стили для Vite
import '../style.css';
import '../styles/landing.css';

// DOM Elements
const authModal = document.getElementById('authModal');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const showRegisterFormLink = document.getElementById('showRegisterForm');
const showLoginFormLink = document.getElementById('showLoginForm');
const closeAuthModalBtn = document.getElementById('closeAuthModal');
const authModalTitle = document.getElementById('authModalTitle');
const registerButton = document.getElementById('registerButton');
const loginLink = document.querySelector('.nav-link.btn');
const featureCards = document.querySelectorAll('.feature-card');
const glassElements = document.querySelectorAll('.glass');
const glassShapes = document.querySelectorAll('.glass-shape');

// Helper Functions
const toggleForms = (showLogin = true) => {
    if (showLogin) {
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        authModalTitle.textContent = 'Вход в систему';
    } else {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
        authModalTitle.textContent = 'Регистрация';
    }
};

const toggleAuthModal = (show = true) => {
    if (show) {
        authModal.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent scrolling when modal is open
    } else {
        authModal.classList.remove('active');
        document.body.style.overflow = '';
    }
};

// Glassmorphism Interactive Effects
const addGlassmorphismInteractivity = () => {
    // Parallax effect for glass shapes
    document.addEventListener('mousemove', (e) => {
        const mouseX = e.clientX / window.innerWidth;
        const mouseY = e.clientY / window.innerHeight;
        
        glassShapes.forEach((shape, index) => {
            const depth = (index + 1) * 20; // Different depths for each shape
            const translateX = (0.5 - mouseX) * depth;
            const translateY = (0.5 - mouseY) * depth;
            
            shape.style.transform = `translate(${translateX}px, ${translateY}px)`;
        });
    });
    
    // 3D tilt effect for feature cards
    featureCards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const cardRect = card.getBoundingClientRect();
            const cardCenterX = cardRect.left + cardRect.width / 2;
            const cardCenterY = cardRect.top + cardRect.height / 2;
            const angleY = (e.clientX - cardCenterX) / 10;
            const angleX = -(e.clientY - cardCenterY) / 10;
            
            card.style.transform = `perspective(1000px) rotateX(${angleX}deg) rotateY(${angleY}deg) translateZ(10px)`;
            
            // Enhance inner glow based on mouse position
            const innerGlow = card.querySelector('.inner-glow');
            if (innerGlow) {
                const percentX = (e.clientX - cardRect.left) / cardRect.width * 100;
                const percentY = (e.clientY - cardRect.top) / cardRect.height * 100;
                innerGlow.style.background = `radial-gradient(circle at ${percentX}% ${percentY}%, rgba(255, 255, 255, 0.2), transparent 70%)`;
            }
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
            const innerGlow = card.querySelector('.inner-glow');
            if (innerGlow) {
                innerGlow.style.background = '';
            }
        });
    });
};

// Event Listeners
if (showRegisterFormLink) {
    showRegisterFormLink.addEventListener('click', (e) => {
        e.preventDefault();
        toggleForms(false);
    });
}

if (showLoginFormLink) {
    showLoginFormLink.addEventListener('click', (e) => {
        e.preventDefault();
        toggleForms(true);
    });
}

if (closeAuthModalBtn) {
    closeAuthModalBtn.addEventListener('click', () => {
        toggleAuthModal(false);
    });
}

if (registerButton) {
    registerButton.addEventListener('click', () => {
        toggleForms(false);
        toggleAuthModal(true);
    });
}

if (loginLink) {
    loginLink.addEventListener('click', (e) => {
        e.preventDefault();
        toggleForms(true);
        toggleAuthModal(true);
    });
}

// Close modal when clicking outside the content
authModal.addEventListener('click', (e) => {
    if (e.target === authModal) {
        toggleAuthModal(false);
    }
});

// Helper to send auth requests
async function authRequest(url, payload, submitButton) {
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Загрузка...';
    submitButton.disabled = true;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Ошибка запроса');
        }

        const data = await response.json();
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('user_email', payload.email);
        window.location.href = 'dashboard.html';
    } catch (err) {
        alert(err.message);
    } finally {
        submitButton.textContent = originalText;
        submitButton.disabled = false;
    }
}

// Handle form submissions
loginForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    if (!email || !password) {
        alert('Пожалуйста, заполните все поля');
        return;
    }

    authRequest('/api/auth/login', { email, password }, e.submitter);
});

registerForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const passwordConfirm = document.getElementById('registerPasswordConfirm').value;

    if (!name || !email || !password || !passwordConfirm) {
        alert('Пожалуйста, заполните все поля');
        return;
    }

    if (password !== passwordConfirm) {
        alert('Пароли не совпадают');
        return;
    }

    authRequest('/api/auth/register', {
        email,
        password,
        first_name: name
    }, e.submitter);
});

// Add glass effect for reduced motion preference
const addReducedMotionGlassEffect = () => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        // Disable animations for users who prefer reduced motion
        document.documentElement.style.setProperty('--duration-normal', '0s');
        
        // Remove parallax and tilt effects
        document.removeEventListener('mousemove', () => {});
        featureCards.forEach(card => {
            card.removeEventListener('mousemove', () => {});
            card.removeEventListener('mouseleave', () => {});
        });
    }
};

// Check for dark/light mode preference
const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
document.body.setAttribute('data-color-scheme', prefersDarkMode ? 'dark' : 'light');

// Initialize glassmorphism effects
document.addEventListener('DOMContentLoaded', () => {
    addGlassmorphismInteractivity();
    addReducedMotionGlassEffect();
    
    // Add smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            if (this.getAttribute('href') !== '#' && this.getAttribute('href') !== '#login') {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    window.scrollTo({
                        top: targetElement.offsetTop - 100,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
