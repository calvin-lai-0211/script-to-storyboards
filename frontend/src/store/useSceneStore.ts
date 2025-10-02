import { create } from 'zustand';
import { SceneData } from './types';

interface SceneStore {
  // Current scene context
  currentScene: SceneData | null;
  setCurrentScene: (scene: SceneData) => void;

  // All scenes list cache
  allScenes: SceneData[] | null;
  setAllScenes: (data: SceneData[]) => void;

  // Clear all cache
  clearAll: () => void;
}

export const useSceneStore = create<SceneStore>((set) => ({
  currentScene: null,

  setCurrentScene: (scene) => {
    set({ currentScene: scene });
  },

  allScenes: null,

  setAllScenes: (data) => {
    set({ allScenes: data });
  },

  clearAll: () => {
    set({
      currentScene: null,
      allScenes: null,
    });
  },
}));
