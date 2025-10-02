import { create } from 'zustand';
import { CharacterData } from './types';

interface CharacterStore {
  // Current character context
  currentCharacter: CharacterData | null;
  setCurrentCharacter: (character: CharacterData) => void;

  // All characters list cache
  allCharacters: CharacterData[] | null;
  setAllCharacters: (data: CharacterData[]) => void;

  // Clear all cache
  clearAll: () => void;
}

export const useCharacterStore = create<CharacterStore>((set) => ({
  currentCharacter: null,

  setCurrentCharacter: (character) => {
    set({ currentCharacter: character });
  },

  allCharacters: null,

  setAllCharacters: (data) => {
    set({ allCharacters: data });
  },

  clearAll: () => {
    set({
      currentCharacter: null,
      allCharacters: null,
    });
  },
}));
