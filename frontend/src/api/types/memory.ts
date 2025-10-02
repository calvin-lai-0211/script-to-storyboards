export interface Memory {
  id: number;
  script_name: string;
  episode_number: number;
  plot_summary: string;
  options: Record<string, unknown>;
  created_at: string;
}
