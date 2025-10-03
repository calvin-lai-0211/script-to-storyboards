export interface Script {
  script_id: number
  key: string
  title: string
  episode_num: number
  author: string | null
  creation_year: number | null
  score: number | null
}

export interface ScriptDetail {
  key: string
  title: string
  episode_num: number
  content: string
  roles: string[]
  sceneries: string[]
  author: string | null
  creation_year: number | null
}

export interface ScriptsResponse {
  scripts: Script[]
  count: number
}
