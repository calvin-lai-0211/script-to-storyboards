import { create } from 'zustand'
import { SceneData } from './types'

interface SceneStore {
  // Current scene context
  currentScene: SceneData | null
  setCurrentScene: (scene: SceneData) => void

  // All scenes list cache
  allScenes: SceneData[] | null
  setAllScenes: (data: SceneData[]) => void

  // Update scene (partial update)
  updateScene: (id: number, updates: Partial<SceneData>) => void

  // Clear all cache
  clearAll: () => void
}

export const useSceneStore = create<SceneStore>((set) => ({
  currentScene: null,

  setCurrentScene: (scene) => {
    set({ currentScene: scene })
  },

  allScenes: null,

  setAllScenes: (data) => {
    set({ allScenes: data })
  },

  updateScene: (id, updates) => {
    set((state) => ({
      allScenes: state.allScenes
        ? state.allScenes.map((scene) => (scene.id === id ? { ...scene, ...updates } : scene))
        : null,
      currentScene:
        state.currentScene && state.currentScene.id === id
          ? { ...state.currentScene, ...updates }
          : state.currentScene
    }))
  },

  clearAll: () => {
    set({
      currentScene: null,
      allScenes: null
    })
  }
}))
