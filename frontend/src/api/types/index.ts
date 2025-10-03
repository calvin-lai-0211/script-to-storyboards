export * from './script'
export * from './character'
export * from './scene'
export * from './prop'
export * from './storyboard'
export * from './memory'

export interface ApiResponse<T = unknown> {
  code: number
  data: T | null
  message: string
}
