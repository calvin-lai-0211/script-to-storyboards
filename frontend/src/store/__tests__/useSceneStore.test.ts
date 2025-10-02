import { describe, it, expect, beforeEach } from 'vitest';
import { useSceneStore } from '../useSceneStore';
import type { SceneData } from '../types';

describe('useSceneStore', () => {
  beforeEach(() => {
    useSceneStore.getState().clearAll();
  });

  it('should initialize with null values', () => {
    const state = useSceneStore.getState();
    expect(state.currentScene).toBeNull();
    expect(state.allScenes).toBeNull();
  });

  it('should set and get currentScene', () => {
    const mockScene: SceneData = {
      id: 1,
      scene_name: 'Test Scene',
      drama_name: 'Test Drama',
      episode_number: 1,
      image_url: null,
      image_prompt: 'Test prompt',
    };

    useSceneStore.getState().setCurrentScene(mockScene);
    expect(useSceneStore.getState().currentScene).toEqual(mockScene);
  });

  it('should set and get allScenes', () => {
    const mockScenes: SceneData[] = [
      {
        id: 1,
        scene_name: 'Scene 1',
        drama_name: 'Drama',
        episode_number: 1,
        image_url: null,
        image_prompt: 'Prompt 1',
      },
    ];

    useSceneStore.getState().setAllScenes(mockScenes);
    expect(useSceneStore.getState().allScenes).toEqual(mockScenes);
  });

  it('should clear all data', () => {
    const mockScene: SceneData = {
      id: 1,
      scene_name: 'Scene',
      drama_name: 'Drama',
      episode_number: 1,
      image_url: null,
      image_prompt: 'Prompt',
    };

    useSceneStore.getState().setCurrentScene(mockScene);
    useSceneStore.getState().setAllScenes([mockScene]);
    useSceneStore.getState().clearAll();

    const state = useSceneStore.getState();
    expect(state.currentScene).toBeNull();
    expect(state.allScenes).toBeNull();
  });
});
