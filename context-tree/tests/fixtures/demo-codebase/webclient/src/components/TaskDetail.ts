import { ApiClient } from "../api";
import { stateBadge } from "../format";

/** TaskDetail component (generated demo module). */
export class TaskDetail {
  constructor(private client: ApiClient) {}

  async render(queue: string): Promise<string> {
    const task = await this.client.poll(queue);
    return task ? stateBadge(task) : "<empty>";
  }
}
