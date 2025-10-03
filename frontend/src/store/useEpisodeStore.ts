import { create } from "zustand";
import { EpisodeData, StoryboardData, MemoryData, ScriptData } from "./types";

interface EpisodeStore {
  // Current episode context (可以是部分数据，因为不同页面可能只有部分信息)
  currentEpisode: Partial<EpisodeData> | null;
  setCurrentEpisode: (episode: Partial<EpisodeData>) => void;

  // Data cache by key (per episode)
  episodes: Record<string, EpisodeData>;
  storyboards: Record<string, StoryboardData>;
  memories: Record<string, MemoryData>;

  // Global list caches
  allEpisodes: ScriptData[] | null;

  // Actions
  setEpisode: (key: string, data: EpisodeData) => void;
  setStoryboard: (key: string, data: StoryboardData) => void;
  setMemory: (key: string, data: MemoryData) => void;
  setAllEpisodes: (data: ScriptData[]) => void;

  getEpisode: (key: string) => EpisodeData | undefined;
  getStoryboard: (key: string) => StoryboardData | undefined;
  getMemory: (key: string) => MemoryData | undefined;

  clearKey: (key: string) => void;
  clearAll: () => void;
}

export const useEpisodeStore = create<EpisodeStore>((set, get) => ({
  currentEpisode: null,

  setCurrentEpisode: (episode) => {
    set({ currentEpisode: episode });
  },

  episodes: {},
  storyboards: {},
  memories: {},

  allEpisodes: null,

  setEpisode: (key, data) => {
    set((state) => ({
      episodes: { ...state.episodes, [key]: data },
    }));
  },

  setStoryboard: (key, data) => {
    set((state) => ({
      storyboards: { ...state.storyboards, [key]: data },
    }));
  },

  setMemory: (key, data) => {
    set((state) => ({
      memories: { ...state.memories, [key]: data },
    }));
  },

  setAllEpisodes: (data) => {
    set({ allEpisodes: data });
  },

  getEpisode: (key) => {
    return get().episodes[key];
  },

  getStoryboard: (key) => {
    return get().storyboards[key];
  },

  getMemory: (key) => {
    return get().memories[key];
  },

  clearKey: (key) => {
    set((state) => {
      const newState = { ...state };
      delete newState.episodes[key];
      delete newState.storyboards[key];
      delete newState.memories[key];
      return newState;
    });
  },

  clearAll: () => {
    set({
      currentEpisode: null,
      episodes: {},
      storyboards: {},
      memories: {},
      allEpisodes: null,
    });
  },
}));
