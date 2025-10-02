import { describe, it, expect, beforeEach } from 'vitest';
import { useCharacterStore } from '../useCharacterStore';
import type { CharacterData } from '../types';

describe('useCharacterStore', () => {
  beforeEach(() => {
    useCharacterStore.getState().clearAll();
  });

  describe('currentCharacter', () => {
    it('should initialize with null currentCharacter', () => {
      const { currentCharacter } = useCharacterStore.getState();
      expect(currentCharacter).toBeNull();
    });

    it('should set and get currentCharacter', () => {
      const mockCharacter: CharacterData = {
        id: 1,
        character_name: 'Test Character',
        drama_name: 'Test Drama',
        episode_number: 1,
        image_url: null,
        image_prompt: 'Test prompt',
        is_key_character: false,
      };

      useCharacterStore.getState().setCurrentCharacter(mockCharacter);
      const { currentCharacter } = useCharacterStore.getState();

      expect(currentCharacter).toEqual(mockCharacter);
    });
  });

  describe('allCharacters', () => {
    it('should initialize with null allCharacters', () => {
      const { allCharacters } = useCharacterStore.getState();
      expect(allCharacters).toBeNull();
    });

    it('should set and get allCharacters list', () => {
      const mockCharacters: CharacterData[] = [
        {
          id: 1,
          character_name: 'Char 1',
          drama_name: 'Drama 1',
          episode_number: 1,
          image_url: null,
          image_prompt: 'Prompt 1',
          is_key_character: true,
        },
        {
          id: 2,
          character_name: 'Char 2',
          drama_name: 'Drama 1',
          episode_number: 1,
          image_url: null,
          image_prompt: 'Prompt 2',
          is_key_character: false,
        },
      ];

      useCharacterStore.getState().setAllCharacters(mockCharacters);
      const { allCharacters } = useCharacterStore.getState();

      expect(allCharacters).toEqual(mockCharacters);
      expect(allCharacters).toHaveLength(2);
    });
  });

  describe('clearAll', () => {
    it('should clear all store data', () => {
      const mockCharacter: CharacterData = {
        id: 1,
        character_name: 'Character',
        drama_name: 'Drama',
        episode_number: 1,
        image_url: null,
        image_prompt: 'Prompt',
        is_key_character: false,
      };

      useCharacterStore.getState().setCurrentCharacter(mockCharacter);
      useCharacterStore.getState().setAllCharacters([mockCharacter]);

      useCharacterStore.getState().clearAll();

      const state = useCharacterStore.getState();
      expect(state.currentCharacter).toBeNull();
      expect(state.allCharacters).toBeNull();
    });
  });
});
