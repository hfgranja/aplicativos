export interface NetworkClientPort {
  get<T>(path: string, params?: Record<string, string>): Promise<T>
  post<T>(path: string, body: unknown): Promise<T>
  put<T>(path: string, body: unknown): Promise<T>
  patch<T>(path: string, body: unknown): Promise<T>
  delete(path: string): Promise<void>
  uploadFile<T>(path: string, file: File, fields?: Record<string, string>): Promise<T>
}
