import { elements } from './dom.js';

// Chat messages storage with limit
let chatMessages = [];
const MAX_MESSAGES = 10;

export function renderChatMessages() {
  if (elements.chatMessages) {
    elements.chatMessages.innerHTML = '';
    
    // Show only last 10 messages
    const displayMessages = chatMessages.slice(-MAX_MESSAGES);
    
    displayMessages.forEach(message => {
      const messageElement = createMessageElement(message);
      elements.chatMessages.appendChild(messageElement);
    });
    
    // Scroll to bottom
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }
}

function createMessageElement(message) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `chat-message ${message.sender}`;
  
  const avatarDiv = document.createElement('div');
  avatarDiv.className = `message-avatar ${message.sender === 'user' ? 'user' : ''}`;
  avatarDiv.textContent = message.sender === 'user' ? '👤' : '🤖';
  
  const contentDiv = document.createElement('div');
  contentDiv.className = `message-content ${message.sender === 'user' ? 'user' : ''}`;
  
  const textDiv = document.createElement('div');
  textDiv.className = 'message-text';
  textDiv.textContent = message.message;
  
  const timeDiv = document.createElement('div');
  timeDiv.className = 'message-time';
  timeDiv.textContent = message.timestamp || getCurrentTime();
  
  contentDiv.appendChild(textDiv);
  contentDiv.appendChild(timeDiv);
  
  messageDiv.appendChild(avatarDiv);
  messageDiv.appendChild(contentDiv);
  
  return messageDiv;
}

function getCurrentTime() {
  const now = new Date();
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
}

export function openChatModal() {
  if (elements.chatModal) {
    elements.chatModal.classList.add('active');
    elements.chatModal.classList.add('fade-in');
    
    // Focus on input
    if (elements.chatMessageInput) {
      setTimeout(() => {
        elements.chatMessageInput.focus();
      }, 100);
    }
    
    // Load initial messages if empty
    if (chatMessages.length === 0) {
      loadInitialMessages();
    }
    
    renderChatMessages();
  }
}

export function closeChatModal() {
  if (elements.chatModal) {
    elements.chatModal.classList.remove('active');
    elements.chatModal.classList.remove('fade-in');
  }
}

function loadInitialMessages() {
  chatMessages = [
    {
      id: 1,
      sender: 'bot',
      message: 'Привет! Я ваш AI-наставник. Готовы изучать JavaScript объекты?',
      timestamp: '10:30'
    },
    {
      id: 2,
      sender: 'user',
      message: 'Да, давайте начнем!',
      timestamp: '10:31'
    },
    {
      id: 3,
      sender: 'bot',
      message: 'Отлично! Объекты в JavaScript - это основа для понимания современного программирования. Начнем с простого примера.',
      timestamp: '10:31'
    }
  ];
}

export function sendChatMessage() {
  if (!elements.chatMessageInput) return;
  
  const messageText = elements.chatMessageInput.value.trim();
  if (!messageText) return;
  
  // Add user message
  const userMessage = {
    id: Date.now(),
    sender: 'user',
    message: messageText,
    timestamp: getCurrentTime()
  };
  
  chatMessages.push(userMessage);
  
  // Clear input
  elements.chatMessageInput.value = '';
  
  // Show typing indicator
  showTypingIndicator();
  
  // Simulate AI response
  setTimeout(() => {
    hideTypingIndicator();
    
    const aiResponse = {
      id: Date.now() + 1,
      sender: 'bot',
      message: generateAIResponse(messageText),
      timestamp: getCurrentTime()
    };
    
    chatMessages.push(aiResponse);
    
    // Keep only last MAX_MESSAGES
    if (chatMessages.length > MAX_MESSAGES) {
      chatMessages = chatMessages.slice(-MAX_MESSAGES);
    }
    
    renderChatMessages();
  }, 1500);
  
  renderChatMessages();
}

function generateAIResponse(userMessage) {
  const responses = [
    'Отличный вопрос! Давайте разберем это пошагово.',
    'Понимаю вашу задачу. Вот как это можно решить...',
    'Это важная тема в программировании. Позвольте объяснить...',
    'Хороший пример! Вот что происходит в коде...',
    'Давайте попробуем другой подход к этой задаче.',
    'Вы на правильном пути! Продолжайте в том же духе.',
    'Интересное наблюдение. Рассмотрим это подробнее...',
    'Отлично! Теперь попробуйте применить это на практике.'
  ];
  
  return responses[Math.floor(Math.random() * responses.length)];
}

function showTypingIndicator() {
  if (elements.typingIndicator) {
    elements.typingIndicator.classList.add('active');
  }
}

function hideTypingIndicator() {
  if (elements.typingIndicator) {
    elements.typingIndicator.classList.remove('active');
  }
}

export function handleChatKeypress(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChatMessage();
  }
}

export function handleOverlayChatKeypress(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChatMessage();
  }
}

// Deprecated function names for compatibility
export function expandChatPanel() {
  openChatModal();
}

export function closeChatPanel() {
  closeChatModal();
}

export function toggleMicrophone() {
  console.log('Microphone feature not implemented yet');
} 