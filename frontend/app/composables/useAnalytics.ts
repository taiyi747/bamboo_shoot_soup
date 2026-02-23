import { useApiClient } from '../services/api/client'
import type { AnalyticsEventName, AnalyticsEventPayload } from '../types/mvp'

const buildUserId = () => {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID()
  }
  return `user_${Math.random().toString(36).slice(2, 10)}`
}

export const useAnalytics = () => {
  const { state } = useMvpFlow()
  const api = useApiClient()
  const userId = useState<string>('mvp-user-id', buildUserId)
  const config = useRuntimeConfig()
  const stage = String(config.public.stage || 'MVP').toUpperCase() as 'MVP'

  const track = async (
    eventName: AnalyticsEventName,
    identityId?: string,
    metadata?: Record<string, unknown>
  ): Promise<AnalyticsEventPayload> => {
    const payload: AnalyticsEventPayload = {
      eventName,
      userId: userId.value,
      timestamp: new Date().toISOString(),
      stage,
      identityId,
      metadata,
    }

    state.value.events.push(payload)

    try {
      await api.trackEvent(payload)
    } catch (error) {
      console.warn('track event failed', error)
    }

    return payload
  }

  return { track, userId }
}
