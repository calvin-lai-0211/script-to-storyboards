export interface Prop {
  id: number
  drama_name: string
  episode_number: number
  prop_name: string
  image_url: string | null
  image_prompt: string
  reflection: string | null
  version: string
  shots_appeared: string[] | null
  is_key_prop: boolean | null
  prop_brief: string | null
  created_at: string
}

export interface PropsResponse {
  props: Prop[]
  count: number
}
