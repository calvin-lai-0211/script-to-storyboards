/**
 * Request Deduplication Manager
 *
 * Prevents duplicate concurrent requests to the same endpoint.
 * If a request is already in progress, subsequent requests will wait for and share the same response.
 */

interface PendingRequest<T> {
  promise: Promise<T>
  timestamp: number
}

class RequestDeduplicator {
  private pendingRequests: Map<string, PendingRequest<unknown>> = new Map()
  private readonly CLEANUP_INTERVAL = 60000 // 1 minute
  private cleanupTimer: ReturnType<typeof setInterval> | null = null

  constructor() {
    this.startCleanup()
  }

  /**
   * Generate a unique key for the request
   */
  private generateKey(url: string, options?: RequestInit): string {
    const method = options?.method || 'GET'
    const body = options?.body ? JSON.stringify(options.body) : ''
    return `${method}:${url}:${body}`
  }

  /**
   * Execute request with deduplication
   */
  async deduplicate<T>(
    url: string,
    options: RequestInit | undefined,
    executor: () => Promise<T>
  ): Promise<T> {
    const key = this.generateKey(url, options)

    // Check if there's already a pending request
    const pending = this.pendingRequests.get(key)
    if (pending) {
      console.debug(`Request deduplication: Reusing pending request for ${url}`)
      return pending.promise as Promise<T>
    }

    // Create new request
    console.debug(`Request deduplication: Starting new request for ${url}`)
    const promise = executor().finally(() => {
      // Remove from pending requests when done
      this.pendingRequests.delete(key)
    })

    // Store the pending request
    this.pendingRequests.set(key, {
      promise,
      timestamp: Date.now()
    })

    return promise
  }

  /**
   * Cleanup stale pending requests (shouldn't normally happen, but safety measure)
   */
  private cleanup() {
    const now = Date.now()
    const MAX_AGE = 300000 // 5 minutes

    for (const [key, request] of this.pendingRequests.entries()) {
      if (now - request.timestamp > MAX_AGE) {
        console.debug(`Request deduplication: Cleaning up stale request ${key}`)
        this.pendingRequests.delete(key)
      }
    }
  }

  /**
   * Start periodic cleanup
   */
  private startCleanup() {
    if (this.cleanupTimer) return
    this.cleanupTimer = setInterval(() => this.cleanup(), this.CLEANUP_INTERVAL)
  }

  /**
   * Stop periodic cleanup
   */
  stopCleanup() {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer)
      this.cleanupTimer = null
    }
  }

  /**
   * Clear all pending requests (useful for testing or reset)
   */
  clear() {
    this.pendingRequests.clear()
  }

  /**
   * Get number of pending requests (for debugging)
   */
  getPendingCount(): number {
    return this.pendingRequests.size
  }
}

// Singleton instance
export const requestDeduplicator = new RequestDeduplicator()
