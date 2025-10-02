export interface Scene {
  id: number;
  drama_name: string;
  episode_number: number;
  scene_name: string;
  image_url: string | null;
  image_prompt: string;
  reflection?: string | null;
}

export interface ScenesResponse {
  scenes: Scene[];
  count: number;
  key?: string;
  drama_name?: string;
  episode_number?: number;
}
