import { appData } from './data.js';
import { state } from './state.js';
import { elements } from './dom.js';
import { showPage } from './ui.js';

export function renderTracks() {
  if (elements.tracksGrid) {
    elements.tracksGrid.innerHTML = '';
    // Получаем email пользователя из localStorage
    const userEmail = localStorage.getItem('user_email');
    let tracksToShow = [];
    if (userEmail === 'test@example.com') {
      tracksToShow = appData.tracks;
    } else {
      tracksToShow = [];
    }
    tracksToShow.forEach(track => {
      const trackCard = createTrackCard(track);
      elements.tracksGrid.appendChild(trackCard);
    });
  }
}

function createTrackCard(track) {
  const card = document.createElement('div');
  card.className = 'track-card glass-card';
  card.innerHTML = `
    <div class="track-header">
      <div class="track-title-card">${track.title}</div>
    </div>
    <div class="track-description">${track.description}</div>
    <div class="track-meta">
      <span>${track.modules} modules</span>
      <div class="track-tags">
        ${track.tags.map(tag => `<span class="track-tag">${tag}</span>`).join('')}
      </div>
    </div>
    <div class="track-progress">
      <div class="progress-label">
        <span>Прогресс</span>
        <span>${track.progress}% complete</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" style="width: ${track.progress}%"></div>
      </div>
    </div>
  `;
  card.addEventListener('click', () => openTrack(track));
  return card;
}

function openTrack(track) {
  state.setCurrentTrack(track);
  showPage('trackPage');
  updateTrackPageContent();
}

export function updateTrackPageContent() {
  const track = state.currentTrack;
  if (track && elements.trackTitle) {
    elements.trackTitle.textContent = track.title;
    elements.progressInfo.textContent = `Overall Progress: ${track.progress}%`;
    renderModulesList();
    
    const lesson = appData.current_lesson;
    elements.lessonTitle.textContent = lesson.title;
    elements.lessonContent.textContent = lesson.content;
    
    if (elements.codeExample) {
      elements.codeExample.textContent = lesson.code_example;
      // Note: In a real app, you'd use a syntax highlighter here
    }
  }
}

function renderModulesList() {
  const track = state.currentTrack;
  if (track && elements.modulesList) {
    elements.modulesList.innerHTML = '';
    track.modules_list.forEach(module => {
      const moduleItem = document.createElement('li');
      moduleItem.className = 'module-item';
      if (module.completed) {
        moduleItem.classList.add('completed');
      }
      moduleItem.innerHTML = `
        <span class="module-status">${module.completed ? '✓' : '○'}</span>
        <span class="module-title">${module.title}</span>
        <span class="module-progress">${module.progress}%</span>
      `;
      moduleItem.addEventListener('click', () => selectModule(module, moduleItem));
      elements.modulesList.appendChild(moduleItem);
    });
  }
}

function selectModule(module, element) {
  // Deselect others
  document.querySelectorAll('.module-item.active').forEach(item => {
    item.classList.remove('active');
  });
  
  // Select current
  element.classList.add('active');
  
  // Update lesson content (mock)
  elements.lessonTitle.textContent = module.title;
  elements.lessonContent.textContent = `Content for ${module.title} goes here.`;
  elements.codeExample.textContent = `// Code for ${module.title}`;
}

export function switchPracticeTab(mode) {
  // Update active tab
  document.querySelectorAll('.practice-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.mode === mode);
  });
  
  // Update content
  const practiceMode = appData.practice_modes.find(m => m.id === mode);
  if (practiceMode && elements.practiceContent) {
    elements.practiceContent.innerHTML = `
      <h4>${practiceMode.title}</h4>
      <p>${practiceMode.description}</p>
      <p>Interactive content for ${mode} would appear here.</p>
    `;
  }
} 