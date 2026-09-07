import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

interface Task {
  id: string;
  title: string;
  is_done: boolean;
  created_at: string;
  updated_at: string;
}

interface TasksState {
  items: Task[];
  status: "idle" | "loading" | "succeeded" | "error";
  error: string | null;
}

const initialState: TasksState = {
  items: [],
  status: "idle",
  error: null,
};

const tasksSlice = createSlice({
  name: "tasks",
  initialState,
  reducers: {
    setTasks: (state, action: PayloadAction<Task[]>) => {
      state.items = action.payload;
      state.status = "succeeded";
      state.error = null;
    },
    addTask: (state, action: PayloadAction<Task>) => {
      state.items.unshift(action.payload);
    },
    updateTask: (state, action: PayloadAction<Task>) => {
      const index = state.items.findIndex((t) => t.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = action.payload;
      }
    },
    removeTask: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter((t) => t.id !== action.payload);
    },
    setStatus: (state, action: PayloadAction<TasksState["status"]>) => {
      state.status = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      state.status = "error";
    },
  },
});

export const { setTasks, addTask, updateTask, removeTask, setStatus, setError } = tasksSlice.actions;
export default tasksSlice.reducer;