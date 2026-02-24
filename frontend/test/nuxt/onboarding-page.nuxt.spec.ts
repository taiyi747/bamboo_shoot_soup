import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import type { MvpFlowState, OnboardingProfile } from '../../app/types/flow'

const createOnboardingSessionMock = vi.hoisted(() => vi.fn())
const completeOnboardingMock = vi.hoisted(() => vi.fn())
const trackMock = vi.hoisted(() => vi.fn())
const navigateToMock = vi.hoisted(() => vi.fn())

const createFlowState = (): MvpFlowState => ({
  onboardingInput: {
    skills: [],
    interests: [],
    cognitiveStyle: '',
    valueBoundaries: [],
    riskTolerance: 'medium',
    weeklyHours: 6,
    goals: [],
  },
  identityModels: [],
  draftToCheck: '',
  events: [],
})

const sampleProfile: OnboardingProfile = {
  skillStack: ['行业分析', '项目管理'],
  energyCurve: ['职场策略'],
  cognitiveStyle: '结构化',
  valueBoundaries: ['不夸大'],
  riskTolerance: 'medium',
  weeklyHours: 8,
  recommendedPlatforms: ['公众号'],
}

const state = ref<MvpFlowState>(createFlowState())
const resetMock = vi.fn(() => {
  state.value = createFlowState()
})

vi.mock('../../app/services/api/client', () => ({
  useApiClient: () => ({
    createOnboardingSession: createOnboardingSessionMock,
    completeOnboarding: completeOnboardingMock,
  }),
}))

mockNuxtImport('useAnalytics', () => () => ({
  track: trackMock,
}))

mockNuxtImport('useMvpFlow', () => () => ({
  state,
  reset: resetMock,
}))

mockNuxtImport('navigateTo', () => navigateToMock)

const createDeferred = <T>() => {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

describe('onboarding page', () => {
  beforeEach(() => {
    state.value = createFlowState()
    resetMock.mockClear()
    createOnboardingSessionMock.mockReset()
    createOnboardingSessionMock.mockResolvedValue({ sessionId: 'session_1' })
    completeOnboardingMock.mockReset()
    completeOnboardingMock.mockResolvedValue({ profile: sampleProfile })
    trackMock.mockReset()
    trackMock.mockResolvedValue({})
    navigateToMock.mockReset()
    navigateToMock.mockResolvedValue(undefined)
  })

  it('renders onboarding content', async () => {
    const OnboardingPage = (await import('../../app/pages/onboarding.vue')).default
    const wrapper = await mountSuspended(OnboardingPage)
    expect(wrapper.text()).toContain('身份诊断')
    expect(wrapper.text()).toContain('技能栈')
  })

  it('shows loading feedback while submitting and hides it after success', async () => {
    const deferred = createDeferred<{ profile: OnboardingProfile }>()
    completeOnboardingMock.mockReturnValueOnce(deferred.promise)

    const OnboardingPage = (await import('../../app/pages/onboarding.vue')).default
    const wrapper = await mountSuspended(OnboardingPage)
    const form = wrapper.find('form')
    expect(form.exists()).toBe(true)
    await form.trigger('submit')
    await flushPromises()

    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('正在生成能力画像')
    expect(trackMock).toHaveBeenCalledWith('onboarding_started', undefined, {
      ui_feedback_variant: 'card_skeleton',
    })

    deferred.resolve({ profile: sampleProfile })
    await flushPromises()

    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(false)
    expect(trackMock).toHaveBeenCalledWith(
      'onboarding_completed',
      undefined,
      expect.objectContaining({
        ui_feedback_variant: 'card_skeleton',
        loading_duration_ms: expect.any(Number),
      })
    )
    expect(navigateToMock).toHaveBeenCalledWith('/identity-models')
  })

  it('shows error and hides loading feedback when submit fails', async () => {
    completeOnboardingMock.mockRejectedValueOnce(new Error('后端异常'))

    const OnboardingPage = (await import('../../app/pages/onboarding.vue')).default
    const wrapper = await mountSuspended(OnboardingPage)
    const form = wrapper.find('form')
    await form.trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('后端异常')
    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(false)
    expect(navigateToMock).not.toHaveBeenCalled()
  })
})
