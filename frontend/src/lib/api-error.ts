export interface ApiErrorShape {
  status: number;
  code: string;
  message: string;
  details: Record<string, string[]> | null;
  requestId: string | null;
}

export class ApiError extends Error implements ApiErrorShape {
  constructor(
    public readonly status: number,
    public readonly code: string,
    public readonly message: string,
    public readonly details: Record<string, string[]> | null,
    public readonly requestId: string | null
  ) {
    super(message);
    this.name = "ApiError";
  }

  static fromResponse(response: Response, data: unknown): ApiError {
    const errorData = data as { error?: { code: string; message: string; details: Record<string, string[]> | null; request_id: string } };
    if (errorData?.error) {
      return new ApiError(
        response.status,
        errorData.error.code,
        errorData.error.message,
        errorData.error.details,
        errorData.error.request_id
      );
    }
    return new ApiError(
      response.status,
      "UNKNOWN_ERROR",
      response.statusText,
      null,
      null
    );
  }

  static fromNetworkError(error: Error): ApiError {
    return new ApiError(
      0,
      "NETWORK_ERROR",
      error.message || "Network error",
      null,
      null
    );
  }
}