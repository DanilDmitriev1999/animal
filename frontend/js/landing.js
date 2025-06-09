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

// Handle form submissions
loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    // Simple validation
    if (!email || !password) {
        alert('Пожалуйста, заполните все поля');
        return;
    }
    
    // In a real app, you would send this data to your backend
    console.log('Login attempt:', { email });
    
    // For demo purposes, simulate a successful login
    simulateSuccessfulAuth('login');
});

registerForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const passwordConfirm = document.getElementById('registerPasswordConfirm').value;
    
    // Simple validation
    if (!name || !email || !password || !passwordConfirm) {
        alert('Пожалуйста, заполните все поля');
        return;
    }
    
    if (password !== passwordConfirm) {
        alert('Пароли не совпадают');
        return;
    }
    
    // In a real app, you would send this data to your backend
    console.log('Registration attempt:', { name, email });
    
    // For demo purposes, simulate a successful registration
    simulateSuccessfulAuth('register');
});

// Simulate successful authentication
const simulateSuccessfulAuth = (type) => {
    // Show loading state
    const submitButton = type === 'login' 
        ? loginForm.querySelector('button[type="submit"]') 
        : registerForm.querySelector('button[type="submit"]');
    
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Загрузка...';
    submitButton.disabled = true;
    
    // Simulate API request delay
    setTimeout(() => {
        // In a real app, we would store the user data and token
        localStorage.setItem('auth_token', 'demo_token_' + Date.now());
        localStorage.setItem('user_email', type === 'login' 
            ? document.getElementById('loginEmail').value
            : document.getElementById('registerEmail').value
        );
        
        // Redirect to dashboard
        window.location.href = 'dashboard.html';
    }, 1500);
};

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
});

function initLandingPage() {
    setupAuth();
    setupAnimations();
}

function setupAuth() {
    const registerButton = document.getElementById('registerButton');
    const authModal = document.getElementById('authModal');
    const closeAuthModal = document.getElementById('closeAuthModal');
    const showRegisterForm = document.getElementById('showRegisterForm');
    const showLoginForm = document.getElementById('showLoginForm');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    // Показать модальное окно авторизации
    if (registerButton) {
        registerButton.addEventListener('click', function() {
            authModal.classList.add('active');
            document.getElementById('registerForm').classList.remove('hidden');
            document.getElementById('loginForm').classList.add('hidden');
            document.getElementById('authModalTitle').textContent = 'Регистрация';
        });
    }

    // Закрыть модальное окно
    if (closeAuthModal) {
        closeAuthModal.addEventListener('click', function() {
            authModal.classList.remove('active');
        });
    }

    // Переключение между формами входа и регистрации
    if (showRegisterForm) {
        showRegisterForm.addEventListener('click', function(e) {
            e.preventDefault();
            loginForm.classList.add('hidden');
            registerForm.classList.remove('hidden');
            document.getElementById('authModalTitle').textContent = 'Регистрация';
        });
    }

    if (showLoginForm) {
        showLoginForm.addEventListener('click', function(e) {
            e.preventDefault();
            registerForm.classList.add('hidden');
            loginForm.classList.remove('hidden');
            document.getElementById('authModalTitle').textContent = 'Вход в систему';
        });
    }

    // Обработка отправки формы входа
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // Здесь будет логика аутентификации
            console.log('Login form submitted');
            
            // Для демонстрации просто перенаправим на основную страницу
            window.location.href = 'dashboard.html';
        });
    }

    // Обработка отправки формы регистрации
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // Здесь будет логика регистрации
            console.log('Register form submitted');
            
            // Проверка совпадения паролей
            const password = document.getElementById('registerPassword').value;
            const confirmPassword = document.getElementById('registerPasswordConfirm').value;
            
            if (password !== confirmPassword) {
                alert('Пароли не совпадают');
                return;
            }
            
            // Для демонстрации просто перенаправим на основную страницу
            window.location.href = 'dashboard.html';
        });
    }

    // Закрытие модального окна при клике вне его
    window.addEventListener('click', function(e) {
        if (e.target === authModal) {
            authModal.classList.remove('active');
        }
    });
}

function setupAnimations() {
    // Анимация для фона с эффектом параллакса
    const shapes = document.querySelectorAll('.glass-shape');
    
    document.addEventListener('mousemove', function(e) {
        const x = e.clientX / window.innerWidth;
        const y = e.clientY / window.innerHeight;
        
        shapes.forEach((shape, index) => {
            const speed = (index + 1) * 20;
            const offsetX = (0.5 - x) * speed;
            const offsetY = (0.5 - y) * speed;
            
            shape.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
        });
    });
    
    // Добавляем плавное появление контента
    document.body.classList.add('loaded');
} 