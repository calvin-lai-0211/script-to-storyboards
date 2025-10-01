/**
 * API Configuration
 */

// API Base URL
// Use ?? instead of || to allow empty string for K8s deployment
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

// API Endpoints
export const API_ENDPOINTS = {
  // Character endpoints
  getCharacter: (id: string | number) => `${API_BASE_URL}/api/character/${id}`,
  updateCharacterPrompt: (id: string | number) => `${API_BASE_URL}/api/character/${id}/prompt`,

  // Storyboard endpoints
  generateStoryboard: () => `${API_BASE_URL}/api/storyboard/generate`,

  // Characters list endpoints
  getCharacters: (dramaName: string, episodeNumber: number) =>
    `${API_BASE_URL}/api/characters/${dramaName}/${episodeNumber}`,
  generateCharacters: () => `${API_BASE_URL}/api/characters/generate`,

  // Scenes endpoints
  getScenes: (dramaName: string, episodeNumber: number) =>
    `${API_BASE_URL}/api/scenes/${dramaName}/${episodeNumber}`,
  generateScenes: () => `${API_BASE_URL}/api/scenes/generate`,

  // Props endpoints
  generateProps: () => `${API_BASE_URL}/api/props/generate`,

  // Scripts endpoints
  listEpisodes: (scriptTitle: string) => `${API_BASE_URL}/api/scripts/${scriptTitle}/episodes`,
};

// Helper function for API calls
export const apiCall = async (url: string, options?: RequestInit) => {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};