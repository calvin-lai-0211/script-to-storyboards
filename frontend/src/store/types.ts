/**
 * Store type definitions
 */

// Episode related types
export interface EpisodeData {
  key: string;
  title: string;
  episode_num: number;
  content: string;
  roles: string[];
  sceneries: string[];
  author: string | null;
  creation_year: number | null;
}

export interface StoryboardData {
  key: string;
  drama_name: string;
  episode_num: number;
  scenes: Record<string, unknown>[];
}

export interface MemoryData {
  key: string;
  drama_name: string;
  episode_num: number;
  memories: Record<string, unknown>[];
}

// Character related types
export interface CharacterData {
  id: number;
  character_name: string;
  drama_name: string;
  episode_number: number;
  image_url: string | null;
  image_prompt: string;
  is_key_character: boolean;
}

// Scene related types
export interface SceneData {
  id: number;
  scene_name: string;
  drama_name: string;
  episode_number: number;
  image_url: string | null;
  image_prompt: string;
}

// Prop related types
export interface PropData {
  id: number;
  prop_name: string;
  drama_name: string;
  episode_number: number;
  image_url: string | null;
  image_prompt: string;
  reflection: string | null;
  version: string;
  shots_appeared: string[] | null;
  is_key_prop: boolean | null;
  prop_brief: string | null;
  created_at: string;
}

// Script list item type (for episode list page)
export interface ScriptData {
  script_id: number;
  key: string;
  title: string;
  episode_num: number;
  author: string | null;
  creation_year: number | null;
  score: number | null;
}
