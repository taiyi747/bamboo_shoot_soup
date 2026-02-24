import { createHttpApiClient } from './http'
import type { ApiClient } from './types'
import { useStableUserId } from '../../composables/useStableUserId'

export const useApiClient = (): ApiClient => {
  const config = useRuntimeConfig()
  const baseURL = String(config.public.apiBase || 'http://127.0.0.1:8000')
  const userId = useStableUserId()

  return createHttpApiClient(baseURL, () => userId.value)
}
