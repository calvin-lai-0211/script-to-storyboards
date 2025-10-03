export interface Character {
  id: number
  drama_name: string
  episode_number: number
  character_name: string
  image_url: string | null
  image_prompt: string
  is_key_character: boolean
  reflection?: string | null
  character_brief?: string | null
}

export interface CharactersResponse {
  characters: Character[]
  count: number
  key?: string
  drama_name?: string
  episode_number?: number
}
