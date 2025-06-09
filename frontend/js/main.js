import { elements } from './dom.js';
import { showPage, openModal, closeModal, closeAllModals } from './ui.js';
import { renderTracks, switchPracticeTab } from './track.js';
import { 
  renderChatMessages, 
  openChatModal, 
  closeChatModal, 
  handleChatKeypress, 
  sendChatMessage, 
  handleOverlayChatKeypress,
  toggleMicrophone
} from './chat.js';

// Импортируем стили для Vite
import '../style.css';

document.addEventListener('DOMContentLoaded', function() {
  initializeApp();
  setupEventListeners();
  renderTracks();
  renderChatMessages();
});

function initializeApp() {
  // Set initial page
  showPage('dashboard');
  
  // Add fade-in animation to elements
  document.body.classList.add('fade-in');
  
  // Focus management
  if (elements.chatInput) {
    elements.chatInput.focus();
  }
}

function setupEventListeners() {
  // Navigation
  if (elements.backButton) {
    elements.backButton.addEventListener('click', () => showPage('dashboard'));
  }

  // Chat functionality - Bottom chat bar
  if (elements.chatInput) {
    // Open overlay chat when clicking on bottom input
    elements.chatInput.addEventListener('click', (e) => {
      e.preventDefault();
      openChatModal();
    });
    
    // Prevent typing in bottom input (it's just for show)
    elements.chatInput.addEventListener('keydown', (e) => {
      e.preventDefault();
      openChatModal();
    });
  }

  // Track page bottom chat (same behavior)
  const trackChatInput = document.querySelector('#trackChatBar .chat-input');
  if (trackChatInput) {
    trackChatInput.addEventListener('click', (e) => {
      e.preventDefault();
      openChatModal();
    });
    
    trackChatInput.addEventListener('keydown', (e) => {
      e.preventDefault();
      openChatModal();
    });
  }

  if (elements.micButton) {
    elements.micButton.addEventListener('click', openChatModal);
  }

  if (elements.closeChatModal) {
    elements.closeChatModal.addEventListener('click', closeChatModal);
  }

  if (elements.sendMessage) {
    elements.sendMessage.addEventListener('click', sendChatMessage);
  }

  // Overlay chat input (actual functioning input)
  if (elements.chatMessageInput) {
    elements.chatMessageInput.addEventListener('keypress', handleOverlayChatKeypress);
  }

  // Practice tabs
  const practiceTabs = document.querySelectorAll('.practice-tab');
  practiceTabs.forEach(tab => {
    tab.addEventListener('click', () => switchPracticeTab(tab.dataset.mode));
  });

  // Modal functionality
  if (elements.conspectButton) {
    elements.conspectButton.addEventListener('click', () => openModal('conspectModal'));
  }

  if (elements.closeConspect) {
    elements.closeConspect.addEventListener('click', () => closeModal('conspectModal'));
  }

  if (elements.commandPaletteButton) {
    elements.commandPaletteButton.addEventListener('click', () => openModal('commandPalette'));
  }

  // Profile modal functionality
  if (elements.profileAvatar) {
    elements.profileAvatar.addEventListener('click', () => openModal('profileModal'));
  }

  if (elements.closeProfile) {
    elements.closeProfile.addEventListener('click', () => closeModal('profileModal'));
  }

  // Click outside to close modals and chat
  document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
      closeAllModals();
      if (e.target.id === 'chatModal') {
        closeChatModal();
      }
    }
  });

  // Command palette keyboard shortcut
  document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      openModal('commandPalette');
    }
    
    if (e.key === 'Escape') {
      closeAllModals();
      closeChatModal();
    }
  });

  // Command list interaction
  const commandItems = document.querySelectorAll('.command-item');
  commandItems.forEach(item => {
    item.addEventListener('click', handleCommandSelection);
  });
}

function handleCommandSelection(e) {
  const action = e.currentTarget.dataset.action;
  if (action) {
    console.log(`Command selected: ${action}`);
    closeAllModals();
    
    switch(action) {
      case 'navigate-dashboard':
        showPage('dashboard');
        break;
      case 'open-track-1':
        // This is a simplified example. In a real app, you'd have a more robust way
        // to handle track opening from the command palette.
        console.log('Opening track 1...');
        break;
      case 'toggle-theme':
        document.body.classList.toggle('dark-theme');
        break;
    }
  }
} 