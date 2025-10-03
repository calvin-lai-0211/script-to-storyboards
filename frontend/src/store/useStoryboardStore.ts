import { create } from "zustand";

export interface SubShot {
  id: number;
  sub_shot_number: string;
  camera_angle: string;
  characters: string[];
  scene_context: string[];
  key_props: string[];
  image_prompt: string;
  dialogue_sound: string;
  duration_seconds: number;
  notes: string;
}

export interface Shot {
  shot_number: string;
  shot_description: string;
  subShots: SubShot[];
}

export interface Scene {
  scene_number: string;
  scene_description: string;
  shots: Shot[];
}

interface StoryboardStore {
  // Storyboard cache by scriptKey
  storyboards: Map<string, Scene[]>;

  // Get storyboard by scriptKey
  getStoryboard: (scriptKey: string) => Scene[] | undefined;

  // Set storyboard for a scriptKey
  setStoryboard: (scriptKey: string, scenes: Scene[]) => void;

  // Clear all cache
  clearAll: () => void;

  // Clear specific scriptKey cache
  clearStoryboard: (scriptKey: string) => void;
}

export const useStoryboardStore = create<StoryboardStore>((set, get) => ({
  storyboards: new Map(),

  getStoryboard: (scriptKey) => {
    return get().storyboards.get(scriptKey);
  },

  setStoryboard: (scriptKey, scenes) => {
    set((state) => {
      const newStoryboards = new Map(state.storyboards);
      newStoryboards.set(scriptKey, scenes);
      return { storyboards: newStoryboards };
    });
  },

  clearStoryboard: (scriptKey) => {
    set((state) => {
      const newStoryboards = new Map(state.storyboards);
      newStoryboards.delete(scriptKey);
      return { storyboards: newStoryboards };
    });
  },

  clearAll: () => {
    set({ storyboards: new Map() });
  },
}));
