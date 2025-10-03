import { describe, it, expect, beforeEach, vi } from "vitest";
import { apiCall, API_BASE_URL } from "../client";
import { requestDeduplicator } from "../requestDeduplicator";

// Mock fetch globally
global.fetch = vi.fn();

describe("API Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    requestDeduplicator.clear();
  });

  it("should make successful API call", async () => {
    const mockData = { id: 1, name: "Test" };
    const mockResponse = {
      code: 0,
      message: "success",
      data: mockData,
    };

    (global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    });

    const result = await apiCall("/test");

    expect(result).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith("/test", {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    });
  });

  it("should throw error when API returns non-zero code", async () => {
    const mockResponse = {
      code: 1,
      message: "Error occurred",
      data: null,
    };

    (global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    });

    await expect(apiCall("/test")).rejects.toThrow("Error occurred");
  });

  it("should throw error with default message when no message provided", async () => {
    const mockResponse = {
      code: 500,
      message: "",
      data: null,
    };

    (global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    });

    await expect(apiCall("/test")).rejects.toThrow("API error! code: 500");
  });

  it("should merge custom headers with default headers", async () => {
    const mockResponse = {
      code: 0,
      message: "success",
      data: {},
    };

    (global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    });

    await apiCall("/test", {
      headers: {
        Authorization: "Bearer token",
      },
    });

    expect(global.fetch).toHaveBeenCalledWith("/test", {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer token",
      },
    });
  });

  it("should use request deduplicator", async () => {
    const mockData = { id: 1 };
    const mockResponse = {
      code: 0,
      message: "success",
      data: mockData,
    };

    (global.fetch as any).mockResolvedValue({
      json: async () => mockResponse,
    });

    // Make two concurrent requests
    const promise1 = apiCall("/test");
    const promise2 = apiCall("/test");

    const [result1, result2] = await Promise.all([promise1, promise2]);

    // Both should return the same data
    expect(result1).toEqual(mockData);
    expect(result2).toEqual(mockData);

    // Fetch should only be called once due to deduplication
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("should have correct API_BASE_URL", () => {
    expect(API_BASE_URL).toBeDefined();
    expect(typeof API_BASE_URL).toBe("string");
  });

  it("should redirect to login when receiving 4003 error code", async () => {
    const mockResponse = {
      code: 4003,
      message: "未登录或登录已过期，请重新登录",
      data: {
        auth_url: "https://accounts.google.com/o/oauth2/auth?...",
      },
    };

    (global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    });

    // Mock window.location.href
    const originalLocation = window.location;
    delete (window as any).location;
    window.location = { href: "" } as any;

    await expect(apiCall("/test")).rejects.toThrow("未登录或登录已过期，请重新登录");

    // Should redirect to auth URL
    expect(window.location.href).toBe(
      "https://accounts.google.com/o/oauth2/auth?..."
    );

    // Restore window.location
    ;(window as any).location = originalLocation;
  });
});
