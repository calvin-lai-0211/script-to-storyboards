import { create } from "zustand";
import { CharacterData } from "./types";

interface CharacterStore {
  // Current character context
  currentCharacter: CharacterData | null;
  setCurrentCharacter: (character: CharacterData) => void;

  // All characters list cache
  allCharacters: CharacterData[] | null;
  setAllCharacters: (data: CharacterData[]) => void;

  // Update a single character in the list
  updateCharacter: (id: number, updates: Partial<CharacterData>) => void;

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

  updateCharacter: (id, updates) => {
    set((state) => ({
      allCharacters: state.allCharacters
        ? state.allCharacters.map((char) =>
            char.id === id ? { ...char, ...updates } : char
          )
        : null,
    }));
  },

  clearAll: () => {
    set({
      currentCharacter: null,
      allCharacters: null,
    });
  },
}));
