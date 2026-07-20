import type { TaskDto } from "./api";

export function stateBadge(task: TaskDto): string {
  const glyphs: Record<TaskDto["state"], string> = {
    pending: "…", running: "▶", done: "✓", failed: "✗",
  };
  return `${glyphs[task.state]} ${task.id}`;
}

export function attemptsLabel(task: TaskDto): string {
  return task.attempts === 0 ? "fresh" : `retry ${task.attempts}`;
}
