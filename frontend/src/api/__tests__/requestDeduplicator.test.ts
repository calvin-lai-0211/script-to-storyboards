import { describe, it, expect, beforeEach, vi } from 'vitest'
import { requestDeduplicator } from '../requestDeduplicator'

describe('RequestDeduplicator', () => {
  beforeEach(() => {
    requestDeduplicator.clear()
  })

  it('should deduplicate concurrent requests to the same endpoint', async () => {
    let callCount = 0
    const mockExecutor = vi.fn(async () => {
      callCount++
      await new Promise((resolve) => setTimeout(resolve, 100))
      return `result-${callCount}`
    })

    // Start 3 concurrent requests
    const promise1 = requestDeduplicator.deduplicate('/api/test', undefined, mockExecutor)
    const promise2 = requestDeduplicator.deduplicate('/api/test', undefined, mockExecutor)
    const promise3 = requestDeduplicator.deduplicate('/api/test', undefined, mockExecutor)

    // All should share the same promise
    expect(requestDeduplicator.getPendingCount()).toBe(1)

    const [result1, result2, result3] = await Promise.all([promise1, promise2, promise3])

    // Executor should only be called once
    expect(mockExecutor).toHaveBeenCalledTimes(1)

    // All results should be the same
    expect(result1).toBe('result-1')
    expect(result2).toBe('result-1')
    expect(result3).toBe('result-1')

    // Pending requests should be cleared
    expect(requestDeduplicator.getPendingCount()).toBe(0)
  })

  it('should not deduplicate requests to different endpoints', async () => {
    const mockExecutor1 = vi.fn(async () => 'result-1')
    const mockExecutor2 = vi.fn(async () => 'result-2')

    const promise1 = requestDeduplicator.deduplicate('/api/test1', undefined, mockExecutor1)
    const promise2 = requestDeduplicator.deduplicate('/api/test2', undefined, mockExecutor2)

    expect(requestDeduplicator.getPendingCount()).toBe(2)

    await Promise.all([promise1, promise2])

    expect(mockExecutor1).toHaveBeenCalledTimes(1)
    expect(mockExecutor2).toHaveBeenCalledTimes(1)
  })

  it('should differentiate requests with different methods', async () => {
    const mockExecutor1 = vi.fn(async () => 'get-result')
    const mockExecutor2 = vi.fn(async () => 'post-result')

    const promise1 = requestDeduplicator.deduplicate('/api/test', { method: 'GET' }, mockExecutor1)
    const promise2 = requestDeduplicator.deduplicate('/api/test', { method: 'POST' }, mockExecutor2)

    expect(requestDeduplicator.getPendingCount()).toBe(2)

    const [result1, result2] = await Promise.all([promise1, promise2])

    expect(result1).toBe('get-result')
    expect(result2).toBe('post-result')
    expect(mockExecutor1).toHaveBeenCalledTimes(1)
    expect(mockExecutor2).toHaveBeenCalledTimes(1)
  })

  it('should differentiate requests with different bodies', async () => {
    const mockExecutor1 = vi.fn(async () => 'body1-result')
    const mockExecutor2 = vi.fn(async () => 'body2-result')

    const promise1 = requestDeduplicator.deduplicate(
      '/api/test',
      { method: 'POST', body: JSON.stringify({ id: 1 }) },
      mockExecutor1
    )
    const promise2 = requestDeduplicator.deduplicate(
      '/api/test',
      { method: 'POST', body: JSON.stringify({ id: 2 }) },
      mockExecutor2
    )

    expect(requestDeduplicator.getPendingCount()).toBe(2)

    await Promise.all([promise1, promise2])

    expect(mockExecutor1).toHaveBeenCalledTimes(1)
    expect(mockExecutor2).toHaveBeenCalledTimes(1)
  })

  it('should handle errors properly', async () => {
    const mockExecutor = vi.fn(async () => {
      throw new Error('Test error')
    })

    const promise1 = requestDeduplicator.deduplicate('/api/test', undefined, mockExecutor)
    const promise2 = requestDeduplicator.deduplicate('/api/test', undefined, mockExecutor)

    await expect(promise1).rejects.toThrow('Test error')
    await expect(promise2).rejects.toThrow('Test error')

    // Executor should only be called once
    expect(mockExecutor).toHaveBeenCalledTimes(1)

    // Pending requests should be cleared after error
    expect(requestDeduplicator.getPendingCount()).toBe(0)
  })

  it('should allow sequential requests to the same endpoint', async () => {
    let callCount = 0
    const mockExecutor = vi.fn(async () => {
      callCount++
      return `result-${callCount}`
    })

    // First request
    const result1 = await requestDeduplicator.deduplicate('/api/test', undefined, mockExecutor)
    expect(result1).toBe('result-1')
    expect(requestDeduplicator.getPendingCount()).toBe(0)

    // Second request (after first completes)
    const result2 = await requestDeduplicator.deduplicate('/api/test', undefined, mockExecutor)
    expect(result2).toBe('result-2')
    expect(requestDeduplicator.getPendingCount()).toBe(0)

    // Executor should be called twice (not deduplicated)
    expect(mockExecutor).toHaveBeenCalledTimes(2)
  })

  it('should clear all pending requests', async () => {
    const mockExecutor = vi.fn(async () => {
      await new Promise((resolve) => setTimeout(resolve, 100))
      return 'result'
    })

    requestDeduplicator.deduplicate('/api/test1', undefined, mockExecutor)
    requestDeduplicator.deduplicate('/api/test2', undefined, mockExecutor)

    expect(requestDeduplicator.getPendingCount()).toBe(2)

    requestDeduplicator.clear()

    expect(requestDeduplicator.getPendingCount()).toBe(0)
  })
})
