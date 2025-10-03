import { describe, it, expect, beforeEach } from 'vitest'
import { useEpisodeStore } from '../useEpisodeStore'
import type { EpisodeData, StoryboardData, MemoryData } from '../types'

describe('useEpisodeStore', () => {
  beforeEach(() => {
    useEpisodeStore.getState().clearAll()
  })

  describe('currentEpisode', () => {
    it('should initialize with null currentEpisode', () => {
      const { currentEpisode } = useEpisodeStore.getState()
      expect(currentEpisode).toBeNull()
    })

    it('should set and get currentEpisode', () => {
      const mockEpisode: Partial<EpisodeData> = {
        key: 'test-key',
        title: 'Test Episode',
        episode_num: 1
      }

      useEpisodeStore.getState().setCurrentEpisode(mockEpisode)
      const { currentEpisode } = useEpisodeStore.getState()

      expect(currentEpisode).toEqual(mockEpisode)
    })
  })

  describe('episodes', () => {
    it('should initialize with empty episodes object', () => {
      const { episodes } = useEpisodeStore.getState()
      expect(episodes).toEqual({})
    })

    it('should set and get episode by key', () => {
      const mockEpisode: EpisodeData = {
        key: 'test-key',
        title: 'Test Title',
        episode_num: 1,
        content: 'Test content',
        roles: ['Role 1'],
        sceneries: ['Scene 1'],
        author: 'Test Author',
        creation_year: 2025
      }

      useEpisodeStore.getState().setEpisode('test-key', mockEpisode)
      const episode = useEpisodeStore.getState().getEpisode('test-key')

      expect(episode).toEqual(mockEpisode)
    })

    it('should return undefined for non-existent key', () => {
      const episode = useEpisodeStore.getState().getEpisode('non-existent')
      expect(episode).toBeUndefined()
    })
  })

  describe('storyboards', () => {
    it('should set and get storyboard by key', () => {
      const mockStoryboard: StoryboardData = {
        key: 'test-key',
        drama_name: 'Test Drama',
        episode_num: 1,
        scenes: []
      }

      useEpisodeStore.getState().setStoryboard('test-key', mockStoryboard)
      const storyboard = useEpisodeStore.getState().getStoryboard('test-key')

      expect(storyboard).toEqual(mockStoryboard)
    })
  })

  describe('memories', () => {
    it('should set and get memory by key', () => {
      const mockMemory: MemoryData = {
        key: 'test-key',
        drama_name: 'Test Drama',
        episode_num: 1,
        memories: []
      }

      useEpisodeStore.getState().setMemory('test-key', mockMemory)
      const memory = useEpisodeStore.getState().getMemory('test-key')

      expect(memory).toEqual(mockMemory)
    })
  })

  describe('clearAll', () => {
    it('should clear all store data', () => {
      const episode: EpisodeData = {
        key: 'test-key',
        title: 'Test',
        episode_num: 1,
        content: 'Content',
        roles: [],
        sceneries: [],
        author: null,
        creation_year: null
      }

      useEpisodeStore.getState().setEpisode('test-key', episode)
      useEpisodeStore.getState().setCurrentEpisode(episode)
      useEpisodeStore.getState().setAllEpisodes([
        {
          script_id: 1,
          key: 'test',
          title: 'Test',
          episode_num: 1,
          author: null,
          creation_year: null,
          score: null
        }
      ])

      useEpisodeStore.getState().clearAll()

      const state = useEpisodeStore.getState()
      expect(state.currentEpisode).toBeNull()
      expect(state.episodes).toEqual({})
      expect(state.storyboards).toEqual({})
      expect(state.memories).toEqual({})
      expect(state.allEpisodes).toBeNull()
    })
  })
})
