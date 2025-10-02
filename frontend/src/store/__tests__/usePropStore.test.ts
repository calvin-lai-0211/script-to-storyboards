import { describe, it, expect, beforeEach } from 'vitest';
import { usePropStore } from '../usePropStore';
import type { PropData } from '../types';

describe('usePropStore', () => {
  beforeEach(() => {
    usePropStore.getState().clearAll();
  });

  it('should initialize with null values', () => {
    const state = usePropStore.getState();
    expect(state.currentProp).toBeNull();
    expect(state.allProps).toBeNull();
  });

  it('should set and get currentProp', () => {
    const mockProp: PropData = {
      id: 1,
      prop_name: 'Test Prop',
      drama_name: 'Test Drama',
      episode_number: 1,
      image_url: null,
      image_prompt: 'Test prompt',
      reflection: null,
      version: 'v1',
      shots_appeared: null,
      is_key_prop: false,
      prop_brief: null,
      created_at: '2025-01-01',
    };

    usePropStore.getState().setCurrentProp(mockProp);
    expect(usePropStore.getState().currentProp).toEqual(mockProp);
  });

  it('should set and get allProps', () => {
    const mockProps: PropData[] = [
      {
        id: 1,
        prop_name: 'Prop 1',
        drama_name: 'Drama',
        episode_number: 1,
        image_url: null,
        image_prompt: 'Prompt 1',
        reflection: null,
        version: 'v1',
        shots_appeared: null,
        is_key_prop: false,
        prop_brief: null,
        created_at: '2025-01-01',
      },
    ];

    usePropStore.getState().setAllProps(mockProps);
    expect(usePropStore.getState().allProps).toEqual(mockProps);
  });

  it('should clear all data', () => {
    const mockProp: PropData = {
      id: 1,
      prop_name: 'Prop',
      drama_name: 'Drama',
      episode_number: 1,
      image_url: null,
      image_prompt: 'Prompt',
      reflection: null,
      version: 'v1',
      shots_appeared: null,
      is_key_prop: false,
      prop_brief: null,
      created_at: '2025-01-01',
    };

    usePropStore.getState().setCurrentProp(mockProp);
    usePropStore.getState().setAllProps([mockProp]);
    usePropStore.getState().clearAll();

    const state = usePropStore.getState();
    expect(state.currentProp).toBeNull();
    expect(state.allProps).toBeNull();
  });
});
