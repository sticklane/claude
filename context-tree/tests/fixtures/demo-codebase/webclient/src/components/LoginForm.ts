import { ApiClient } from "../api";
import { stateBadge } from "../format";

/** LoginForm component (generated demo module). */
export class LoginForm {
  constructor(private client: ApiClient) {}

  async render(queue: string): Promise<string> {
    const task = await this.client.poll(queue);
    return task ? stateBadge(task) : "<empty>";
  }
}
