/**
 * API Configuration
 */

// API Base URL
// Use ?? instead of || to allow empty string for K8s deployment
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// API Endpoints
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
  getScenes: (key: string) =>
    `${API_BASE_URL}/api/scenes/${encodeURIComponent(key)}`,
  generateScenes: () => `${API_BASE_URL}/api/scenes/generate`,

  // Props endpoints
  getAllProps: () => `${API_BASE_URL}/api/props/all`,
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

// API Response type
export interface ApiResponse<T = unknown> {
  code: number;
  data: T | null;
  message: string;
}

// Helper function for API calls
export const apiCall = async <T = unknown>(
  url: string,
  options?: RequestInit,
): Promise<T> => {
  console.debug("API call:", url);
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  const result: ApiResponse<T> = await response.json();

  // Check if API returned error (code !== 0)
  if (result.code !== 0) {
    throw new Error(result.message || `API error! code: ${result.code}`);
  }

  // Return the data field
  return result.data as T;
};
