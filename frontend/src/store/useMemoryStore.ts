import { create } from "zustand";

export interface EpisodeMemory {
  id: number;
  script_name: string;
  episode_number: number;
  plot_summary: string;
  options: Record<string, unknown>;
  created_at: string;
}

interface MemoryStore {
  // Memory cache by scriptKey
  memories: Map<string, EpisodeMemory>;

  // Get memory by scriptKey
  getMemory: (scriptKey: string) => EpisodeMemory | undefined;

  // Set memory for a scriptKey
  setMemory: (scriptKey: string, memory: EpisodeMemory) => void;

  // Clear all cache
  clearAll: () => void;

  // Clear specific scriptKey cache
  clearMemory: (scriptKey: string) => void;
}

export const useMemoryStore = create<MemoryStore>((set, get) => ({
  memories: new Map(),

  getMemory: (scriptKey) => {
    return get().memories.get(scriptKey);
  },

  setMemory: (scriptKey, memory) => {
    set((state) => {
      const newMemories = new Map(state.memories);
      newMemories.set(scriptKey, memory);
      return { memories: newMemories };
    });
  },

  clearMemory: (scriptKey) => {
    set((state) => {
      const newMemories = new Map(state.memories);
      newMemories.delete(scriptKey);
      return { memories: newMemories };
    });
  },

  clearAll: () => {
    set({ memories: new Map() });
  },
}));
