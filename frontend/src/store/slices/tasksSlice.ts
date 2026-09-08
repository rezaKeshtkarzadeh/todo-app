import { createSlice, type PayloadAction, createAsyncThunk } from "@reduxjs/toolkit";
import { tasksApi } from "@/lib/api/tasks";
import type { Task, CreateTaskRequest, UpdateTaskRequest } from "@/lib/api/tasks";

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

export const fetchTasks = createAsyncThunk(
  "tasks/fetchTasks",
  async (_, { rejectWithValue }) => {
    try {
      const response = await tasksApi.list();
      return response.data;
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue(apiError.message || "Failed to fetch tasks");
    }
  }
);

export const createTask = createAsyncThunk(
  "tasks/createTask",
  async (data: CreateTaskRequest, { rejectWithValue }) => {
    try {
      const response = await tasksApi.create(data);
      return response.data;
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue(apiError.message || "Failed to create task");
    }
  }
);

export const updateTask = createAsyncThunk(
  "tasks/updateTask",
  async ({ id, data, previousTask }: { id: string; data: UpdateTaskRequest; previousTask: Task }, { rejectWithValue }) => {
    try {
      const response = await tasksApi.update(id, data);
      return response.data;
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue({ message: apiError.message || "Failed to update task", previousTask });
    }
  }
);

export const deleteTask = createAsyncThunk(
  "tasks/deleteTask",
  async ({ id, previousTask }: { id: string; previousTask: Task }, { rejectWithValue }) => {
    try {
      await tasksApi.remove(id);
      return { id, previousTask };
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue({ message: apiError.message || "Failed to delete task", previousTask });
    }
  }
);

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
  extraReducers: (builder) => {
    builder
      .addCase(fetchTasks.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(fetchTasks.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload;
        state.error = null;
      })
      .addCase(fetchTasks.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload as string;
      })
      .addCase(createTask.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(createTask.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items.unshift(action.payload);
        state.error = null;
      })
      .addCase(createTask.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload as string;
      })
      .addCase(updateTask.pending, (state, action) => {
        const { id, data } = action.meta.arg;
        const index = state.items.findIndex((t) => t.id === id);
        if (index !== -1) {
          state.items[index] = { ...state.items[index], ...data };
        }
      })
      .addCase(updateTask.fulfilled, (state, action) => {
        state.status = "succeeded";
        const index = state.items.findIndex((t) => t.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
        state.error = null;
      })
      .addCase(updateTask.rejected, (state, action) => {
        state.status = "error";
        const { previousTask } = action.payload as { previousTask: Task };
        const index = state.items.findIndex((t) => t.id === previousTask.id);
        if (index !== -1) {
          state.items[index] = previousTask;
        }
        state.error = (action.payload as { message: string }).message;
      })
      .addCase(deleteTask.pending, (state, action) => {
        const { id } = action.meta.arg;
        state.items = state.items.filter((t) => t.id !== id);
      })
      .addCase(deleteTask.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.error = null;
      })
      .addCase(deleteTask.rejected, (state, action) => {
        state.status = "error";
        const { previousTask } = action.payload as { previousTask: Task };
        state.items.unshift(previousTask);
        state.error = (action.payload as { message: string }).message;
      });
  },
});

export const { setTasks, addTask, updateTask: updateTaskReducer, removeTask, setStatus, setError } = tasksSlice.actions;
export default tasksSlice.reducer;