import { apiClient } from "../api-client";
import type { Task } from "../types";

export interface CreateTaskRequest {
  title: string;
}

export interface UpdateTaskRequest {
  title?: string;
  is_done?: boolean;
}

export const tasksApi = {
  list: () => apiClient.get<Task[]>("/tasks"),

  create: (data: CreateTaskRequest) => apiClient.post<Task>("/tasks", data),

  update: (id: string, data: UpdateTaskRequest) => apiClient.patch<Task>(`/tasks/${id}`, data),

  remove: (id: string) => apiClient.delete(`/tasks/${id}`),
};