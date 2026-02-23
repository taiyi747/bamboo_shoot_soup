import type { ApiClient } from './types'

export const createHttpApiClient = (baseURL: string): ApiClient => ({
  createOnboardingSession: input =>
    $fetch('/api/v1/onboarding/sessions', {
      method: 'POST',
      baseURL,
      body: input,
    }),

  completeOnboarding: input =>
    $fetch(`/api/v1/onboarding/sessions/${input.sessionId}/complete`, {
      method: 'POST',
      baseURL,
      body: input.input,
    }),

  generateIdentityModels: input =>
    $fetch('/api/v1/identity-models/generate', {
      method: 'POST',
      baseURL,
      body: input,
    }),

  selectIdentity: input =>
    $fetch('/api/v1/identity-selections', {
      method: 'POST',
      baseURL,
      body: input,
    }),

  generatePersonaConstitution: input =>
    $fetch('/api/v1/persona-constitutions/generate', {
      method: 'POST',
      baseURL,
      body: input,
    }),

  generateLaunchKit: input =>
    $fetch('/api/v1/launch-kits/generate', {
      method: 'POST',
      baseURL,
      body: input,
    }),

  runConsistencyCheck: input =>
    $fetch('/api/v1/consistency-checks', {
      method: 'POST',
      baseURL,
      body: input,
    }),

  trackEvent: input =>
    $fetch('/api/v1/events', {
      method: 'POST',
      baseURL,
      body: input,
    }),
})
