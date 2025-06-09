import { appData } from './data.js';

let currentTrack = null;
let currentPage = 'dashboard';
let chatMessages = [...appData.chat_messages];

export const state = {
  get currentTrack() {
    return currentTrack;
  },
  get currentPage() {
    return currentPage;
  },
  get chatMessages() {
    return chatMessages;
  },
  setCurrentTrack(track) {
    currentTrack = track;
  },
  setCurrentPage(page) {
    currentPage = page;
  },
  setChatMessages(messages) {
    chatMessages = messages;
  },
  addChatMessage(message) {
    chatMessages.push(message);
  }
}; 