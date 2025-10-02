import { apiCall } from '../client';
import { API_ENDPOINTS } from '../endpoints';
import type { CharactersResponse, Character } from '../types';

export const characterService = {
  /**
   * Get all characters across all scripts
   */
  async getAllCharacters(signal?: AbortSignal): Promise<CharactersResponse> {
    return apiCall<CharactersResponse>(API_ENDPOINTS.getAllCharacters(), { signal });
  },

  /**
   * Get characters for a specific script
   */
  async getCharacters(key: string, signal?: AbortSignal): Promise<CharactersResponse> {
    return apiCall<CharactersResponse>(API_ENDPOINTS.getCharacters(key), { signal });
  },

  /**
   * Get character detail by ID
   */
  async getCharacter(id: string | number, signal?: AbortSignal): Promise<Character> {
    return apiCall<Character>(API_ENDPOINTS.getCharacter(id), { signal });
  },

  /**
   * Update character prompt
   */
  async updateCharacterPrompt(id: string | number, imagePrompt: string, signal?: AbortSignal): Promise<{ character_id: number }> {
    return apiCall<{ character_id: number }>(
      API_ENDPOINTS.updateCharacterPrompt(id),
      {
        method: 'PUT',
        body: JSON.stringify({ image_prompt: imagePrompt }),
        signal,
      }
    );
  },

  /**
   * Generate character image
   */
  async generateCharacterImage(
    id: string | number,
    imagePrompt: string,
    signal?: AbortSignal
  ): Promise<{ character_id: number; image_url: string; local_path: string }> {
    return apiCall<{ character_id: number; image_url: string; local_path: string }>(
      API_ENDPOINTS.generateCharacterImage(id),
      {
        method: 'POST',
        body: JSON.stringify({ image_prompt: imagePrompt }),
        signal,
      }
    );
  },
};
