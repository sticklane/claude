/** Typed client for the taskflow pyserver API. */

export interface TaskDto {
  id: string;
  queue: string;
  state: "pending" | "running" | "done" | "failed";
  attempts: number;
}

export class ApiClient {
  constructor(private baseUrl: string) {}

  async submit(queue: string, payload: object): Promise<TaskDto> {
    const res = await fetch(`${this.baseUrl}/${queue}`, {
      method: "POST",
      body: JSON.stringify({ payload }),
    });
    return res.json();
  }

  async poll(queue: string): Promise<TaskDto | null> {
    const res = await fetch(`${this.baseUrl}/${queue}`);
    return res.status === 204 ? null : res.json();
  }
}
