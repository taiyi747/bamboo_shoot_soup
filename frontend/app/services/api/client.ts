import { createHttpApiClient } from './http'
import { mockApiClient } from './mock'
import type { ApiClient } from './types'

export const useApiClient = (): ApiClient => {
  const config = useRuntimeConfig()
  const mode = String(config.public.apiMode || 'mock').toLowerCase()
  const baseURL = String(config.public.apiBase || 'http://127.0.0.1:8000')

  if (mode === 'http') {
    return createHttpApiClient(baseURL)
  }

  return mockApiClient
}
