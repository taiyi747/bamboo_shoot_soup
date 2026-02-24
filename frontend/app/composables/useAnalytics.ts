import { useApiClient } from '../services/api/client'
import type { AnalyticsEventName, AnalyticsEventPayload } from '../types/flow'
import { useStableUserId } from './useStableUserId'

export const useAnalytics = () => {
  const { state } = useMvpFlow()
  const api = useApiClient()
  const userId = useStableUserId()

  const track = async (
    eventName: AnalyticsEventName,
    identityId?: string,
    metadata?: Record<string, unknown>
  ): Promise<AnalyticsEventPayload> => {
    const payload: AnalyticsEventPayload = {
      eventName,
      userId: userId.value,
      timestamp: new Date().toISOString(),
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
