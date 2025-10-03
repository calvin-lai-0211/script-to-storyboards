import { API_BASE_URL } from "./client";

export const API_ENDPOINTS = {
  // Character endpoints
  getCharacter: (id: string | number) => `${API_BASE_URL}/api/character/${id}`,
  updateCharacterPrompt: (id: string | number) =>
    `${API_BASE_URL}/api/character/${id}/prompt`,
  generateCharacterImage: (id: string | number) =>
    `${API_BASE_URL}/api/character/${id}/generate-image`,

  // Storyboard endpoints
  generateStoryboard: () => `${API_BASE_URL}/api/storyboard/generate`,

  // Characters list endpoints
  getAllCharacters: () => `${API_BASE_URL}/api/characters/all`,
  getCharacters: (key: string) =>
    `${API_BASE_URL}/api/characters/${encodeURIComponent(key)}`,
  generateCharacters: () => `${API_BASE_URL}/api/characters/generate`,

  // Scenes endpoints
  getAllScenes: () => `${API_BASE_URL}/api/scenes/all`,
  getScene: (id: string | number) => `${API_BASE_URL}/api/scene/${id}`,
  getScenes: (key: string) =>
    `${API_BASE_URL}/api/scenes/${encodeURIComponent(key)}`,
  generateScenes: () => `${API_BASE_URL}/api/scenes/generate`,

  // Props endpoints
  getAllProps: () => `${API_BASE_URL}/api/props/all`,
  getProp: (id: string | number) => `${API_BASE_URL}/api/prop/${id}`,
  generateProps: () => `${API_BASE_URL}/api/props/generate`,

  // Scripts endpoints
  getAllScripts: () => `${API_BASE_URL}/api/scripts`,
  getScript: (key: string) =>
    `${API_BASE_URL}/api/scripts/${encodeURIComponent(key)}`,

  // Storyboards endpoints
  getStoryboards: (key: string) =>
    `${API_BASE_URL}/api/storyboards/${encodeURIComponent(key)}`,

  // Memory endpoints
  getEpisodeMemory: (key: string) =>
    `${API_BASE_URL}/api/memory/${encodeURIComponent(key)}`,
};
