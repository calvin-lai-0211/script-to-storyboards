import { describe, it, expect } from "vitest";
import { API_ENDPOINTS } from "../endpoints";
import { API_BASE_URL } from "../client";

describe("API Endpoints", () => {
  describe("Character endpoints", () => {
    it("should generate correct character URL", () => {
      expect(API_ENDPOINTS.getCharacter(123)).toBe(
        `${API_BASE_URL}/api/character/123`,
      );
      expect(API_ENDPOINTS.getCharacter("abc")).toBe(
        `${API_BASE_URL}/api/character/abc`,
      );
    });

    it("should generate correct update character prompt URL", () => {
      expect(API_ENDPOINTS.updateCharacterPrompt(123)).toBe(
        `${API_BASE_URL}/api/character/123/prompt`,
      );
    });

    it("should generate correct generate character image URL", () => {
      expect(API_ENDPOINTS.generateCharacterImage(123)).toBe(
        `${API_BASE_URL}/api/character/123/generate-image`,
      );
    });
  });

  describe("Characters list endpoints", () => {
    it("should generate correct get all characters URL", () => {
      expect(API_ENDPOINTS.getAllCharacters()).toBe(
        `${API_BASE_URL}/api/characters/all`,
      );
    });

    it("should generate correct get characters URL with encoding", () => {
      const key = "剧本名";
      const encoded = encodeURIComponent(key);
      expect(API_ENDPOINTS.getCharacters(key)).toBe(
        `${API_BASE_URL}/api/characters/${encoded}`,
      );
    });

    it("should generate correct generate characters URL", () => {
      expect(API_ENDPOINTS.generateCharacters()).toBe(
        `${API_BASE_URL}/api/characters/generate`,
      );
    });
  });

  describe("Scenes endpoints", () => {
    it("should generate correct get all scenes URL", () => {
      expect(API_ENDPOINTS.getAllScenes()).toBe(
        `${API_BASE_URL}/api/scenes/all`,
      );
    });

    it("should generate correct get scene URL", () => {
      expect(API_ENDPOINTS.getScene(456)).toBe(`${API_BASE_URL}/api/scene/456`);
    });

    it("should generate correct get scenes URL with encoding", () => {
      const key = "test-key";
      expect(API_ENDPOINTS.getScenes(key)).toBe(
        `${API_BASE_URL}/api/scenes/${encodeURIComponent(key)}`,
      );
    });

    it("should generate correct generate scenes URL", () => {
      expect(API_ENDPOINTS.generateScenes()).toBe(
        `${API_BASE_URL}/api/scenes/generate`,
      );
    });
  });

  describe("Props endpoints", () => {
    it("should generate correct get all props URL", () => {
      expect(API_ENDPOINTS.getAllProps()).toBe(`${API_BASE_URL}/api/props/all`);
    });

    it("should generate correct generate props URL", () => {
      expect(API_ENDPOINTS.generateProps()).toBe(
        `${API_BASE_URL}/api/props/generate`,
      );
    });
  });

  describe("Scripts endpoints", () => {
    it("should generate correct get all scripts URL", () => {
      expect(API_ENDPOINTS.getAllScripts()).toBe(`${API_BASE_URL}/api/scripts`);
    });

    it("should generate correct get script URL with encoding", () => {
      const key = "script-123";
      expect(API_ENDPOINTS.getScript(key)).toBe(
        `${API_BASE_URL}/api/scripts/${encodeURIComponent(key)}`,
      );
    });

    it("should handle special characters in script key", () => {
      const key = "剧本/第1集";
      const encoded = encodeURIComponent(key);
      expect(API_ENDPOINTS.getScript(key)).toBe(
        `${API_BASE_URL}/api/scripts/${encoded}`,
      );
    });
  });

  describe("Storyboards endpoints", () => {
    it("should generate correct storyboard URL", () => {
      expect(API_ENDPOINTS.generateStoryboard()).toBe(
        `${API_BASE_URL}/api/storyboard/generate`,
      );
    });

    it("should generate correct get storyboards URL with encoding", () => {
      const key = "storyboard-key";
      expect(API_ENDPOINTS.getStoryboards(key)).toBe(
        `${API_BASE_URL}/api/storyboards/${encodeURIComponent(key)}`,
      );
    });
  });

  describe("Memory endpoints", () => {
    it("should generate correct get episode memory URL with encoding", () => {
      const key = "episode-123";
      expect(API_ENDPOINTS.getEpisodeMemory(key)).toBe(
        `${API_BASE_URL}/api/memory/${encodeURIComponent(key)}`,
      );
    });

    it("should handle UUID keys", () => {
      const key = "da4ef19d-5965-41c3-a971-f17d0ce06ef7";
      expect(API_ENDPOINTS.getEpisodeMemory(key)).toBe(
        `${API_BASE_URL}/api/memory/${key}`,
      );
    });
  });

  describe("URL encoding", () => {
    it("should properly encode special characters", () => {
      const specialKey = "test key/with spaces&symbols";
      const endpoints = [
        API_ENDPOINTS.getCharacters(specialKey),
        API_ENDPOINTS.getScenes(specialKey),
        API_ENDPOINTS.getScript(specialKey),
        API_ENDPOINTS.getStoryboards(specialKey),
        API_ENDPOINTS.getEpisodeMemory(specialKey),
      ];

      endpoints.forEach((url) => {
        expect(url).toContain(encodeURIComponent(specialKey));
        expect(url).not.toContain(" ");
        expect(url).not.toContain("&");
      });
    });
  });
});
