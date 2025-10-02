export interface Storyboard {
  id: number;
  scene_number: number;
  scene_description: string;
  shot_number: number;
  shot_description: string;
  sub_shot_number: number;
  camera_angle: string;
  characters: string[];
  scenes: string[];
  image_prompt: string;
  video_prompt: string;
  dialogue_sound: string;
  duration: number;
  director_notes: string;
}

export interface StoryboardsResponse {
  storyboards: Storyboard[];
  count: number;
  key: string;
  drama_name: string;
  episode_number: number;
}
