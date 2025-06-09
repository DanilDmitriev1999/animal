import { pages } from './dom.js';
import { state } from './state.js';

export function showPage(pageName) {
  // Hide all pages
  Object.values(pages).forEach(page => {
    if (page) {
      page.classList.remove('active');
    }
  });

  // Show selected page
  if (pages[pageName]) {
    pages[pageName].classList.add('active');
    pages[pageName].classList.add('fade-in');
  }

  state.setCurrentPage(pageName);
}

export function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
  }
}

export function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

export function closeAllModals() {
  const modals = document.querySelectorAll('.modal-overlay');
  modals.forEach(modal => {
    modal.classList.remove('active');
  });
}

export function smoothScrollTo(element) {
  element.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
  });
}

export function observeElements() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.track-card, .module-item, .chat-bubble').forEach(el => {
        observer.observe(el);
    });
} 