// Import markdown parser - используем глобальную переменную marked из CDN

// Configure marked for security
function initializeMarked() {
    if (typeof marked !== 'undefined') {
marked.setOptions({
    breaks: true,
    gfm: true,
    sanitize: false,
    smartLists: true,
    smartypants: true
});
        console.log('✅ Marked library initialized');
    } else {
        console.warn('⚠️ Marked library not loaded, using fallback');
    }
}

// Безопасная функция для обработки markdown
function safeMarkdown(text) {
    if (typeof marked !== 'undefined' && typeof marked.parse === 'function') {
        return marked.parse(text);
    } else if (typeof marked === 'function') {
        return marked(text);
    } else {
        // Fallback: простая обработка текста
        console.warn('Marked not available, using simple text formatting');
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>')
            .replace(/#{3}\s+(.*)/g, '<h3>$1</h3>')
            .replace(/#{2}\s+(.*)/g, '<h2>$1</h2>')
            .replace(/#{1}\s+(.*)/g, '<h1>$1</h1>');
    }
}

// API Configuration
// Используем относительные пути для работы с Vite proxy
const API_BASE_URL = '';  // Пустая строка для относительных путей

const WS_BASE_URL = (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') ? 
  (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host : 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ?
    'ws://localhost:8000' :
    `ws://${window.location.hostname}:8000`;

const API_ENDPOINTS = {
    auth: {
        register: '/api/auth/register',
        login: '/api/auth/login',
        guest: '/api/auth/guest-login',
        me: '/api/auth/me'
    },
    tracks: {
        list: '/api/tracks',
        create: '/api/tracks',
        get: (id) => `/api/tracks/${id}`,
        update: (id) => `/api/tracks/${id}`,
        delete: (id) => `/api/tracks/${id}`
    },
    chat: {
        sessions: '/api/chat/sessions',
        messages: (sessionId) => `/api/chat/sessions/${sessionId}/messages`,
        websocket: (sessionId) => `${WS_BASE_URL}/ws/chat/${sessionId}`
    },
    ai: {
        generatePlan: '/api/ai/generate-plan',
        chatResponse: '/api/ai/chat-response',
        defaultConfig: '/api/ai/default-config',
        testConnection: '/api/ai/test-connection',
        generateLesson: '/api/ai/generate-lesson',
        moduleStart: '/api/ai/module-learning-start',
        moduleChat: '/api/ai/module-chat',
        moduleComplete: '/api/ai/module-complete',
        moduleChatHistory: '/api/ai/module-chat-history'
    },
    health: '/api/health'
};

// API Utilities
async function apiRequest(endpoint, options = {}) {
    try {
        const url = `${API_BASE_URL}${endpoint}`;
        
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        };

        // Добавляем токен авторизации если пользователь залогинен
        const token = localStorage.getItem('auth_token');
        if (token) {
            defaultOptions.headers.Authorization = `Bearer ${token}`;
        }

        const finalOptions = { ...defaultOptions, ...options };
        
        console.log(`Making ${finalOptions.method} request to ${url}`);
        
        const response = await fetch(url, finalOptions);
        
        if (!response.ok) {
            let errorMessage = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
            } catch (e) {
                // Если не можем распарсить ошибку, используем статус
            }
            throw new Error(errorMessage);
        }

        // Проверяем есть ли тело ответа
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            console.log('Response data:', data);
            return data;
        } else {
            // Если нет JSON, возвращаем текст
            const text = await response.text();
            console.log('Response text:', text);
            return { success: true, message: text };
        }
    } catch (error) {
        console.error(`Error in API request to ${endpoint}:`, error);
        throw error;
    }
}

// Global Variables
let currentUser = null;
let currentTrack = null;
let currentSessionId = null;
let currentChatId = null;
let tracks = [];
let chatMessages = [];
let aiSettings = {
    model_name: "gpt-3.5-turbo",
    base_url: "https://api.openai.com/v1",
    api_key: "",
    max_tokens: 2000,
    temperature: 0.7
};
let chatWebSocket = null;
let activeChats = [];

// Переменные для изучения модуля
let currentLearningModule = null;
let currentModuleChatId = null;
let moduleSessionId = null;
let moduleChatMessages = [];
let moduleWebSocket = null;

// Конфигурация системы обучения
let learningConfig = {
    progressiveUnlock: true, // Включить прогрессивную разблокировку модулей
    showLockedModules: false, // Показывать заблокированные модули
    adaptiveLearning: true, // Адаптивное обучение на основе прогресса
    debugMode: false // Режим отладки (отключает все блокировки)
};

// Removed all sample data - tracks and chat messages

// Utility Functions
function showPage(pageId) {
    // Hide all pages immediately
    document.querySelectorAll('.page').forEach(page => {
        page.classList.add('hidden');
    });
    
    // Show selected page immediately
    const targetPage = document.getElementById(pageId);
    if (targetPage) {
        targetPage.classList.remove('hidden');
    }
    
    // Load page-specific data
    if (pageId === 'dashboard-page') {
        loadDashboard();
    } else if (pageId === 'ai-settings-page') {
        loadAISettings();
    }
}

function showDashboardSection(sectionId) {
    // Hide all dashboard sections
    document.querySelectorAll('.dashboard-section').forEach(section => {
        section.classList.add('hidden');
    });
    
    // Show selected section
    const targetSection = document.getElementById(sectionId + '-section');
    if (targetSection) {
        targetSection.classList.remove('hidden');
    }
    
    // Update sidebar active state
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Find the clicked link and make it active
    if (typeof event !== 'undefined' && event && event.target) {
        const clickedLink = event.target;
        if (clickedLink.classList && clickedLink.classList.contains('sidebar-link')) {
            clickedLink.classList.add('active');
        }
    }
    
    if (sectionId === 'tracks') {
        loadTracks();
    } else if (sectionId === 'profile') {
        loadProfile();
    }
}

function loadFromStorage() {
    try {
        const userData = localStorage.getItem('ailearning_user');
        if (userData) {
            currentUser = JSON.parse(userData);
        }
        
        const tracksData = localStorage.getItem('ailearning_tracks');
        if (tracksData) {
            tracks = JSON.parse(tracksData);
        } else {
            // Start with empty tracks array instead of sample data
            tracks = [];
        }
        
        const settingsData = localStorage.getItem('ailearning_settings');
        if (settingsData) {
            aiSettings = {...aiSettings, ...JSON.parse(settingsData)};
        }
    } catch (error) {
        console.error('Error loading from storage:', error);
        // Set empty tracks on error instead of sample data
        tracks = [];
    }
}

function saveToStorage() {
    try {
        if (currentUser) {
            localStorage.setItem('ailearning_user', JSON.stringify(currentUser));
        }
        localStorage.setItem('ailearning_tracks', JSON.stringify(tracks));
        localStorage.setItem('ailearning_settings', JSON.stringify(aiSettings));
    } catch (error) {
        console.error('Error saving to storage:', error);
    }
}

function generateId() {
    return Date.now().toString() + Math.random().toString(36).substr(2, 9);
}

// Authentication Functions
function setupAuthForm() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const authTitle = document.getElementById('auth-title');
    const authSwitchText = document.getElementById('auth-switch-text');
    const authSwitchLink = document.getElementById('auth-switch-link');
    
    let isLogin = true;
    
    function toggleForm() {
        isLogin = !isLogin;
        
        // Clear any existing errors
        clearFormErrors();
        
        if (isLogin) {
            loginForm.classList.remove('hidden');
            registerForm.classList.add('hidden');
            authTitle.textContent = 'Вход в систему';
            authSwitchText.innerHTML = 'Нет аккаунта? <a href="#" id="auth-switch-link">Зарегистрироваться</a>';
        } else {
            loginForm.classList.add('hidden');
            registerForm.classList.remove('hidden');
            authTitle.textContent = 'Регистрация';
            authSwitchText.innerHTML = 'Уже есть аккаунт? <a href="#" id="auth-switch-link">Войти</a>';
        }
        
        // Re-bind the click event
        const newSwitchLink = document.getElementById('auth-switch-link');
        if (newSwitchLink) {
            newSwitchLink.addEventListener('click', (e) => {
                e.preventDefault();
                toggleForm();
            });
        }
    }
    
    if (authSwitchLink) {
        authSwitchLink.addEventListener('click', (e) => {
            e.preventDefault();
            toggleForm();
        });
    }
    
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePassword(password) {
    // Password must be at least 8 characters long and contain at least one letter and one number
    const minLength = password.length >= 8;
    const hasLetter = /[a-zA-Z]/.test(password);
    const hasNumber = /\d/.test(password);
    
    return {
        valid: minLength && hasLetter && hasNumber,
        errors: {
            minLength,
            hasLetter,
            hasNumber
        }
    };
}

function validateForm(formData, isRegister = false) {
    const errors = {};
    
    // Email validation
    if (!formData.email || !validateEmail(formData.email)) {
        errors.email = 'Введите корректный email адрес';
    }
    
    // Password validation
    if (!formData.password) {
        errors.password = 'Пароль обязателен';
    } else {
        const passwordValidation = validatePassword(formData.password);
        if (!passwordValidation.valid) {
            errors.password = 'Пароль должен содержать минимум 8 символов, включая буквы и цифры';
        }
    }
    
    if (isRegister) {
        // Name validation
        if (!formData.name || formData.name.trim().length < 2) {
            errors.name = 'Имя должно содержать минимум 2 символа';
        }
        
        if (!formData.lastname || formData.lastname.trim().length < 2) {
            errors.lastname = 'Фамилия должна содержать минимум 2 символа';
        }
        
        // Confirm password validation
        if (formData.password !== formData.confirmPassword) {
            errors.confirmPassword = 'Пароли не совпадают';
        }
    }
    
    return errors;
}

function clearFormErrors() {
    document.querySelectorAll('.form-error').forEach(error => error.remove());
    document.querySelectorAll('.form-control.error').forEach(field => field.classList.remove('error'));
}

function showFormErrors(errors, formPrefix = '') {
    clearFormErrors();
    
    Object.keys(errors).forEach(field => {
        const inputElement = document.getElementById(formPrefix + field);
        if (inputElement) {
            inputElement.classList.add('error');
            
            const errorElement = document.createElement('div');
            errorElement.className = 'form-error';
            errorElement.textContent = errors[field];
            
            inputElement.parentNode.appendChild(errorElement);
        }
    });
}

function setButtonLoading(button, isLoading) {
    if (!button) return;
    
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = `
            <span class="loading-spinner"></span>
            Загрузка...
        `;
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || button.textContent;
    }
}

async function handleLogin(e) {
    e.preventDefault();
    
    const submitButton = e.target.querySelector('button[type="submit"]');
    setButtonLoading(submitButton, true);
    
    const formData = {
        email: document.getElementById('login-email').value,
        password: document.getElementById('login-password').value
    };
    
    const errors = validateForm(formData);
    
    if (Object.keys(errors).length > 0) {
        setButtonLoading(submitButton, false);
        showFormErrors(errors, 'login-');
        return;
    }
    
    try {
        const response = await apiRequest(API_ENDPOINTS.auth.login, {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        // Сохраняем токен и пользователя
        if (response.access_token) {
            localStorage.setItem('auth_token', response.access_token);
        }
        
        currentUser = response.user || {
            id: generateId(),
            name: 'Пользователь',
            lastname: 'API',
            email: formData.email
        };
        
        saveToStorage();
        setButtonLoading(submitButton, false);
        showPage('dashboard-page');
        
        // Загружаем треки из API для зарегистрированного пользователя
        console.log('🔄 Loading tracks from API after login...');
        await loadTracksFromAPI();
        
    } catch (error) {
        setButtonLoading(submitButton, false);
        showFormErrors({ email: error.message }, 'login-');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const submitButton = e.target.querySelector('button[type="submit"]');
    setButtonLoading(submitButton, true);
    
    const formData = {
        first_name: document.getElementById('register-name').value,
        last_name: document.getElementById('register-lastname').value,
        email: document.getElementById('register-email').value,
        password: document.getElementById('register-password').value,
        confirmPassword: document.getElementById('register-confirm').value
    };
    
    const errors = validateForm({
        name: formData.first_name,
        lastname: formData.last_name,
        email: formData.email,
        password: formData.password,
        confirmPassword: formData.confirmPassword
    }, true);
    
    if (Object.keys(errors).length > 0) {
        setButtonLoading(submitButton, false);
        showFormErrors(errors, 'register-');
        return;
    }
    
    try {
        const registerData = {
            first_name: formData.first_name,
            last_name: formData.last_name,
            email: formData.email,
            password: formData.password
        };
        
        const response = await apiRequest(API_ENDPOINTS.auth.register, {
            method: 'POST',
            body: JSON.stringify(registerData)
        });
        
        // Сохраняем токен и пользователя
        if (response.access_token) {
            localStorage.setItem('auth_token', response.access_token);
        }
        
        currentUser = response.user || {
            id: generateId(),
            name: formData.first_name,
            lastname: formData.last_name,
            email: formData.email
        };
        
        saveToStorage();
        setButtonLoading(submitButton, false);
        showPage('dashboard-page');
        
        // Загружаем треки из API для нового зарегистрированного пользователя
        console.log('🔄 Loading tracks from API after registration...');
        await loadTracksFromAPI();
        
    } catch (error) {
        setButtonLoading(submitButton, false);
        showFormErrors({ email: error.message }, 'register-');
    }
}

async function handleGuestLogin(guestName = 'Гость') {
    try {
        const response = await apiRequest(API_ENDPOINTS.auth.guest, {
            method: 'POST'
        });
        
        // Сохраняем токен и пользователя
        if (response.access_token) {
            localStorage.setItem('auth_token', response.access_token);
        }
        
        currentUser = response.user || {
            id: generateId(),
            name: guestName,
            lastname: '',
            email: 'guest@local',
            is_guest: true
        };
        
        saveToStorage();
        showPage('dashboard-page');
        
    } catch (error) {
        console.error('Guest login failed:', error);
        // В случае ошибки все равно создаем локального гостя
        currentUser = {
            id: 'guest_' + generateId(),
            name: guestName,
            lastname: '',
            email: 'guest@local',
            is_guest: true
        };
        saveToStorage();
        showPage('dashboard-page');
    }
}

function logout() {
    currentUser = null;
    localStorage.removeItem('ailearning_user');
    localStorage.removeItem('auth_token');
    showPage('landing-page');
}

// Dashboard Functions
function loadDashboard() {
    if (!currentUser) {
        showPage('auth-page');
        return;
    }
    
    // Загружаем треки из API для зарегистрированных пользователей
    if (currentUser && !currentUser.is_guest) {
        loadTracksFromAPI();
    }
    
    showDashboardSection('tracks');
}

function loadTracks() {
    const container = document.getElementById('tracks-container');
    
    if (!container) return;
    
    if (tracks.length === 0) {
        container.innerHTML = `
            <div class="card">
                <div class="card__body">
                    <h3>Добро пожаловать!</h3>
                    <p>У вас пока нет треков обучения. Создайте свой первый трек, чтобы начать изучение новых навыков с помощью AI.</p>
                    <button class="btn btn--primary" onclick="showPage('create-track-page')">Создать первый трек</button>
                </div>
            </div>
        `;
        return;
    }
    
    container.innerHTML = tracks.map(track => `
        <div class="card track-card">
            <div class="card__body">
                <div class="track-card-header">
                    <h3 onclick="openTrackDetail('${track.id}')" style="cursor: pointer;">${track.title}</h3>
                    <div class="track-actions-container">
                        <span class="status status--${track.status}">
                            ${getStatusText(track.status)}
                        </span>
                        <button class="btn btn--delete" onclick="deleteTrack('${track.id}', event)" title="Удалить трек">
                            🗑️
                        </button>
                    </div>
                </div>
                <p onclick="openTrackDetail('${track.id}')" style="cursor: pointer;">${track.description}</p>
                <div class="track-progress" onclick="openTrackDetail('${track.id}')" style="cursor: pointer;">
                    <div class="progress-header">
                        <span>Прогресс</span>
                        <span>${track.progress}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${track.progress}%"></div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function loadProfile() {
    if (currentUser) {
        const nameElement = document.getElementById('user-name');
        const emailElement = document.getElementById('user-email');
        const tracksCountElement = document.getElementById('user-tracks-count');
        
        if (nameElement) nameElement.textContent = `${currentUser.name} ${currentUser.lastname}`;
        if (emailElement) emailElement.textContent = currentUser.email;
        if (tracksCountElement) tracksCountElement.textContent = tracks.length;
    }
}

function getStatusText(status) {
    const statusTexts = {
        'active': 'Активный',
        'planning': 'Планирование',
        'completed': 'Завершен',
        'paused': 'Приостановлен'
    };
    return statusTexts[status] || status;
}

function getDifficultyText(difficulty) {
    const difficultyTexts = {
        'beginner': 'Начальный',
        'intermediate': 'Средний',
        'advanced': 'Продвинутый'
    };
    return difficultyTexts[difficulty] || difficulty;
}

// Track Creation Functions
function setupTrackForm() {
    const form = document.getElementById('create-track-form');
    if (form) {
        form.addEventListener('submit', handleTrackCreation);
    }
}

function handleTrackCreation(e) {
    e.preventDefault();
    
    const submitButton = e.target.querySelector('button[type="submit"]');
    setButtonLoading(submitButton, true);
    
    const formData = {
        title: document.getElementById('track-title').value.trim(),
        description: document.getElementById('track-description').value.trim(),
        skill_area: document.getElementById('track-title').value.trim(), // Используем название как навык
        difficulty_level: document.getElementById('track-difficulty').value,
        estimated_duration_hours: parseInt(document.getElementById('track-duration').value),
        user_expectations: document.getElementById('track-expectations').value.trim()
    };
    
    // Validation
    const errors = {};
    if (!formData.title) errors.title = 'Название трека обязательно';
    if (!formData.description) errors.description = 'Описание обязательно';
    if (!formData.difficulty_level) errors.difficulty = 'Выберите уровень сложности';
    if (!formData.estimated_duration_hours || formData.estimated_duration_hours < 1) errors.duration = 'Укажите корректную продолжительность';
    
    if (Object.keys(errors).length > 0) {
        setButtonLoading(submitButton, false);
        showFormErrors(errors, 'track-');
        return;
    }

    // Create track via API
    createTrackViaAPI(formData, submitButton);
}

async function createTrackViaAPI(formData, submitButton) {
    try {
        const response = await apiRequest('/api/tracks', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        if (response && response.id) {
            // Трек успешно создан
            const newTrack = {
                id: response.id,
                title: response.title,
                description: response.description,
                skill_area: response.skill_area,
                difficulty_level: response.difficulty_level,
                duration_hours: response.estimated_duration_hours,
                expectations: response.user_expectations,
                status: response.status,
                progress: 0,
                modules: [],
                ai_generated_plan: response.ai_generated_plan
            };
            
            // Для зарегистрированных пользователей загружаем треки заново
            if (currentUser && !currentUser.is_guest) {
                await loadTracksFromAPI();
            } else {
                // Для гостей добавляем локально
                tracks.push(newTrack);
                saveToStorage();
            }
            
            currentTrack = newTrack;
            setButtonLoading(submitButton, false);
            
            // Показываем сообщение об успехе
            // План будет генерироваться в welcome-message, поэтому убираем проверку ai_generated_plan
            alert('Трек создан! Переходим к планированию курса с AI...');
            
            // Переходим к чату для планирования
            initializeChatPlanning(newTrack);
            showPage('chat-page');
        } else {
            throw new Error('Ошибка создания трека');
        }
    } catch (error) {
        console.error('Error creating track:', error);
        setButtonLoading(submitButton, false);
        alert('Произошла ошибка при создании трека: ' + error.message);
    }
}

async function loadTracksFromAPI() {
    try {
        const response = await apiRequest('/api/tracks');
        if (Array.isArray(response)) {
            tracks = response.map(track => ({
                id: track.id,
                title: track.title,
                description: track.description,
                skill_area: track.skill_area,
                difficulty_level: track.difficulty_level,
                duration_hours: track.estimated_duration_hours,
                expectations: track.user_expectations,
                status: track.status,
                progress: Math.floor(Math.random() * 100), // Временно случайный прогресс
                modules: track.modules ? track.modules.map(module => ({
                    id: module.id,
                    title: module.title,
                    description: module.description,
                    progress: 0, // Пока без прогресса
                    module_number: module.module_number,
                    learning_objectives: module.learning_objectives || [],
                    estimated_duration_hours: module.estimated_duration_hours,
                    status: module.status
                })) : [], // Загружаем модули из API
                ai_generated_plan: track.ai_generated_plan
            }));
            saveToStorage();
            loadTracks(); // Обновляем UI
            
            console.log('✅ Loaded tracks from API with modules:', tracks.map(t => ({
                title: t.title, 
                status: t.status, 
                modulesCount: t.modules.length
            })));
        }
    } catch (error) {
        console.error('Error loading tracks:', error);
    }
}

async function deleteTrack(trackId, event) {
    // Останавливаем всплытие события чтобы не открывать детали трека
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
    
    // Находим трек для отображения в подтверждении
    const track = tracks.find(t => t.id === trackId);
    const trackTitle = track ? track.title : 'этот трек';
    
    // Запрашиваем подтверждение
    if (!confirm(`Вы уверены, что хотите удалить трек "${trackTitle}"?\n\nЭто действие нельзя отменить. Все данные трека, включая план курса и прогресс, будут удалены навсегда.`)) {
        return;
    }
    
    try {
        // Для зарегистрированных пользователей удаляем через API
        if (currentUser && !currentUser.is_guest) {
            await apiRequest(API_ENDPOINTS.tracks.delete(trackId), {
                method: 'DELETE'
            });
            
            // Перезагружаем треки из API
            await loadTracksFromAPI();
        } else {
            // Для гостей удаляем локально
            tracks = tracks.filter(t => t.id !== trackId);
            saveToStorage();
            loadTracks();
        }
        
        // Показываем сообщение об успехе
        showSuccessMessage(`Трек "${trackTitle}" успешно удален.`);
        
        // Если мы сейчас просматриваем удаленный трек, возвращаемся к дашборду
        if (currentTrack && currentTrack.id === trackId) {
            currentTrack = null;
            showPage('dashboard-page');
        }
        
    } catch (error) {
        console.error('Error deleting track:', error);
        alert(`Произошла ошибка при удалении трека: ${error.message}`);
    }
}

// Chat Functions
function createNewChatForTrack(track) {
    // Создаем новый session_id для трека
    const trackSessionKey = `session_${track.id}`;
    currentSessionId = localStorage.getItem(trackSessionKey) || generateId();
    localStorage.setItem(trackSessionKey, currentSessionId);
    
    console.log(`Creating new chat for track ${track.id}, session: ${currentSessionId}`);
    
    // Инициализируем пустой чат
    currentChatId = null;
    activeChats = [];
    
    // Настраиваем форму чата
    setupChatForm();
    
    // Загружаем существующие чаты сессии если есть
    setTimeout(async () => {
        await loadSessionChats();
        // Не показываем welcome screen - его заменил preparation screen
    }, 500);
}

function initializeChatPlanning(track) {
    currentTrack = track;
    
    // Заполняем информацию о треке
    document.getElementById('chat-track-title').textContent = track.title;
    document.getElementById('chat-track-level').textContent = getDifficultyText(track.difficulty_level);
    document.getElementById('chat-track-duration').textContent = track.duration_hours;

    // Сбрасываем состояние планирования
    resetPlanningProgress();
    updateAIStatus('thinking', 'Готовим персональный план...');
    
    // Очищаем чат и показываем loading состояние
    chatMessages = [];
    showPlanPreparationScreen();
    
    // Создаем новый чат
    createNewChatForTrack(track);
    
    // Подключаемся к WebSocket
    connectChatWebSocket();
    
    // Инициализируем AI статус
    initializeAIPlanning();
    
    showPage('chat-page');
    
    // Автоматически запрашиваем приветственное сообщение с планом от AI
    setTimeout(() => {
        sendWelcomeMessage();
    }, 1000);
}

function showPlanPreparationScreen() {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;
    
    chatContainer.innerHTML = `
        <div class="plan-preparation-screen">
            <div class="preparation-icon">🤖</div>
            <h2 class="preparation-title">AI готовит персональный план курса</h2>
            <p class="preparation-subtitle">Анализируем ваши требования и создаем оптимальную структуру обучения...</p>
            
            <div class="preparation-progress">
                <div class="progress-step active">
                    <div class="step-icon active">⟳</div>
                    <span>Анализ целей обучения</span>
                </div>
                <div class="progress-step pending">
                    <div class="step-icon pending">2</div>
                    <span>Создание структуры курса</span>
                </div>
                <div class="progress-step pending">
                    <div class="step-icon pending">3</div>
                    <span>Персонализация под уровень</span>
                </div>
                <div class="progress-step pending">
                    <div class="step-icon pending">4</div>
                    <span>Подготовка плана</span>
                </div>
            </div>
            
            <div class="preparation-hint">
                💡 После получения плана вы сможете обсудить детали и внести изменения
            </div>
        </div>
    `;
    
    // Анимируем прогресс подготовки
    animatePreparationProgress();
}

function animatePreparationProgress() {
    const steps = document.querySelectorAll('.preparation-progress .progress-step');
    
    let currentStep = 0;
    const interval = setInterval(() => {
        if (currentStep < steps.length) {
            // Завершаем предыдущий шаг
            if (currentStep > 0) {
                const prevStep = steps[currentStep - 1];
                prevStep.className = 'progress-step completed';
                prevStep.querySelector('.step-icon').className = 'step-icon completed';
                prevStep.querySelector('.step-icon').innerHTML = '✓';
            }
            
            // Активируем текущий шаг
            if (currentStep < steps.length) {
                const currentStepEl = steps[currentStep];
                currentStepEl.className = 'progress-step active';
                currentStepEl.querySelector('.step-icon').className = 'step-icon active';
                currentStepEl.querySelector('.step-icon').innerHTML = '⟳';
            }
            
            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 1500);
    
    // Сохраняем interval ID для возможной очистки
    window.preparationInterval = interval;
}


function hidePlanPreparationScreen() {
    const preparationScreen = document.querySelector('.plan-preparation-screen');
    if (preparationScreen) {
        preparationScreen.remove();
    }
}

function resetPlanningProgress() {
    const steps = document.querySelectorAll('#planning-steps .progress-step');
    steps.forEach((step, index) => {
        step.className = 'progress-step pending';
        const icon = step.querySelector('.step-icon');
        icon.className = 'step-icon pending';
        icon.textContent = index + 1;
    });
}

function updatePlanningProgress(stepIndex, status = 'active') {
    const steps = document.querySelectorAll('#planning-steps .progress-step');
    const step = steps[stepIndex];
    
    if (step) {
        step.className = `progress-step ${status}`;
        const icon = step.querySelector('.step-icon');
        icon.className = `step-icon ${status}`;
        
        if (status === 'completed') {
            icon.innerHTML = '✓';
        } else if (status === 'active') {
            icon.innerHTML = '⟳';
        }
    }

    // Если дошли до финализации, показываем кнопку
    if (stepIndex >= 3 && status === 'active') {
        showFinalizeButton();
    }
}

function updateAIStatus(status, message) {
    const aiStatusElement = document.getElementById('ai-status');
    const indicator = aiStatusElement.querySelector('.status-indicator');
    const text = aiStatusElement.querySelector('.status-text');
    
    // Обновляем классы
    aiStatusElement.className = `ai-status ${status}`;
    indicator.className = `status-indicator ${status}`;
    text.textContent = message;
}

function initializeAIPlanning() {
    updateAIStatus('ready', 'Готов к планированию');
    
    // Скрываем кнопку финализации
    const finalizeBtn = document.getElementById('finalize-main-btn');
    if (finalizeBtn) {
        finalizeBtn.style.display = 'none';
    }
}

function hideWelcomeScreen() {
    const welcomeScreen = document.getElementById('chat-welcome');
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none';
    }
}

// Функция для сохранения сообщений чата
function saveChatMessages() {
    if (currentTrack && chatMessages.length > 0) {
        const trackChatKey = `chat_${currentTrack.id}`;
        try {
            localStorage.setItem(trackChatKey, JSON.stringify(chatMessages));
            
            // 🆕 Также сохраняем текущий chat_id для трека
            if (currentChatId) {
                const trackChatIdKey = `chat_id_${currentTrack.id}`;
                localStorage.setItem(trackChatIdKey, currentChatId);
            }
        } catch (error) {
            console.error('Error saving chat messages:', error);
        }
    }
}

// 🆕 Функция для восстановления chat_id из localStorage
function restoreChatId() {
    if (currentTrack) {
        const trackChatIdKey = `chat_id_${currentTrack.id}`;
        const savedChatId = localStorage.getItem(trackChatIdKey);
        if (savedChatId && !currentChatId) {
            currentChatId = savedChatId;
            console.log(`Restored chat_id from localStorage: ${currentChatId}`);
        }
    }
}

async function sendWelcomeMessage() {
    if (!currentTrack) return;

    try {
        updateAIStatus('thinking', 'AI создает базовый план курса...');
        const response = await apiRequest('/api/ai/welcome-message', {
            method: 'POST',
            body: JSON.stringify({
                session_id: currentSessionId,
                user_id: currentUser ? currentUser.id : 'guest_' + generateId(),
                skill_area: currentTrack.skill_area || currentTrack.title,
                user_expectations: currentTrack.expectations || 'Изучить основы',
                difficulty_level: currentTrack.difficulty_level,
                duration_hours: currentTrack.duration_hours || 10
            })
        });
        
        if (response && response.success) {
            const welcomeMessage = {
                sender: 'ai',
                content: response.message.message || response.message,
                timestamp: new Date().toLocaleTimeString('ru-RU', {
                    hour: '2-digit', 
                    minute: '2-digit'
                }),
                tokens_used: response.message.tokens_used || response.tokens_used,
                model_used: response.message.model_used,
                chat_id: response.chat_id || response.message.chat_id, // ← Сохраняем chat_id
                isWelcome: true
            };
            
            chatMessages.push(welcomeMessage);
            loadChatMessages();
            saveChatMessages();
            showFinalizeButton();

            hidePlanPreparationScreen();
            updateAIStatus('ready', 'План готов! Можно обсуждать детали');
            updatePlanningProgress(0, 'completed');
            
            // Обновляем currentChatId если получили его от сервера
            if (response.chat_id || response.message.chat_id) {
                currentChatId = response.chat_id || response.message.chat_id;
                updateChatsUI();
                console.log(`Welcome message created chat: ${currentChatId}`);
            }
        }
    } catch (error) {
        console.error('Error sending welcome message:', error);
        
        // Fallback сообщение
        const fallbackMessage = {
            sender: 'ai',
            content: `🎯 **Добро пожаловать в планирование курса "${currentTrack.title}"!**\n\nЯ помогу вам создать индивидуальный план обучения.\n\n📋 **Что мы можем обсудить:**\n- Структуру курса\n- Временные рамки\n- Практические задания\n- Дополнительные материалы\n\nЗадавайте вопросы или предложите изменения!`,
            timestamp: new Date().toLocaleTimeString('ru-RU', {
                hour: '2-digit', 
                minute: '2-digit'
            }),
            isWelcome: true,
            isError: false
        };
        
        chatMessages.push(fallbackMessage);
        loadChatMessages();
        saveChatMessages();
        showFinalizeButton();
        hidePlanPreparationScreen();
        updateAIStatus('error', 'Ошибка создания плана');
    }
}

function showFinalizeButton() {
    const finalizeBtn = document.getElementById('finalize-main-btn');
    if (finalizeBtn) {
        finalizeBtn.style.display = 'block';
    }
    
    // Добавляем финализационное сообщение если его еще нет
    const hasFinalizationPrompt = chatMessages.some(msg => msg.isFinalizationPrompt);
    if (!hasFinalizationPrompt) {
        const finalizeContainer = document.getElementById('finalize-container');
        if (!finalizeContainer) {
            addFinalizationPrompt();
        }
    }
}

function addFinalizationPrompt() {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;

    const finalizeDiv = document.createElement('div');
    finalizeDiv.className = 'finalize-container';
    finalizeDiv.id = 'finalize-container';
    finalizeDiv.innerHTML = `
        <h4>Готов создать план курса</h4>
        <p>AI проанализировал ваши требования и готов создать детальный план курса с модулями, уроками и заданиями.</p>
        <button id="finalize-button" onclick="finalizeCoursePlan()">
            Создать курс
        </button>
        <p class="finalize-hint">Нажмите, когда будете готовы создать модули курса</p>
    `;
    
    chatContainer.appendChild(finalizeDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Убираем функцию сохранения плана
function saveCurrentPlan() {
    // Функция больше не нужна - планы сохраняются автоматически
    console.log('План сохраняется автоматически');
}

function connectChatWebSocket() {
    if (chatWebSocket) {
        chatWebSocket.close();
        chatWebSocket = null;
    }
    
    // Используем currentSessionId для WebSocket
    const sessionId = currentSessionId || generateId();
    
    // Исправляем URL для WebSocket 
    let wsUrl;
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${protocol}//${window.location.host}/ws/chat/${sessionId}`;
    } else {
        // Для разработки используем правильный хост
        const host = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
            ? 'localhost:8000' 
            : `${window.location.hostname}:8000`;
        wsUrl = `ws://${host}/ws/chat/${sessionId}`;
    }
    
    console.log('Connecting to WebSocket:', wsUrl);
    
    try {
        chatWebSocket = new WebSocket(wsUrl);
        
        chatWebSocket.onopen = function(event) {
            console.log('WebSocket connected for chat');
            
            // 🆕 Автоматически запрашиваем восстановление истории диалога
            const restoreMessage = {
                type: "restore_chat",
                user_id: currentUser ? currentUser.id : 'guest_' + generateId()
            };
            
            console.log('Requesting chat restoration:', restoreMessage);
            chatWebSocket.send(JSON.stringify(restoreMessage));
        };
        
        chatWebSocket.onmessage = function(event) {
            try {
                const response = JSON.parse(event.data);
                handleWebSocketMessage(response);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        chatWebSocket.onclose = function(event) {
            console.log('WebSocket closed, code:', event.code, 'reason:', event.reason);
            chatWebSocket = null;
            
            // Автоматическое переподключение через 3 секунды, если это было неожиданное закрытие
            if (event.code !== 1000 && event.code !== 1001) {
                console.log('Attempting to reconnect WebSocket in 3 seconds...');
                setTimeout(() => {
                    if (!chatWebSocket && currentSessionId) {
                        connectChatWebSocket();
                    }
                }, 3000);
            }
        };
        
        chatWebSocket.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
    } catch (error) {
        console.error('Error creating WebSocket:', error);
        // Fallback к REST API если WebSocket не работает
        console.log('WebSocket failed, will use REST API for chat');
    }
}

function handleWebSocketMessage(response) {
    console.log('Received WebSocket message:', response);
    
    if (response.type === 'ai_response') {
        const aiMessage = {
            sender: 'ai',
            content: response.message,
            timestamp: new Date().toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'}),
            model_used: response.model_used,
            tokens_used: response.tokens_used,
            chat_id: response.chat_id // ← Сохраняем chat_id
        };
        
        chatMessages.push(aiMessage);
        loadChatMessages();
        saveChatMessages();
        
        // Обновляем chat_id если получили новый
        if (response.chat_id && response.chat_id !== currentChatId) {
            currentChatId = response.chat_id;
            updateChatsUI();
        }
        
    } else if (response.type === 'chat_restored') {
        // 🆕 Обработка восстановления диалога
        console.log('Chat restoration response:', response);
        
        if (response.has_existing_chat && response.history && response.history.length > 0) {
            // Восстанавливаем chat_id
            currentChatId = response.chat_id;
            
            // Восстанавливаем историю диалога
            chatMessages = response.history.map(msg => ({
                sender: msg.sender,
                content: msg.content,
                timestamp: new Date(msg.timestamp).toLocaleTimeString('ru-RU', {
                    hour: '2-digit', 
                    minute: '2-digit'
                }),
                chat_id: msg.chat_id,
                tokens_used: msg.tokens_used,
                model_used: msg.ai_model_used,
                isWelcome: msg.message_type === 'welcome' || msg.sender === 'ai' && chatMessages.length === 0
            }));
            
            // Обновляем UI
            loadChatMessages();
            saveChatMessages();
            showFinalizeButton();
            
            console.log(`✅ Restored chat ${response.chat_id} with ${response.message_count} messages`);
        } else {
            console.log('ℹ️ No existing chat found, starting fresh');
        }
        
    } else if (response.type === 'finalization_complete') {
        const finalizationMessage = {
            sender: 'ai',
            content: response.message,
            timestamp: new Date().toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'}),
            chat_id: response.chat_id, // ← Сохраняем chat_id
            isFinalization: true
        };
        
        chatMessages.push(finalizationMessage);
        loadChatMessages();
        saveChatMessages();
        
        // Убираем кнопку финализации
        const finalizeContainer = document.getElementById('finalize-container');
        if (finalizeContainer) {
            finalizeContainer.remove();
        }
        
    } else if (response.type === 'error') {
        const errorMessage = {
            sender: 'ai',
            content: `Произошла ошибка: ${response.message}`,
            timestamp: new Date().toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'}),
            chat_id: response.chat_id, // ← Сохраняем chat_id
            isError: true
        };
        
        chatMessages.push(errorMessage);
        loadChatMessages();
        saveChatMessages();
    }
}

function setupChatForm() {
    const form = document.getElementById('chat-form');
    if (form) {
        form.addEventListener('submit', handleChatMessage);
    }
}

function handleChatMessage(e) {
    e.preventDefault();
    
    const input = document.getElementById('chat-message-input');
    const message = input.value.trim();
    
    if (!message) return;

    // Скрываем welcome screen при первом сообщении
    hideWelcomeScreen();
    
    // Показываем статус "думает"
    updateAIStatus('thinking', 'AI обрабатывает ваш запрос...');
    
    sendMessage(message, input);
}

function sendMessage(message, input) {
    // Добавляем сообщение пользователя
    const userMessage = {
        sender: 'user',
        content: message,
        timestamp: new Date().toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'})
    };

    chatMessages.push(userMessage);
    
    // Показываем thinking indicator
    showAIThinking();
    
    loadChatMessages();
    input.value = '';
    
    // Отправляем сообщение через API
    handleChatMessageViaAPI(message);
}

function showAIThinking() {
    const chatContainer = document.getElementById('chat-messages');
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'ai-thinking';
    thinkingDiv.id = 'ai-thinking';
    thinkingDiv.innerHTML = `
        <div class="thinking-dots">
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
        </div>
        <span>AI думает...</span>
    `;
    
    chatContainer.appendChild(thinkingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function hideAIThinking() {
    const thinkingDiv = document.getElementById('ai-thinking');
    if (thinkingDiv) {
        thinkingDiv.remove();
    }
}

async function handleChatMessageViaAPI(message) {
    try {
        updateAIStatus('thinking', 'AI генерирует ответ...');
        
        const response = await apiRequest('/api/ai/chat-response', {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId,
                track_context: currentTrack ? currentTrack.skill_area || currentTrack.title : 'General'
            })
        });

        hideAIThinking();
        
        if (response && response.success && response.response) {
            const aiMessage = {
                sender: 'ai',
                content: response.response,
                timestamp: new Date().toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'}),
                tokens_used: response.tokens_used,
                model_used: response.model_used,
                chat_id: response.chat_id || currentChatId
            };

            // Обновляем currentChatId если получен новый
            if (response.chat_id && !currentChatId) {
                currentChatId = response.chat_id;
            }

            chatMessages.push(aiMessage);
            loadChatMessages();
            saveChatMessages();
            
            updateAIStatus('ready', 'Готов к следующему вопросу');
            
            // Обновляем чаты UI
            updateChatsUI();
            
        } else {
            throw new Error(response?.error || 'Ошибка получения ответа от AI');
        }
        
    } catch (error) {
        hideAIThinking();
        console.error('Error sending message to AI:', error);
        
        updateAIStatus('error', 'Ошибка соединения');
        
        const errorMessage = {
            sender: 'ai',
            content: `Извините, произошла ошибка: ${error.message}. Попробуйте еще раз.`,
            timestamp: new Date().toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'}),
            isError: true
        };

        chatMessages.push(errorMessage);
        loadChatMessages();
        
        // Восстанавливаем статус через 3 секунды
        setTimeout(() => {
            updateAIStatus('ready', 'Готов к планированию');
        }, 3000);
    }
}

function generateAIResponse(userMessage) {
    // Эта функция больше не используется в продакшене, так как AI работает через WebSocket/API
    // Оставлена только для совместимости в случае необходимости fallback
    return {
        sender: 'ai',
        content: 'Функция генерации ответов временно недоступна. Используйте WebSocket соединение.',
        timestamp: new Date().toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'})
    };
}

function loadChatMessages() {
    const chatMessagesContainer = document.getElementById('chat-messages');
    if (!chatMessagesContainer) return;

    // Если нет сообщений, не показываем ничего - preparation screen уже показан
    if (chatMessages.length === 0) {
        return;
    }

    // Скрываем preparation screen если есть сообщения
    hidePlanPreparationScreen();
    
    // Очищаем контейнер
    chatMessagesContainer.innerHTML = '';

    // Показываем информацию о текущем чате
    if (currentChatId) {
        const currentChat = activeChats.find(chat => chat.id === currentChatId);
        const chatHeader = document.createElement('div');
        chatHeader.className = 'chat-header';
        chatHeader.innerHTML = `
            <div class="chat-header-info">
                <span class="chat-name">${currentChat ? currentChat.chat_name : 'Чат'}</span>
                <span class="chat-type">${currentChat ? getChatTypeText(currentChat.chat_type) : ''}</span>
            </div>
            <div class="chat-id-info">
                <small>Chat ID: ${currentChatId.substring(0, 8)}...</small>
            </div>
        `;
        chatMessagesContainer.appendChild(chatHeader);
    }

    // Отображаем сообщения
    chatMessages.forEach((message, index) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${message.sender}`;
        
        // Добавляем специальные классы
        if (message.isWelcome) messageDiv.classList.add('welcome');
        if (message.isError) messageDiv.classList.add('error');
        if (message.isFinalization) messageDiv.classList.add('finalization');

        // Создаем контент сообщения
        let messageContent = message.content;
        
        // Обрабатываем markdown для AI сообщений
        if (message.sender === 'ai') {
            messageContent = safeMarkdown(message.content);
        }

        // Добавляем метаинформацию только для AI сообщений
        let metaInfo = `<span class="timestamp">${message.timestamp}</span>`;
        
        if (message.sender === 'ai') {
            if (message.tokens_used) {
                metaInfo += ` <span class="tokens">🔢 ${message.tokens_used}</span>`;
            }
            
            if (message.model_used) {
                metaInfo += ` <span class="model">🤖 ${message.model_used}</span>`;
            }

            if (message.chat_id && message.chat_id !== currentChatId) {
                metaInfo += ` <span class="different-chat">💬 ${message.chat_id.substring(0, 8)}...</span>`;
            }
        }

        messageDiv.innerHTML = `
            <div class="message-content">${messageContent}</div>
            <div class="message-meta">${metaInfo}</div>
        `;

        chatMessagesContainer.appendChild(messageDiv);
        
        // Обновляем прогресс планирования на основе содержимого
        updatePlanningProgressFromMessage(message, index);
    });

    // Прокручиваем к последнему сообщению
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

function updatePlanningProgressFromMessage(message, index) {
    if (message.sender === 'ai') {
        const content = message.content.toLowerCase();
        
        // Обновляем прогресс на основе содержимого
        if (index === 0) {
            updatePlanningProgress(0, 'completed'); // Обсуждение началось
        }
        
        if (content.includes('модул') || content.includes('структур') || content.includes('план')) {
            updatePlanningProgress(1, 'completed'); // Структура обсуждается
        }
        
        if (content.includes('детал') || content.includes('урок') || content.includes('задани')) {
            updatePlanningProgress(2, 'completed'); // Детализация
        }
        
        if (content.includes('финализ') || content.includes('готов') && content.includes('создать')) {
            updatePlanningProgress(3, 'active'); // Готов к финализации
        }
    }
}

// Исправляем дублированную функцию и используем правильную логику AI
async function finalizeCoursePlan() {
    if (!currentTrack) {
        showErrorMessage('Трек не найден');
        return;
    }
    
    const finalizeButton = document.getElementById('finalize-button');
    if (finalizeButton) {
        setButtonLoading(finalizeButton, true);
    }
    
    try {
        // Теперь backend автоматически извлекает план из истории чата
        // Убираем генерацию course_plan на frontend
        
        const response = await apiRequest('/api/ai/finalize-course-plan', {
            method: 'POST',
            body: JSON.stringify({
                session_id: currentSessionId,
                user_id: currentUser ? currentUser.id : 'guest_' + generateId(),
                skill_area: currentTrack.skill_area || currentTrack.title,
                track_id: currentTrack.id
            })
        });
        
        if (response && response.success) {
            await processFinalizedPlan(response);
            
            // Убираем кнопку финализации
            const finalizeContainer = document.getElementById('finalize-container');
            if (finalizeContainer) {
                finalizeContainer.remove();
            }
            
            showSuccessMessage(`Создано ${response.modules_count} модулей курса!`);
        } else {
            throw new Error(response?.error || 'Ошибка финализации плана');
        }
        
    } catch (error) {
        console.error('Error finalizing course plan:', error);
        showErrorMessage(`Ошибка при финализации: ${error.message}`);
        
        // Восстанавливаем кнопку
        if (finalizeButton) {
            setButtonLoading(finalizeButton, false);
        }
    }
}

// Новая функция для обработки финализированного плана
async function processFinalizedPlan(response) {
    // Проверяем что модули получены
    const modules = response.modules || [];
    const modulesCount = response.modules_count || modules.length;
    
    console.log('Processing finalized plan:', response);
    console.log('Modules received:', modules);
    console.log('Current track before update:', currentTrack);
    
    if (modules.length === 0) {
        throw new Error('AI не смог создать модули курса. Попробуйте заново.');
    }
    
    // Обновляем статус трека
    currentTrack.status = 'active';
    currentTrack.modules = modules.map((module, index) => ({
        id: generateId(),
        title: module.title || `Модуль ${index + 1}`,
        description: module.description || 'Описание модуля',
        progress: 0,
        module_number: module.module_number || (index + 1),
        learning_objectives: module.learning_objectives || [],
        estimated_duration_hours: module.estimated_duration_hours || 5,
        status: module.status || 'not_started'
    }));
    
    console.log('Current track after module update:', currentTrack);
    console.log('Modules added to track:', currentTrack.modules);
    
    // Обновляем трек в списке
    const trackIndex = tracks.findIndex(t => t.id === currentTrack.id);
    if (trackIndex !== -1) {
        tracks[trackIndex] = { ...currentTrack }; // Создаем новую копию объекта
        console.log('Updated track in tracks array at index:', trackIndex);
    } else {
        tracks.push({ ...currentTrack }); // Создаем новую копию объекта
        console.log('Added new track to tracks array');
    }
    
    // Принудительно сохраняем в localStorage
    saveToStorage();
    console.log('Saved to localStorage. Tracks array now contains:', tracks);
    
    // Создаем красивое сообщение об успехе
    const successMessage = {
        sender: 'ai',
        content: `## 🎉 План курса финализирован!

**Создано модулей:** ${modulesCount}

### 📚 Структура курса:
${modules.map((module, i) => `
**${i + 1}. ${module.title}**
- ${module.description}
- Длительность: ${module.estimated_duration_hours || 5} часов
- Цели: ${(module.learning_objectives || []).join(', ') || 'Изучение основ'}
`).join('\n')}

---
✅ **Готово!** Теперь вы можете начать обучение. Модули доступны в разделе "Мои треки".`,
        timestamp: new Date().toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'}),
        isFinalization: true
    };
    
    chatMessages.push(successMessage);
    loadChatMessages();
    saveChatMessages(); // Сохраняем сообщения
    
    // Показываем модальное окно с результатом
    showFinalizationSuccess(modulesCount, modules);
}

// Новая функция для показа успешной финализации
function showFinalizationSuccess(modulesCount, modules) {
    // Обновляем UI треков с новыми модулями
    loadTracks();
    
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal__content">
            <div class="modal__header">
                <h3>🎉 Курс успешно создан!</h3>
                <button class="modal__close" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal__body">
                <div class="finalization-success">
                    <div class="success-stats">
                        <div class="stat">
                            <div class="stat-number">${modulesCount}</div>
                            <div class="stat-label">Модулей создано</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number">${modules.reduce((sum, m) => sum + (m.estimated_duration_hours || 5), 0)}</div>
                            <div class="stat-label">Часов обучения</div>
                        </div>
                    </div>
                    
                    <div class="course-modules">
                        <h4>📚 Структура курса:</h4>
                        ${modules.map((module, i) => `
                            <div class="module-preview">
                                <div class="module-number">${i + 1}</div>
                                <div class="module-info">
                                    <h5>${module.title}</h5>
                                    <p>${module.description}</p>
                                    <div class="module-meta">
                                        ⏱️ ${module.estimated_duration_hours || 5}ч • 
                                        🎯 ${(module.learning_objectives || []).length || 3} целей
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div class="success-actions">
                        <button class="btn btn--secondary" onclick="this.closest('.modal').remove()">
                            Остаться в чате
                        </button>
                        <button class="btn btn--primary" onclick="this.closest('.modal').remove(); openTrackDetail('${currentTrack.id}');">
                            Посмотреть модули
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Автоматический переход через 10 секунд
    setTimeout(() => {
        if (document.body.contains(modal)) {
            modal.remove();
            openTrackDetail(currentTrack.id);
        }
    }, 10000);
}

// AI Settings Functions
async function loadAISettings() {
    try {
        let response;
        
        // Если пользователь авторизован, пытаемся получить его настройки
        if (currentUser && !currentUser.is_guest) {
            try {
                response = await apiRequest('/api/ai/user-config');
            } catch (error) {
                console.log('User config not available, loading defaults');
                response = null;
            }
        }
        
        // Если не получилось или пользователь гость - получаем настройки по умолчанию
        if (!response) {
            response = await apiRequest(API_ENDPOINTS.ai.defaultConfig);
        }
        
        if (response) {
            // Обновляем aiSettings настройками из backend
            aiSettings = {
                model_name: response.model_name,
                base_url: response.base_url,
                api_key: '', // API ключ не возвращается из соображений безопасности
                max_tokens: response.max_tokens || 2000,
                temperature: response.temperature || 0.7
            };
            
            console.log('Loaded AI settings:', {
                model: aiSettings.model_name,
                base_url: aiSettings.base_url,
                has_custom_key: response.has_custom_key
            });
            
            // Принудительно обновляем localStorage
            localStorage.setItem('ailearning_settings', JSON.stringify(aiSettings));
        }
    } catch (error) {
        console.error('Error loading AI settings from backend:', error);
        // Если ошибка - используем локальные настройки по умолчанию
        aiSettings = {
            model_name: "gpt-3.5-turbo",
            base_url: "https://api.openai.com/v1",
            api_key: "",
            max_tokens: 2000,
            temperature: 0.7
        };
    }
    
    // Заполняем форму актуальными настройками
    const elements = {
        'model-name': aiSettings.model_name,
        'base-url': aiSettings.base_url,
        'api-key': aiSettings.api_key,
        'max-tokens': aiSettings.max_tokens,
        'temperature': aiSettings.temperature
    };
    
    Object.keys(elements).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.value = elements[id];
            console.log(`Updated ${id}: ${element.value}`);
        }
    });
    
    const temperatureValue = document.getElementById('temperature-value');
    if (temperatureValue) {
        temperatureValue.textContent = aiSettings.temperature;
    }
}

function setupAISettingsForm() {
    const form = document.getElementById('ai-settings-form');
    const temperatureSlider = document.getElementById('temperature');
    
    if (temperatureSlider) {
        temperatureSlider.addEventListener('input', (e) => {
            const temperatureValue = document.getElementById('temperature-value');
            if (temperatureValue) {
                temperatureValue.textContent = e.target.value;
            }
        });
    }
    
    if (form) {
        form.addEventListener('submit', handleAISettingsSave);
    }
}

function handleAISettingsSave(e) {
    e.preventDefault();
    
    const submitButton = e.target.querySelector('button[type="submit"]');
    setButtonLoading(submitButton, true);
    
    setTimeout(() => {
        aiSettings = {
            model_name: document.getElementById('model-name').value,
            base_url: document.getElementById('base-url').value,
            api_key: document.getElementById('api-key').value,
            max_tokens: parseInt(document.getElementById('max-tokens').value),
            temperature: parseFloat(document.getElementById('temperature').value)
        };
        
        saveToStorage();
        setButtonLoading(submitButton, false);
        
        // Show success message
        showSuccessMessage('Настройки AI успешно сохранены!');
    }, 300);
}

function showSuccessMessage(message) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.success-message, .error-message');
    existingMessages.forEach(msg => msg.remove());
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'success-message';
    messageDiv.innerHTML = `
        <div class="message-content">
            <span class="message-icon">✅</span>
            <span class="message-text">${message}</span>
            <button class="message-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    document.body.appendChild(messageDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentElement) {
            messageDiv.remove();
        }
    }, 5000);
}

function showErrorMessage(message) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.success-message, .error-message');
    existingMessages.forEach(msg => msg.remove());
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'error-message';
    messageDiv.innerHTML = `
        <div class="message-content">
            <span class="message-icon">❌</span>
            <span class="message-text">${message}</span>
            <button class="message-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    document.body.appendChild(messageDiv);
    
    // Auto-remove after 8 seconds (longer for errors)
    setTimeout(() => {
        if (messageDiv.parentElement) {
            messageDiv.remove();
        }
    }, 8000);
}

async function testConnection() {
    const button = event.target;
    setButtonLoading(button, true);
    
    try {
        // Получаем текущие настройки из формы
        const testSettings = {
            api_key: document.getElementById('api-key').value,
            base_url: document.getElementById('base-url').value,
            model_name: document.getElementById('model-name').value
        };
        
        // Отправляем запрос на тестирование
        const response = await apiRequest(API_ENDPOINTS.ai.testConnection, {
            method: 'POST',
            body: JSON.stringify(testSettings)
        });
        
        setButtonLoading(button, false);
        
        if (response.success) {
            alert(`✅ ${response.message}\n\nМодель: ${response.model_used}\nТокенов использовано: ${response.tokens_used || 'не указано'}`);
        } else {
            alert(`❌ Ошибка подключения:\n${response.error}`);
        }
        
    } catch (error) {
        setButtonLoading(button, false);
        console.error('Test connection error:', error);
        alert(`❌ Ошибка при тестировании подключения:\n${error.message}`);
    }
}

// Track Detail Functions
function openTrackDetail(trackId) {
    // Сначала загружаем данные из localStorage для обеспечения актуальности
    loadFromStorage();
    
    const track = tracks.find(t => t.id === trackId);
    if (!track) {
        console.error('Track not found:', trackId);
        return;
    }
    
    currentTrack = track;
    console.log('Opening track detail for:', track.title);
    console.log('Track has modules:', track.modules ? track.modules.length : 0);
    
    // Update track detail page elements
    const elements = {
        'track-detail-title': track.title,
        'track-detail-description': track.description,
        'track-detail-progress': track.progress + '%'
    };
    
    Object.keys(elements).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = elements[id];
        }
    });
    
    const progressFill = document.getElementById('track-detail-progress-fill');
    if (progressFill) {
        progressFill.style.width = track.progress + '%';
    }
    
    const statusElement = document.getElementById('track-detail-status');
    if (statusElement) {
        statusElement.textContent = getStatusText(track.status);
        statusElement.className = `status status--${track.status}`;
    }
    
    // Устанавливаем состояние чекбоксов конфигурации
    setTimeout(() => {
        const progressiveUnlockCheckbox = document.getElementById('progressive-unlock');
        const adaptiveLearningCheckbox = document.getElementById('adaptive-learning');
        const debugModeCheckbox = document.getElementById('debug-mode');
        
        if (progressiveUnlockCheckbox) {
            progressiveUnlockCheckbox.checked = learningConfig.progressiveUnlock;
        }
        if (adaptiveLearningCheckbox) {
            adaptiveLearningCheckbox.checked = learningConfig.adaptiveLearning;
        }
        if (debugModeCheckbox) {
            debugModeCheckbox.checked = learningConfig.debugMode;
        }
    }, 100);
    
    // Load modules
    loadTrackModules(track);
    
    showPage('track-detail-page');
}

function loadTrackModules(track) {
    const container = document.getElementById('modules-container');
    if (!container) return;
    
    // Добавляем отладочную информацию
    console.log('Loading track modules for:', track.title);
    console.log('Track modules:', track.modules);
    console.log('Track status:', track.status);
    console.log('Modules length:', track.modules ? track.modules.length : 'undefined');
    console.log('Learning config:', learningConfig);
    
    // Проверяем что модули существуют и это массив
    if (!track.modules || !Array.isArray(track.modules) || track.modules.length === 0) {
        container.innerHTML = `
            <div class="card">
                <div class="card__body">
                    <p>Модули курса будут доступны после финализации плана обучения.</p>
                    <small>Текущий статус: ${getStatusText(track.status)}</small>
                </div>
            </div>
        `;
        return;
    }
    
    // Добавляем информационное сообщение об адаптивном обучении
    const adaptiveMessage = learningConfig.adaptiveLearning ? `
        <div class="adaptive-learning-notice card">
            <div class="card__body">
                <div class="notice-content">
                    <div class="notice-icon">🎯</div>
                    <div class="notice-text">
                        <h4>Адаптивное обучение</h4>
                        <p>План курса будет корректироваться относительно вашего прогресса для максимальной адаптации к вашим знаниям. 
                        ${learningConfig.progressiveUnlock ? 'Модули разблокируются по мере прохождения предыдущих.' : 'Все модули доступны сразу.'}</p>
                        ${learningConfig.progressiveUnlock && !learningConfig.showLockedModules ? 
                            `<button class="btn btn--outline btn--small" onclick="toggleLockedModulesVisibility()">
                                📋 Посмотреть весь план курса
                            </button>` : ''}
                    </div>
                </div>
            </div>
        </div>
    ` : '';

    // Вычисляем статусы модулей с учетом прогрессивной разблокировки
    const modulesWithStatus = calculateModuleStatuses(track.modules);
    
    // Фильтруем модули в зависимости от настроек
    const visibleModules = learningConfig.showLockedModules 
        ? modulesWithStatus 
        : modulesWithStatus.filter(module => !module.isLocked || learningConfig.debugMode);

    const lockedModulesCount = modulesWithStatus.filter(m => m.isLocked).length;
    const showToggleButton = learningConfig.progressiveUnlock && lockedModulesCount > 0;

    container.innerHTML = adaptiveMessage + 
        visibleModules.map((module, index) => {
            const actualIndex = track.modules.findIndex(m => m.id === module.id || m.module_number === module.module_number);
            return createModuleCard(module, actualIndex, track.id);
        }).join('') +
        (showToggleButton && !learningConfig.showLockedModules ? `
            <div class="locked-modules-toggle card">
                <div class="card__body text-center">
                    <button class="btn btn--outline" onclick="toggleLockedModulesVisibility()">
                        🔒 Показать заблокированные модули (${lockedModulesCount})
                    </button>
                    <p><small>Эти модули станут доступны после прохождения предыдущих</small></p>
                </div>
            </div>
        ` : '');
}

// Функция для вычисления статусов модулей с учетом блокировки
function calculateModuleStatuses(modules) {
    if (!learningConfig.progressiveUnlock || learningConfig.debugMode) {
        // Если прогрессивная разблокировка отключена, все модули доступны
        return modules.map(module => ({
            ...module,
            isLocked: false,
            unlockReason: 'Все модули доступны'
        }));
    }

    let unlockedModules = [];
    
    for (let i = 0; i < modules.length; i++) {
        const module = modules[i];
        const previousModule = i > 0 ? modules[i - 1] : null;
        
        // Первый модуль всегда разблокирован
        if (i === 0) {
            unlockedModules.push({
                ...module,
                isLocked: false,
                unlockReason: 'Первый модуль курса'
            });
            continue;
        }
        
        // Проверяем, завершен ли предыдущий модуль
        const isPreviousCompleted = previousModule && (
            previousModule.status === 'completed' || 
            (previousModule.progress && previousModule.progress >= 100)
        );
        
        // Проверяем, начат ли предыдущий модуль (частичная разблокировка)
        const isPreviousStarted = previousModule && (
            previousModule.status === 'in_progress' || 
            (previousModule.progress && previousModule.progress > 0)
        );
        
        if (isPreviousCompleted) {
            // Предыдущий модуль завершен - разблокируем текущий
            unlockedModules.push({
                ...module,
                isLocked: false,
                unlockReason: `Модуль "${previousModule.title}" завершен`
            });
        } else if (isPreviousStarted && i === 1) {
            // Если это второй модуль и первый начат, можем частично разблокировать
            unlockedModules.push({
                ...module,
                isLocked: false,
                isPartiallyLocked: true,
                unlockReason: `Модуль "${previousModule.title}" в процессе изучения`
            });
        } else {
            // Модуль заблокирован
            unlockedModules.push({
                ...module,
                isLocked: true,
                unlockReason: previousModule 
                    ? `Завершите модуль "${previousModule.title}"` 
                    : 'Завершите предыдущие модули'
            });
        }
    }
    
    return unlockedModules;
}

// Функция для создания карточки модуля
function createModuleCard(module, index, trackId) {
    const isLocked = module.isLocked && learningConfig.progressiveUnlock && !learningConfig.debugMode;
    const isPartiallyLocked = module.isPartiallyLocked && learningConfig.progressiveUnlock && !learningConfig.debugMode;
    
    const cardClasses = [
        'card', 
        'module-card',
        isLocked ? 'module-card--locked' : '',
        isPartiallyLocked ? 'module-card--partially-locked' : ''
    ].filter(Boolean).join(' ');
    
    const clickHandler = isLocked ? '' : `onclick="openModuleDetail('${trackId}', '${module.id || index}')"`;
    const cursorStyle = isLocked ? 'cursor: not-allowed;' : 'cursor: pointer;';
    
    return `
        <div class="${cardClasses}" ${clickHandler} style="${cursorStyle}">
            <div class="card__body">
                <div class="module-header">
                    <h4 class="module-title">
                        ${isLocked ? '🔒' : (isPartiallyLocked ? '🔓' : '📚')} 
                        ${module.title || `Модуль ${index + 1}`}
                    </h4>
                    <span class="module-progress">${module.progress || 0}%</span>
                </div>
                <p class="module-description">${module.description || 'Описание модуля'}</p>
                <div class="module-meta">
                    <small>⏱️ ${module.estimated_duration_hours || 5} часов • 🎯 ${(module.learning_objectives || []).length || 0} целей</small>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${module.progress || 0}%"></div>
                </div>
                <div class="module-card-actions">
                    ${isLocked ? `
                        <div class="unlock-requirement">
                            <small>🔒 ${module.unlockReason}</small>
            </div>
                    ` : `
                        <span class="module-status status--${getModuleStatusClass(module.status || 'not_started')}">
                            ${getModuleStatusText(module.status || 'not_started')}
                        </span>
                    `}
        </div>
            </div>
        </div>
    `;
}

// Функция переключения видимости заблокированных модулей
function toggleLockedModulesVisibility() {
    learningConfig.showLockedModules = !learningConfig.showLockedModules;
    
    // Обновляем интерфейс
    if (currentTrack) {
        loadTrackModules(currentTrack);
    }
    
    // Сохраняем настройки
    localStorage.setItem('learningConfig', JSON.stringify(learningConfig));
}

// Новые функции для работы с модулями

let currentModule = null;

function getModuleStatusText(status) {
    const statusMap = {
        'not_started': 'Не начат',
        'in_progress': 'В процессе',
        'completed': 'Завершен',
        'paused': 'Приостановлен'
    };
    return statusMap[status] || 'Не начат';
}

function getModuleStatusClass(status) {
    const classMap = {
        'not_started': 'planning',
        'in_progress': 'active',
        'completed': 'completed',
        'paused': 'paused'
    };
    return classMap[status] || 'planning';
}

function openModuleDetail(trackId, moduleId) {
    console.log('Opening module detail:', trackId, moduleId);
    
    const track = tracks.find(t => t.id === trackId);
    if (!track) {
        console.error('Track not found:', trackId);
        return;
    }
    
    const module = track.modules ? track.modules.find(m => (m.id || m.module_number-1) == moduleId) : null;
    if (!module) {
        console.error('Module not found:', moduleId);
        return;
    }
    
    currentModule = { ...module, trackId: trackId };
    
    // Заполняем данные модуля
    fillModuleDetails(track, module);
    
    // Показываем страницу модуля
    showPage('module-detail-page');
}

function fillModuleDetails(track, module) {
    // Breadcrumb
    const trackTitleElement = document.getElementById('module-track-title');
    const moduleTitleElement = document.getElementById('module-detail-title');
    if (trackTitleElement) trackTitleElement.textContent = track.title;
    if (moduleTitleElement) moduleTitleElement.textContent = module.title || `Модуль ${module.module_number || 1}`;
    
    // Основная информация о модуле
    const elements = {
        'module-detail-name': module.title || `Модуль ${module.module_number || 1}`,
        'module-detail-description': module.description || 'Описание модуля',
        'module-duration': module.estimated_duration_hours || 5,
        'module-objectives-count': (module.learning_objectives || []).length,
        'module-lessons-count': (module.lessons || []).length || 5, // По умолчанию 5 уроков
        'module-detail-progress': (module.progress || 0) + '%'
    };
    
    Object.keys(elements).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = elements[id];
        }
    });
    
    // Статус модуля
    const statusElement = document.getElementById('module-detail-status');
    if (statusElement) {
        statusElement.textContent = getModuleStatusText(module.status || 'not_started');
        statusElement.className = `status status--${getModuleStatusClass(module.status || 'not_started')}`;
    }
    
    // Прогресс бар
    const progressFill = document.getElementById('module-detail-progress-fill');
    if (progressFill) {
        progressFill.style.width = (module.progress || 0) + '%';
    }
    
    // Загружаем цели обучения
    loadLearningObjectives(module);
    
    // Загружаем структуру модуля (уроки)
    loadModuleLessons(module);
    
    // Загружаем практические задания
    loadModuleHomework(module);
    
    // Обновляем кнопки действий
    updateModuleActionButtons(module);
}

function loadLearningObjectives(module) {
    const container = document.getElementById('objectives-list');
    if (!container) return;
    
    const objectives = module.learning_objectives || [];
    
    if (objectives.length === 0) {
        container.innerHTML = `
            <div class="objective-item">
                <div class="objective-icon">🎯</div>
                <div class="objective-text">Цели обучения будут определены автоматически при генерации контента модуля</div>
            </div>
        `;
        return;
    }
    
    container.innerHTML = objectives.map((objective, index) => `
        <div class="objective-item">
            <div class="objective-icon">🎯</div>
            <div class="objective-text">${objective}</div>
        </div>
    `).join('');
}

function loadModuleLessons(module) {
    const container = document.getElementById('lessons-container');
    if (!container) return;
    
    // Генерируем примерные уроки если их нет
    const lessons = module.lessons || generateSampleLessons(module);
    
    container.innerHTML = lessons.map((lesson, index) => `
        <div class="lesson-item ${lesson.status || 'not-started'}" onclick="openLessonDetail('${lesson.id || index}')" style="cursor: pointer;">
            <div class="lesson-number">${index + 1}</div>
                <div class="lesson-content">
                <h5 class="lesson-title">${lesson.title || `Урок ${index + 1}: ${module.title}`}</h5>
                <p class="lesson-description">${lesson.description || 'Описание урока'}</p>
                <div class="lesson-meta">
                    <span>⏱️ ${lesson.duration || '30'} мин</span>
                    <span>📖 ${lesson.type || 'Теория'}</span>
                </div>
                </div>
            <div class="lesson-status">
                <div class="lesson-progress-circle" style="--progress: ${lesson.progress || 0}%">
                    ${lesson.status === 'completed' ? '✓' : (lesson.progress || 0) + '%'}
                </div>
            </div>
        </div>
    `).join('');
}

function generateSampleLessons(module) {
    const lessonTemplates = [
        { title: 'Введение', description: 'Основные концепции и терминология', type: 'Теория', duration: '30' },
        { title: 'Практические основы', description: 'Первые шаги и базовые навыки', type: 'Практика', duration: '45' },
        { title: 'Углубленное изучение', description: 'Детальный разбор ключевых аспектов', type: 'Теория', duration: '40' },
        { title: 'Практическое применение', description: 'Применение знаний на практике', type: 'Практика', duration: '60' },
        { title: 'Заключение и итоги', description: 'Подведение итогов и дальнейшие шаги', type: 'Теория', duration: '20' }
    ];
    
    return lessonTemplates.map((template, index) => ({
        id: `lesson_${index}`,
        title: `${template.title}: ${module.title}`,
        description: template.description,
        type: template.type,
        duration: template.duration,
        status: 'not-started',
        progress: 0
    }));
}

function loadModuleHomework(module) {
    const container = document.getElementById('homework-container');
    if (!container) return;
    
    // Генерируем примерные задания если их нет
    const homework = module.homework || generateSampleHomework(module);
    
    if (homework.length === 0) {
        container.innerHTML = `
            <div class="homework-item">
                <div class="homework-header">
                    <h5 class="homework-title">📝 Практические задания</h5>
                    <span class="homework-type">Авто-генерация</span>
                </div>
                <p class="homework-description">Задания будут сгенерированы автоматически при создании контента модуля</p>
                <div class="homework-meta">
                    <span>⏱️ Будет определено</span>
                    <span>🎯 В процессе</span>
            </div>
        </div>
    `;
        return;
    }
    
    container.innerHTML = homework.map((hw, index) => `
        <div class="homework-item" onclick="openHomeworkDetail('${hw.id || index}')" style="cursor: pointer;">
            <div class="homework-header">
                <h5 class="homework-title">${hw.title || `Задание ${index + 1}`}</h5>
                <span class="homework-type">${hw.type || 'Практика'}</span>
            </div>
            <p class="homework-description">${hw.description || 'Описание задания'}</p>
            <div class="homework-meta">
                <span>⏱️ ${hw.estimated_time || '60'} мин</span>
                <span class="status status--${hw.status || 'not_started'}">${getModuleStatusText(hw.status || 'not_started')}</span>
            </div>
        </div>
    `).join('');
}

function generateSampleHomework(module) {
    return [
        {
            id: 'hw_1',
            title: 'Практическое задание',
            description: `Примените изученные концепции модуля "${module.title}" на практике`,
            type: 'Практика',
            estimated_time: '60',
            status: 'not_started'
        },
        {
            id: 'hw_2', 
            title: 'Итоговый тест',
            description: 'Проверьте свои знания по пройденному материалу',
            type: 'Тест',
            estimated_time: '30',
            status: 'not_started'
        }
    ];
}

function updateModuleActionButtons(module) {
    const startBtn = document.getElementById('start-module-btn');
    const continueBtn = document.getElementById('continue-module-btn');
    
    if (!startBtn || !continueBtn) return;
    
    const status = module.status || 'not_started';
    
    if (status === 'not_started') {
        startBtn.style.display = 'inline-block';
        continueBtn.style.display = 'none';
        startBtn.textContent = '🚀 Начать изучение';
    } else if (status === 'in_progress') {
        startBtn.style.display = 'none';
        continueBtn.style.display = 'inline-block';
        continueBtn.textContent = '📖 Продолжить изучение';
    } else if (status === 'completed') {
        startBtn.style.display = 'inline-block';
        continueBtn.style.display = 'none';
        startBtn.textContent = '🔄 Повторить модуль';
    }
}

// Функции действий с модулем
function backToTrackDetail() {
    if (currentTrack) {
        openTrackDetail(currentTrack.id);
        } else {
        showPage('dashboard-page');
    }
}

function startModule() {
    if (!currentModule) return;
    
    // Проверяем, можно ли начать модуль (не заблокирован ли он)
    const track = tracks.find(t => t.id === currentModule.trackId);
    if (!track) return;
    
    const moduleIndex = track.modules.findIndex(m => (m.id || m.module_number-1) == currentModule.id);
    if (moduleIndex === -1) return;
    
    // Пересчитываем статусы модулей
    const modulesWithStatus = calculateModuleStatuses(track.modules);
    const moduleWithStatus = modulesWithStatus[moduleIndex];
    
    // Проверяем блокировку
    if (moduleWithStatus.isLocked && learningConfig.progressiveUnlock && !learningConfig.debugMode) {
        showErrorMessage(`🔒 Модуль заблокирован: ${moduleWithStatus.unlockReason}`);
        return;
    }
    
    // Переходим к изучению модуля
    initializeModuleLearning(track, track.modules[moduleIndex]);
}

function continueModule() {
    if (!currentModule) return;
    
    const track = tracks.find(t => t.id === currentModule.trackId);
    if (!track) return;
    
    const module = track.modules.find(m => (m.id || m.module_number-1) == currentModule.id);
    if (!module) return;
    
    // Переходим к изучению модуля
    initializeModuleLearning(track, module);
}

function generateModuleContent() {
    if (!currentModule) return;
    
    showSuccessMessage('🤖 AI генерирует контент модуля... Это может занять немного времени.');
    
    // Здесь можно добавить вызов API для генерации контента
    setTimeout(() => {
        showSuccessMessage('✅ Контент модуля успешно сгенерирован!');
        // Перезагружаем детали модуля
        const track = tracks.find(t => t.id === currentModule.trackId);
        const module = track?.modules?.find(m => (m.id || m.module_number-1) == currentModule.id);
        if (track && module) {
            fillModuleDetails(track, module);
        }
    }, 2000);
}

function downloadModulePDF() {
    if (!currentModule) return;
    
    showSuccessMessage('📄 Генерация PDF... Скачивание начнется автоматически.');
    
    // Здесь можно добавить логику для генерации и скачивания PDF
    setTimeout(() => {
        showSuccessMessage('✅ PDF модуля готов к скачиванию!');
    }, 1500);
}

function toggleLessonsView(viewType) {
    const container = document.getElementById('lessons-container');
    const buttons = document.querySelectorAll('.structure-controls .btn');
    
    if (!container) return;
    
    // Обновляем активные кнопки
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Переключаем класс контейнера
    if (viewType === 'grid') {
        container.className = 'lessons-grid';
    } else {
        container.className = 'lessons-list';
    }
}

function openLessonDetail(lessonId) {
    console.log('Opening lesson detail:', lessonId);
    showSuccessMessage('🔜 Детальный просмотр урока скоро будет доступен!');
}

function openHomeworkDetail(homeworkId) {
    console.log('Opening homework detail:', homeworkId);
    showSuccessMessage('🔜 Просмотр задания скоро будет доступен!');
}

// ... existing code ...

// Функции управления чатами
async function createNewChat(chatName, chatType = 'track_manager') {
    if (!currentSessionId) {
        console.error('No active session for creating chat');
        return null;
    }

    try {
        const response = await apiRequest('/api/chat/chats', {
            method: 'POST',
            body: JSON.stringify({
                session_id: currentSessionId,
                chat_name: chatName,
                chat_type: chatType
            })
        });

        console.log('Created new chat:', response);
        
        // Обновляем список активных чатов
        await loadSessionChats();
        
        return response.id;
    } catch (error) {
        console.error('Error creating chat:', error);
        // Для гостей создаем временный chat_id
        const tempChatId = generateId();
        console.log('Created temporary chat ID for guest:', tempChatId);
        return tempChatId;
    }
}

async function loadSessionChats() {
    if (!currentSessionId) return;

    try {
        const chats = await apiRequest(`/api/chat/sessions/${currentSessionId}/chats`);
        activeChats = chats;
        updateChatsUI();
    } catch (error) {
        console.error('Error loading session chats:', error);
        activeChats = [];
    }
}

function updateChatsUI() {
    const chatContainer = document.querySelector('.chat-main');
    if (!chatContainer) return;

    // Добавляем информацию о текущем чате
    let chatInfoHtml = '';
    if (currentChatId) {
        const currentChat = activeChats.find(chat => chat.id === currentChatId);
        const chatName = currentChat ? currentChat.chat_name : 'Чат';
        const chatType = currentChat ? getChatTypeText(currentChat.chat_type) : '';
        
        chatInfoHtml = `
            <div class="chat-info">
                <div class="current-chat">
                    <span class="chat-name">💬 ${chatName}</span>
                    <span class="chat-type">${chatType}</span>
                    <span class="chat-id">${currentChatId.substring(0, 8)}...</span>
                </div>
                ${activeChats.length > 1 ? `
                    <select id="chat-selector" onchange="switchChat(this.value)">
                        <option value="">Переключить чат</option>
                        ${activeChats.map(chat => `
                            <option value="${chat.id}" ${chat.id === currentChatId ? 'selected' : ''}>
                                ${chat.chat_name} (${getChatTypeText(chat.chat_type)})
                            </option>
                        `).join('')}
                    </select>
                ` : ''}
                <button class="btn btn--secondary btn--small" onclick="createChatDialog()">
                    ➕ Новый чат
                </button>
            </div>
        `;
    }

    // Добавляем или обновляем информацию о чате
    let chatInfoElement = chatContainer.querySelector('.chat-info');
    if (chatInfoElement) {
        chatInfoElement.outerHTML = chatInfoHtml;
    } else if (chatInfoHtml) {
        chatContainer.insertAdjacentHTML('afterbegin', chatInfoHtml);
    }
}

function getChatTypeText(chatType) {
    const types = {
        'track_manager': '📋 План курса',
        'lecture_agent': '📚 Модуль'
    };
    return types[chatType] || chatType;
}

async function switchChat(chatId) {
    if (!chatId || chatId === currentChatId) return;

    // Сохраняем текущие сообщения
    saveChatMessages();

    // Переключаемся на новый чат
    currentChatId = chatId;
    
    // Загружаем сообщения нового чата
    await loadChatMessages();
    
    // Обновляем UI
    updateChatsUI();
    
    console.log('Switched to chat:', chatId);
}

function createChatDialog() {
    const chatName = prompt('Введите название нового чата:', '');
    if (chatName && chatName.trim()) {
        createNewChatAndSwitch(chatName.trim());
    }
}

async function createNewChatAndSwitch(chatName) {
    const chatId = await createNewChat(chatName, 'track_manager');
    if (chatId) {
        await switchChat(chatId);
    }
}

// Initialize Application
function initializeApp() {
    // Инициализируем markdown библиотеку
    initializeMarked();
    
    // Clear any old sample data from localStorage
    clearOldSampleData();
    
    // Load configuration and data from storage
    loadFromStorage();
    loadLearningConfig();
    
    // Check if user is logged in
    if (currentUser) {
        showPage('dashboard-page');
        
        // Для зарегистрированных пользователей загружаем треки из API
        if (!currentUser.is_guest) {
            console.log('🔄 Loading tracks from API for registered user...');
            loadTracksFromAPI();
        } else {
            console.log('👤 Guest user detected, using localStorage tracks');
        }
    } else {
        showPage('landing-page');
    }
    
    // Setup event listeners
    setupAuthForm();
    setupTrackForm();
    setupChatForm();
    setupAISettingsForm();
}

function clearOldSampleData() {
    // Check if localStorage contains old sample tracks and remove them
    try {
        const storedTracks = localStorage.getItem('ailearning_tracks');
        if (storedTracks) {
            const tracks = JSON.parse(storedTracks);
            // Remove tracks with specific sample IDs or titles
            const filteredTracks = tracks.filter(track => 
                track.id !== "1" && 
                track.id !== "2" && 
                track.title !== "Изучение Python для анализа данных" &&
                track.title !== "Frontend разработка с React"
            );
            
            // If we filtered out some tracks, update localStorage
            if (filteredTracks.length !== tracks.length) {
                console.log('Cleared old sample tracks from localStorage');
                localStorage.setItem('ailearning_tracks', JSON.stringify(filteredTracks));
            }
        }
    } catch (error) {
        console.error('Error clearing old sample data:', error);
        // If there's an error, just clear all tracks to be safe
        localStorage.removeItem('ailearning_tracks');
    }
}

// Make functions available globally for onclick handlers
window.showPage = showPage;
window.showDashboardSection = showDashboardSection;
window.logout = logout;
window.handleGuestLogin = handleGuestLogin;
window.openTrackDetail = openTrackDetail;
window.openModuleDetail = openModuleDetail;
window.backToTrackDetail = backToTrackDetail;
window.startModule = startModule;
window.continueModule = continueModule;
window.generateModuleContent = generateModuleContent;
window.downloadModulePDF = downloadModulePDF;
window.toggleLessonsView = toggleLessonsView;
window.openLessonDetail = openLessonDetail;
window.openHomeworkDetail = openHomeworkDetail;
window.deleteTrack = deleteTrack;
window.saveCurrentPlan = saveCurrentPlan;
window.finalizeCoursePlan = finalizeCoursePlan;
window.testConnection = testConnection;
window.continuelearning = continuelearning;
window.editTrackPlan = editTrackPlan;
window.completeLessonAndContinue = completeLessonAndContinue;
window.switchChat = switchChat;
window.createChatDialog = createChatDialog;
window.toggleLockedModulesVisibility = toggleLockedModulesVisibility;
window.toggleProgressiveUnlock = toggleProgressiveUnlock;
window.toggleDebugMode = toggleDebugMode;
window.toggleAdaptiveLearning = toggleAdaptiveLearning;

// Debug functions for testing
window.debugTracks = function() {
    console.log('=== DEBUG TRACKS ===');
    console.log('Current tracks:', tracks);
    console.log('Current track:', currentTrack);
    tracks.forEach((track, index) => {
        console.log(`Track ${index}:`, track.title, 'Modules:', track.modules ? track.modules.length : 'undefined');
    });
};

window.debugModules = function(trackId) {
    const track = tracks.find(t => t.id === trackId);
    if (track) {
        console.log('=== DEBUG MODULES ===');
        console.log('Track:', track.title);
        console.log('Status:', track.status);
        console.log('Modules:', track.modules);
        console.log('Modules count:', track.modules ? track.modules.length : 'undefined');
        if (track.modules && track.modules.length > 0) {
            track.modules.forEach((module, index) => {
                console.log(`Module ${index}:`, module);
            });
        }
    } else {
        console.log('Track not found:', trackId);
    }
};

// Debug API configuration
window.debugAPI = function() {
    console.log('=== DEBUG API ===');
    console.log('API_BASE_URL:', API_BASE_URL);
    console.log('WS_BASE_URL:', WS_BASE_URL);
    console.log('window.location.hostname:', window.location.hostname);
    console.log('Is production:', window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1');
    console.log('Current user:', currentUser);
    console.log('Auth token:', localStorage.getItem('auth_token'));
};

// Test API request function
window.testAPI = async function(trackId = 'test-id') {
    console.log('=== TESTING API ===');
    
    try {
        // Test health endpoint
        console.log('Testing health endpoint...');
        const healthResponse = await fetch(`${API_BASE_URL}/api/health`);
        console.log('Health response status:', healthResponse.status);
        console.log('Health response headers:', [...healthResponse.headers.entries()]);
        
        if (healthResponse.ok) {
            const healthData = await healthResponse.text();
            console.log('Health data:', healthData);
        }
        
        // Test CORS preflight
        console.log('\nTesting CORS preflight...');
        const corsResponse = await fetch(`${API_BASE_URL}/api/tracks/${trackId}`, {
            method: 'OPTIONS',
            headers: {
                'Origin': window.location.origin,
                'Access-Control-Request-Method': 'DELETE',
                'Access-Control-Request-Headers': 'authorization,content-type'
            }
        });
        console.log('CORS preflight status:', corsResponse.status);
        console.log('CORS preflight headers:', [...corsResponse.headers.entries()]);
        
        // Test actual DELETE (will fail due to auth, but should show CORS headers)
        console.log('\nTesting DELETE request...');
        const deleteResponse = await fetch(`${API_BASE_URL}/api/tracks/${trackId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token') || 'test-token'}`
            }
        });
        console.log('DELETE response status:', deleteResponse.status);
        console.log('DELETE response headers:', [...deleteResponse.headers.entries()]);
        
        if (!deleteResponse.ok) {
            const errorText = await deleteResponse.text();
            console.log('DELETE error response:', errorText);
        }
        
        console.log('✅ All API tests completed');
        
    } catch (error) {
        console.error('❌ API test failed:', error);
        console.error('Error details:', {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
    }
};

// Test delete function specifically
window.testDelete = async function() {
    console.log('=== TESTING DELETE FUNCTION ===');
    
    // Check if we have any tracks
    console.log('Current tracks:', tracks.length);
    
    if (tracks.length === 0) {
        console.log('❌ No tracks found. Creating a test track...');
        
        // Create a test track for guest user
        const testTrack = {
            id: generateId(),
            title: 'Test Track for Deletion',
            description: 'This is a test track to test deletion',
            skill_area: 'Testing',
            difficulty_level: 'beginner',
            duration_hours: 1,
            expectations: 'Learn testing',
            status: 'planning',
            progress: 0,
            modules: [],
            ai_generated_plan: null
        };
        
        tracks.push(testTrack);
        saveToStorage();
        loadTracks();
        
        console.log('✅ Test track created:', testTrack.id);
        return testTrack.id;
    } else {
        const firstTrack = tracks[0];
        console.log('🎯 Testing with existing track:', firstTrack.title, 'ID:', firstTrack.id);
        
        // Test the delete function
        try {
            await deleteTrack(firstTrack.id);
            console.log('✅ Delete function completed successfully');
        } catch (error) {
            console.error('❌ Delete function failed:', error);
        }
    }
};

// Create test track for debugging
window.createTestTrack = function() {
    console.log('=== CREATING TEST TRACK ===');
    
    const testTrack = {
        id: generateId(),
        title: 'Тестовый курс с системой блокировки ' + new Date().getTime(),
        description: 'Курс для демонстрации прогрессивной разблокировки модулей',
        skill_area: 'Тестирование',
        difficulty_level: 'beginner',
        duration_hours: 15,
        expectations: 'Протестировать систему блокировки модулей',
        status: 'active',
        progress: 10,
        modules: [
            {
                id: 'module_1',
                title: 'Основы тестирования',
                description: 'Введение в основы тестирования ПО',
                module_number: 1,
        progress: 0,
                status: 'not_started',
                estimated_duration_hours: 3,
                learning_objectives: ['Понять основы', 'Изучить терминологию', 'Освоить базовые навыки']
            },
            {
                id: 'module_2',
                title: 'Автоматизация тестов',
                description: 'Создание автоматических тестов',
                module_number: 2,
                progress: 0,
                status: 'not_started',
                estimated_duration_hours: 5,
                learning_objectives: ['Настроить окружение', 'Написать первый тест', 'Освоить фреймворки']
            },
            {
                id: 'module_3',
                title: 'Продвинутые техники',
                description: 'Сложные сценарии и интеграционное тестирование',
                module_number: 3,
                progress: 0,
                status: 'not_started',
                estimated_duration_hours: 4,
                learning_objectives: ['Интеграционные тесты', 'Performance тестирование', 'CI/CD']
            },
            {
                id: 'module_4',
                title: 'Финальный проект',
                description: 'Создание комплексного проекта тестирования',
                module_number: 4,
                progress: 0,
                status: 'not_started',
                estimated_duration_hours: 3,
                learning_objectives: ['Планирование проекта', 'Реализация', 'Документация']
            }
        ],
        ai_generated_plan: null
    };
    
    tracks.push(testTrack);
    saveToStorage();
    loadTracks();
    
    console.log('✅ Test track created:', testTrack);
    console.log('Track ID for testing:', testTrack.id);
    
    return testTrack.id;
};

// Force clear browser cache and reload
window.clearCacheAndReload = function() {
    console.log('=== CLEARING CACHE AND RELOADING ===');
    
    // Clear localStorage
    localStorage.clear();
    
    // Clear sessionStorage
    sessionStorage.clear();
    
    // Force reload with cache bypass
    window.location.reload(true);
};

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', initializeApp);

// Восстановленные функции для совместимости
function continuelearning() {
    if (!currentTrack) {
        alert('Сначала выберите трек для продолжения обучения');
        return;
    }
    
    // Проверяем статус трека
    if (currentTrack.status === 'planning') {
        alert('Необходимо сначала завершить планирование курса');
        return;
    }
    
    if (currentTrack.status === 'completed') {
        alert('Этот курс уже завершен!');
        return;
    }
    
    // Переходим к обучению
    startLearningSession(currentTrack);
}

async function startLearningSession(track) {
    try {
        // Генерируем содержимое урока с помощью AI
        const response = await apiRequest('/api/ai/generate-lesson', {
            method: 'POST',
            body: JSON.stringify({
                lesson_title: `Урок из трека: ${track.title}`,
                module_context: track.skill_area,
                content_type: 'theory'
            })
        });
        
        if (response.success && response.content) {
            // Показываем содержимое урока
            showLessonContent(track, response.content);
        } else {
            alert('Ошибка при генерации урока: ' + (response.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Error starting learning session:', error);
        alert('Произошла ошибка при запуске обучения');
    }
}

function showLessonContent(track, content) {
    // Создаем модальное окно с содержимым урока
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal__content modal__content--large">
            <div class="modal__header">
                <h3>${track.title} - Урок</h3>
                <button class="modal__close" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal__body">
                <div class="lesson-content">
                    <pre>${content}</pre>
                </div>
                <div class="lesson-actions">
                    <button class="btn btn--secondary" onclick="this.closest('.modal').remove()">
                        Закрыть урок
                    </button>
                    <button class="btn btn--primary" onclick="completeLessonAndContinue('${track.id}')">
                        Завершить урок
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function completeLessonAndContinue(trackId) {
    const track = tracks.find(t => t.id === trackId);
    if (track) {
        // Увеличиваем прогресс
        track.progress = Math.min(track.progress + 10, 100);
        
        if (track.progress >= 100) {
            track.status = 'completed';
        } else {
            track.status = 'active';
        }
        
        saveToStorage();
        loadTracks(); // Обновляем список треков
        
        // Закрываем модальное окно
        document.querySelector('.modal').remove();
        
        alert('Урок завершен! Прогресс обновлен.');
    }
}

function editTrackPlan() {
    if (currentTrack) {
        initializeChatPlanning(currentTrack);
        showPage('chat-page');
    }
}

// Функции управления конфигурацией обучения
function toggleProgressiveUnlock() {
    learningConfig.progressiveUnlock = !learningConfig.progressiveUnlock;
    if (currentTrack) {
        loadTrackModules(currentTrack);
    }
    localStorage.setItem('learningConfig', JSON.stringify(learningConfig));
    showSuccessMessage(`Прогрессивная разблокировка ${learningConfig.progressiveUnlock ? 'включена' : 'отключена'}`);
}

function toggleDebugMode() {
    learningConfig.debugMode = !learningConfig.debugMode;
    if (currentTrack) {
        loadTrackModules(currentTrack);
    }
    localStorage.setItem('learningConfig', JSON.stringify(learningConfig));
    showSuccessMessage(`Режим отладки ${learningConfig.debugMode ? 'включен' : 'отключен'}`);
}

function toggleAdaptiveLearning() {
    learningConfig.adaptiveLearning = !learningConfig.adaptiveLearning;
    if (currentTrack) {
        loadTrackModules(currentTrack);
    }
    localStorage.setItem('learningConfig', JSON.stringify(learningConfig));
    showSuccessMessage(`Адаптивное обучение ${learningConfig.adaptiveLearning ? 'включено' : 'отключено'}`);
}

// Функция загрузки конфигурации из localStorage
function loadLearningConfig() {
    try {
        const savedConfig = localStorage.getItem('learningConfig');
        if (savedConfig) {
            learningConfig = { ...learningConfig, ...JSON.parse(savedConfig) };
        }
    } catch (error) {
        console.error('Error loading learning config:', error);
    }
}

// Функция для симуляции прогресса модуля
window.simulateModuleProgress = function(trackId, moduleIndex, progress) {
    const track = tracks.find(t => t.id === trackId);
    if (!track || !track.modules || !track.modules[moduleIndex]) {
        console.error('Track or module not found');
        return;
    }
    
    const module = track.modules[moduleIndex];
    module.progress = Math.min(100, Math.max(0, progress));
    
    // Обновляем статус в зависимости от прогресса
    if (module.progress === 0) {
        module.status = 'not_started';
    } else if (module.progress >= 100) {
        module.status = 'completed';
    } else {
        module.status = 'in_progress';
    }
    
    saveToStorage();
    
    // Обновляем интерфейс если просматриваем этот трек
    if (currentTrack && currentTrack.id === trackId) {
        loadTrackModules(currentTrack);
    }
    
    showSuccessMessage(`Модуль "${module.title}" обновлен: ${progress}% (${module.status})`);
    console.log(`Module ${moduleIndex} progress updated:`, module);
};

// === ФУНКЦИИ ИЗУЧЕНИЯ МОДУЛЯ ===

async function initializeModuleLearning(track, module) {
    console.log('Initializing module learning:', track.title, module.title);
    
    // Сохраняем текущий модуль для изучения
    currentLearningModule = {
        ...module,
        trackId: track.id,
        trackTitle: track.title
    };
    
    // Генерируем session_id для модуля
    moduleSessionId = generateId();
    
    // Заполняем информацию о модуле
    fillModuleLearningInfo(track, module);
    
    // Показываем страницу изучения
    showPage('module-learning-page');
    
    // Настраиваем форму чата модуля
    setupModuleChatForm();
    
    // Проверяем существует ли уже чат для этого модуля
    const existingChatKey = `module_chat_${track.id}_${module.id || module.module_number}`;
    const savedChat = localStorage.getItem(existingChatKey);
    
    if (savedChat) {
        try {
            const chatData = JSON.parse(savedChat);
            
            // Восстанавливаем существующий чат
            currentModuleChatId = chatData.chat_id;
            
            // Валидируем и очищаем сообщения
            let validMessages = [];
            if (Array.isArray(chatData.messages)) {
                validMessages = chatData.messages.filter(message => {
                    // Проверяем что сообщение корректное
                    return message && 
                           typeof message === 'object' && 
                           (message.sender || message.sender_type) &&
                           (message.content || message.message_content);
                });
            }
            
            moduleChatMessages = validMessages;
            
            console.log('Restored existing module chat:', currentModuleChatId, 'with', moduleChatMessages.length, 'valid messages');
            
            // Отображаем сохраненный конспект и чат
            if (moduleChatMessages.length > 0) {
                const firstMessage = moduleChatMessages[0];
                if (firstMessage.isConspect || (firstMessage.sender === 'ai' && firstMessage.content)) {
                    displayModuleConspect(firstMessage.content);
                }
            }
            
            // Загружаем сообщения в интерфейс
            loadModuleChatMessages();
            
            // Показываем индикатор если есть сообщения в чате
            if (moduleChatMessages.length > 1) {
                const chatIndicator = document.getElementById('chat-indicator');
                if (chatIndicator) {
                    chatIndicator.style.display = 'inline-block';
                }
            }
            
            showSuccessMessage('📖 Модуль восстановлен! Продолжайте изучение.');
            return;
            
        } catch (error) {
            console.error('Error restoring module chat:', error);
            // Очищаем поврежденные данные
            localStorage.removeItem(existingChatKey);
            moduleChatMessages = [];
            // Если не удалось восстановить, генерируем новый
        }
    }
    
    // Если нет сохраненного чата, начинаем генерацию конспекта
    await startModuleLearning();
}

function fillModuleLearningInfo(track, module) {
    // Заполняем информацию о треке и модуле
    const elements = {
        'learning-track-title': track.title,
        'learning-module-title': `Модуль ${module.module_number || 1}`,
        'learning-module-name': module.title || `Модуль ${module.module_number || 1}`,
        'learning-module-description': module.description || 'Описание модуля',
        'learning-progress-text': (module.progress || 0) + '%'
    };
    
    Object.keys(elements).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = elements[id];
        }
    });
    
    // Обновляем прогресс
    const progressFill = document.getElementById('learning-progress-fill');
    if (progressFill) {
        progressFill.style.width = (module.progress || 0) + '%';
    }
}

async function startModuleLearning() {
    if (!currentLearningModule) return;
    
    try {
        // Показываем загрузку конспекта
        const conspectContent = document.getElementById('module-conspect-content');
        if (conspectContent) {
            conspectContent.innerHTML = `
                <div class="conspect-loading">
                    <div class="loading-spinner"></div>
                    <p>Генерируем конспект модуля...</p>
                </div>
            `;
        }
        
        // Подготавливаем ID в правильном формате
        let trackId = currentLearningModule.trackId;
        let moduleId = currentLearningModule.id || currentLearningModule.module_number || '1';
        
        // Проверяем и конвертируем ID в строковый формат
        if (typeof trackId === 'number') {
            trackId = trackId.toString();
        }
        if (typeof moduleId === 'number') {
            moduleId = moduleId.toString();
        }
        
        console.log('Starting module learning:', {
            trackId: trackId,
            moduleId: moduleId,
            trackTitle: currentLearningModule.trackTitle,
            moduleTitle: currentLearningModule.title
        });
        
        // Вызываем API для начала изучения модуля
        const response = await apiRequest(API_ENDPOINTS.ai.moduleStart, {
            method: 'POST',
            body: JSON.stringify({
                track_id: trackId,
                module_id: moduleId,
                session_id: moduleSessionId,
                user_id: currentUser ? currentUser.id : 'guest_' + generateId()
            })
        });
        
        if (response.success) {
            // Сохраняем chat_id модуля
            currentModuleChatId = response.chat_id;
            
            // Отображаем конспект
            displayModuleConspect(response.module_summary);
            
            // Инициализируем чат с конспектом
            initializeModuleChat(response.module_summary);
            
            // Обновляем статус модуля
            updateModuleProgress('in_progress', 10);
            
            showSuccessMessage('🎉 Модуль готов к изучению! Конспект сгенерирован.');
        } else {
            throw new Error(response.error || 'Ошибка генерации конспекта');
        }
        
    } catch (error) {
        console.error('Error starting module learning:', error);
        const conspectContent = document.getElementById('module-conspect-content');
        if (conspectContent) {
            conspectContent.innerHTML = `
                <div class="error-message">
                    <h3>❌ Ошибка генерации конспекта</h3>
                    <p>${error.message}</p>
                    <button class="btn btn--primary" onclick="startModuleLearning()">
                        🔄 Попробовать снова
                    </button>
                </div>
            `;
        }
        showErrorMessage('Ошибка при генерации конспекта: ' + error.message);
    }
}

function displayModuleConspect(conspectText) {
    const conspectContent = document.getElementById('module-conspect-content');
    if (!conspectContent) return;
    
    // Обрабатываем markdown и отображаем
    const htmlContent = safeMarkdown(conspectText);
    conspectContent.innerHTML = htmlContent;
    
    // Добавляем класс для стилизации
    conspectContent.classList.add('markdown-content');
}

function initializeModuleChat(conspectText) {
    // Инициализируем чат с конспектом как первым сообщением
    moduleChatMessages = [
        {
            sender: 'ai',
            content: conspectText,
            timestamp: new Date().toLocaleTimeString('ru-RU', {
                hour: '2-digit', 
                minute: '2-digit'
            }),
            isConspect: true
        }
    ];
    
    // Загружаем сообщения в интерфейс чата
    loadModuleChatMessages();
    
    // Показываем индикатор нового сообщения
    const chatIndicator = document.getElementById('chat-indicator');
    if (chatIndicator) {
        chatIndicator.style.display = 'inline-block';
    }
    
    // Сохраняем чат в localStorage
    saveModuleChat();
}

function setupModuleChatForm() {
    const form = document.getElementById('module-chat-form');
    if (form) {
        form.addEventListener('submit', handleModuleChatMessage);
    }
}

async function handleModuleChatMessage(e) {
    e.preventDefault();
    
    const input = document.getElementById('module-chat-message-input');
    const message = input.value.trim();
    
    if (!message || !currentModuleChatId) return;
    
    // Добавляем сообщение пользователя
    const userMessage = {
        sender: 'user',
        content: message,
        timestamp: new Date().toLocaleTimeString('ru-RU', {
            hour: '2-digit', 
            minute: '2-digit'
        })
    };
    
    moduleChatMessages.push(userMessage);
    input.value = '';
    loadModuleChatMessages();
    
    // Показываем индикатор загрузки
    const loadingMessage = {
        sender: 'ai',
        content: '⏳ Обрабатываю ваш вопрос...',
        timestamp: new Date().toLocaleTimeString('ru-RU', {
            hour: '2-digit', 
            minute: '2-digit'
        }),
        isLoading: true
    };
    
    moduleChatMessages.push(loadingMessage);
    loadModuleChatMessages();
    
    try {
        // Подготавливаем ID в правильном формате
        let trackId = currentLearningModule.trackId;
        let moduleId = currentLearningModule.id || currentLearningModule.module_number || '1';
        
        // Проверяем и конвертируем ID в строковый формат
        if (typeof trackId === 'number') {
            trackId = trackId.toString();
        }
        if (typeof moduleId === 'number') {
            moduleId = moduleId.toString();
        }
        
        // Отправляем сообщение через API
        const response = await apiRequest(API_ENDPOINTS.ai.moduleChat, {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                track_id: trackId,
                module_id: moduleId,
                session_id: moduleSessionId,
                user_id: currentUser ? currentUser.id : 'guest_' + generateId(),
                chat_id: currentModuleChatId
            })
        });
        
        // Убираем сообщение загрузки
        moduleChatMessages.pop();
        
        if (response.success) {
            // Добавляем ответ AI
            const aiMessage = {
                sender: 'ai',
                content: response.response,
                timestamp: new Date().toLocaleTimeString('ru-RU', {
                    hour: '2-digit', 
                    minute: '2-digit'
                }),
                tokens_used: response.tokens_used
            };
            
            moduleChatMessages.push(aiMessage);
            loadModuleChatMessages();
            
            // Сохраняем обновленный чат
            saveModuleChat();
        } else {
            throw new Error(response.error || 'Ошибка обработки сообщения');
        }
        
    } catch (error) {
        // Убираем сообщение загрузки
        moduleChatMessages.pop();
        
        console.error('Error sending module chat message:', error);
        const errorMessage = {
            sender: 'ai',
            content: `❌ Произошла ошибка: ${error.message}`,
            timestamp: new Date().toLocaleTimeString('ru-RU', {
                hour: '2-digit', 
                minute: '2-digit'
            }),
            isError: true
        };
        
        moduleChatMessages.push(errorMessage);
        loadModuleChatMessages();
    }
}

function loadModuleChatMessages() {
    const chatContainer = document.getElementById('module-chat-messages');
    if (!chatContainer) return;
    
    chatContainer.innerHTML = '';
    
    moduleChatMessages.forEach((message, index) => {
        // Безопасная проверка наличия сообщения
        if (!message || typeof message !== 'object') {
            console.warn('Invalid message at index:', index, message);
            return;
        }
        
        const messageDiv = document.createElement('div');
        
        // Безопасное определение отправителя
        let sender = 'user'; // значение по умолчанию
        if (message.sender && typeof message.sender === 'string') {
            sender = message.sender;
        } else if (message.sender_type && typeof message.sender_type === 'string') {
            sender = message.sender_type;
        }
        
        messageDiv.className = `module-chat-message ${sender}`;
        
        if (message.isConspect) messageDiv.classList.add('conspect');
        if (message.isLoading) messageDiv.classList.add('loading');
        if (message.isError) messageDiv.classList.add('error');
        
        // Безопасное получение контента
        let messageContent = '';
        if (message.content && typeof message.content === 'string') {
            messageContent = message.content;
        } else if (message.message_content && typeof message.message_content === 'string') {
            messageContent = message.message_content;
        }
        
        // Обрабатываем markdown для AI сообщений
        if ((sender === 'ai' || sender === 'assistant') && !message.isLoading && messageContent) {
            try {
                messageContent = safeMarkdown(messageContent);
            } catch (error) {
                console.error('Error processing markdown:', error);
                // Оставляем исходный текст при ошибке
            }
        }
        
        // Метаинформация
        let metaInfo = '';
        if (message.timestamp) {
            metaInfo += `<span class="timestamp">${message.timestamp}</span>`;
        }
        if (message.tokens_used && typeof message.tokens_used === 'number') {
            metaInfo += ` <span class="tokens">🔢 ${message.tokens_used} токенов</span>`;
        }
        
        messageDiv.innerHTML = `
            <div class="message-content">${messageContent}</div>
            <div class="message-meta">${metaInfo}</div>
        `;
        
        chatContainer.appendChild(messageDiv);
    });
    
    // Прокручиваем к последнему сообщению
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function switchLearningTab(tabName) {
    // Переключаем активные вкладки
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.learning-tab-content').forEach(content => content.classList.remove('active'));
    
    // Активируем выбранную вкладку
    const activeButton = event.target;
    const activeContent = document.getElementById(`learning-${tabName}-tab`);
    
    if (activeButton) activeButton.classList.add('active');
    if (activeContent) activeContent.classList.add('active');
    
    // Скрываем индикатор чата при переключении на чат
    if (tabName === 'chat') {
        const chatIndicator = document.getElementById('chat-indicator');
        if (chatIndicator) {
            chatIndicator.style.display = 'none';
        }
    }
}

function insertChatHint(hintText) {
    const input = document.getElementById('module-chat-message-input');
    if (input) {
        input.value = hintText;
        input.focus();
    }
}

async function completeModuleLearning() {
    if (!currentLearningModule) return;
    
    const confirmMessage = `Вы уверены, что хотите завершить изучение модуля "${currentLearningModule.title}"?\n\nЭто разблокирует следующий модуль курса.`;
    
    if (!confirm(confirmMessage)) return;
    
    const completeButton = document.getElementById('complete-module-btn');
    setButtonLoading(completeButton, true);
    
    try {
        // Подготавливаем ID в правильном формате
        let trackId = currentLearningModule.trackId;
        let moduleId = currentLearningModule.id || currentLearningModule.module_number || '1';
        
        // Проверяем и конвертируем ID в строковый формат
        if (typeof trackId === 'number') {
            trackId = trackId.toString();
        }
        if (typeof moduleId === 'number') {
            moduleId = moduleId.toString();
        }
        
        // Вызываем API для завершения модуля
        const response = await apiRequest(API_ENDPOINTS.ai.moduleComplete, {
            method: 'POST',
            body: JSON.stringify({
                track_id: trackId,
                module_id: moduleId,
                session_id: moduleSessionId,
                user_id: currentUser ? currentUser.id : 'guest_' + generateId()
            })
        });
        
        if (response.success) {
            // Обновляем прогресс модуля
            updateModuleProgress('completed', 100);
            
            // Обновляем треки в localStorage
            updateModuleInTracks('completed', 100);
            
            showSuccessMessage('🎉 Модуль успешно завершен! Следующий модуль разблокирован.');
            
            // Возвращаемся к деталям трека через 2 секунды
            setTimeout(() => {
                backToModuleDetail();
            }, 2000);
        } else {
            throw new Error(response.error || 'Ошибка завершения модуля');
        }
        
    } catch (error) {
        console.error('Error completing module:', error);
        showErrorMessage('Ошибка при завершении модуля: ' + error.message);
    } finally {
        setButtonLoading(completeButton, false);
    }
}

function updateModuleProgress(status, progress) {
    if (!currentLearningModule) return;
    
    // Обновляем прогресс в интерфейсе
    const progressText = document.getElementById('learning-progress-text');
    const progressFill = document.getElementById('learning-progress-fill');
    
    if (progressText) progressText.textContent = progress + '%';
    if (progressFill) progressFill.style.width = progress + '%';
    
    // Обновляем текущий модуль
    currentLearningModule.status = status;
    currentLearningModule.progress = progress;
}

function updateModuleInTracks(status, progress) {
    if (!currentLearningModule) return;
    
    // Найти и обновить модуль в треках
    const track = tracks.find(t => t.id === currentLearningModule.trackId);
    if (track && track.modules) {
        const module = track.modules.find(m => 
            (m.id || m.module_number) === (currentLearningModule.id || currentLearningModule.module_number)
        );
        
        if (module) {
            module.status = status;
            module.progress = progress;
            
            // Сохраняем в localStorage
            saveToStorage();
            
            console.log('Updated module in tracks:', module.title, status, progress + '%');
        }
    }
}

function backToModuleDetail() {
    if (currentLearningModule && currentTrack) {
        openModuleDetail(currentLearningModule.trackId, currentLearningModule.id || currentLearningModule.module_number);
    } else if (currentTrack) {
        openTrackDetail(currentTrack.id);
    } else {
        showPage('dashboard-page');
    }
}

function downloadModuleConspect() {
    if (!currentLearningModule) return;
    
    const conspectContent = document.getElementById('module-conspect-content');
    if (!conspectContent) return;
    
    // Получаем текст конспекта
    const conspectText = conspectContent.textContent || conspectContent.innerText;
    
    // Создаем и скачиваем файл
    const blob = new Blob([conspectText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    
    link.href = url;
    link.download = `${currentLearningModule.title}_конспект.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showSuccessMessage('📄 Конспект загружен!');
}

function toggleConspectFullscreen() {
    const conspectContainer = document.querySelector('.conspect-container');
    if (!conspectContainer) return;
    
    if (conspectContainer.classList.contains('fullscreen')) {
        conspectContainer.classList.remove('fullscreen');
        showSuccessMessage('Обычный режим просмотра');
    } else {
        conspectContainer.classList.add('fullscreen');
        showSuccessMessage('Полноэкранный режим');
    }
}

window.toggleProgressiveUnlock = toggleProgressiveUnlock;
window.toggleDebugMode = toggleDebugMode;
window.toggleAdaptiveLearning = toggleAdaptiveLearning;

// Новые функции для изучения модуля
window.switchLearningTab = switchLearningTab;
window.insertChatHint = insertChatHint;
window.completeModuleLearning = completeModuleLearning;
window.downloadModuleConspect = downloadModuleConspect;
window.toggleConspectFullscreen = toggleConspectFullscreen;
window.backToModuleDetail = backToModuleDetail;

function saveModuleChat() {
    if (!currentLearningModule || !currentModuleChatId || !moduleChatMessages.length) return;
    
    const chatKey = `module_chat_${currentLearningModule.trackId}_${currentLearningModule.id || currentLearningModule.module_number}`;
    const chatData = {
        chat_id: currentModuleChatId,
        track_id: currentLearningModule.trackId,
        module_id: currentLearningModule.id || currentLearningModule.module_number,
        module_title: currentLearningModule.title,
        track_title: currentLearningModule.trackTitle,
        messages: moduleChatMessages,
        last_updated: new Date().toISOString()
    };
    
    try {
        localStorage.setItem(chatKey, JSON.stringify(chatData));
        console.log('Module chat saved to localStorage:', chatKey);
    } catch (error) {
        console.error('Error saving module chat to localStorage:', error);
    }
}

// Test marked library
window.testMarked = function() {
    console.log('=== TESTING MARKED LIBRARY ===');
    console.log('typeof marked:', typeof marked);
    
    if (typeof marked !== 'undefined') {
        console.log('marked object:', marked);
        console.log('marked.parse:', typeof marked.parse);
        
        const testText = '# Test Heading\n\n**Bold text** and *italic text*\n\n- List item 1\n- List item 2';
        
        try {
            let result;
            if (typeof marked.parse === 'function') {
                result = marked.parse(testText);
            } else if (typeof marked === 'function') {
                result = marked(testText);
            }
            console.log('Marked test result:', result);
        } catch (error) {
            console.error('Marked test failed:', error);
        }
    } else {
        console.log('Marked not available, testing fallback...');
        const testText = '# Test Heading\n\n**Bold text** and *italic text*';
        const result = safeMarkdown(testText);
        console.log('Fallback test result:', result);
    }
    
    console.log('✅ Marked test completed');
};

// Debug function for module chat messages
window.debugModuleChat = function() {
    console.log('=== DEBUG MODULE CHAT ===');
    console.log('currentLearningModule:', currentLearningModule);
    console.log('currentModuleChatId:', currentModuleChatId);
    console.log('moduleChatMessages length:', moduleChatMessages.length);
    
    moduleChatMessages.forEach((message, index) => {
        console.log(`Message ${index}:`, {
            sender: message.sender,
            sender_type: message.sender_type,
            content: message.content ? message.content.substring(0, 50) + '...' : 'no content',
            message_content: message.message_content ? message.message_content.substring(0, 50) + '...' : 'no message_content',
            timestamp: message.timestamp,
            isConspect: message.isConspect,
            isLoading: message.isLoading,
            isError: message.isError
        });
    });
    
    console.log('✅ Module chat debug completed');
};