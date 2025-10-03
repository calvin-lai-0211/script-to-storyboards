import type { ApiResponse } from "./types";
import { requestDeduplicator } from "./requestDeduplicator";

// API Base URL
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// Helper function for API calls with automatic request deduplication
export const apiCall = async <T = unknown>(
  url: string,
  options?: RequestInit,
): Promise<T> => {
  return requestDeduplicator.deduplicate(url, options, async () => {
    console.debug("API call:", url);
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    const result: ApiResponse<T> = await response.json();

    // Check if API returned error (code !== 0)
    if (result.code !== 0) {
      throw new Error(result.message || `API error! code: ${result.code}`);
    }

    // Return the data field
    return result.data as T;
  });
};
