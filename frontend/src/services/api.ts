/**
 * Base API client with fetch wrapper.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers: customHeaders, ...restOptions } = options

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...customHeaders,
  }

  const config: RequestInit = {
    ...restOptions,
    headers,
  }

  if (body !== undefined) {
    config.body = JSON.stringify(body)
  }

  const response = await fetch(`${API_BASE}${endpoint}`, config)

  if (!response.ok) {
    let errorMessage = `HTTP error ${response.status}`
    let errorDetails: unknown

    try {
      const errorData = await response.json()
      errorDetails = errorData

      // Handle different error formats
      if (typeof errorData.message === 'string') {
        errorMessage = errorData.message
      } else if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail
      } else if (Array.isArray(errorData.detail)) {
        // FastAPI validation errors are arrays of objects
        errorMessage = errorData.detail
          .map((err: { msg?: string; message?: string }) => err.msg || err.message || 'Unknown error')
          .join('; ')
      } else if (errorData.detail && typeof errorData.detail === 'object') {
        errorMessage = JSON.stringify(errorData.detail)
      }
    } catch {
      // Ignore JSON parse errors for error responses
    }

    throw new ApiError(response.status, errorMessage, errorDetails)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'POST', body }),

  put: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'PUT', body }),

  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
}

export default api
