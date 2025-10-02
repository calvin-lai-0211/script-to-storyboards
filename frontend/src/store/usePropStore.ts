import { create } from 'zustand';
import { PropData } from './types';

interface PropStore {
  // Current prop context
  currentProp: PropData | null;
  setCurrentProp: (prop: PropData) => void;

  // All props list cache
  allProps: PropData[] | null;
  setAllProps: (data: PropData[]) => void;

  // Clear all cache
  clearAll: () => void;
}

export const usePropStore = create<PropStore>((set) => ({
  currentProp: null,

  setCurrentProp: (prop) => {
    set({ currentProp: prop });
  },

  allProps: null,

  setAllProps: (data) => {
    set({ allProps: data });
  },

  clearAll: () => {
    set({
      currentProp: null,
      allProps: null,
    });
  },
}));
