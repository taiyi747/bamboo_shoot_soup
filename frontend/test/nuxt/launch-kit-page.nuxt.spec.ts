import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { computed, ref } from 'vue'
import type { IdentityModelCard, LaunchKit, MvpFlowState, PersonaConstitution } from '../../app/types/flow'

const generateLaunchKitMock = vi.hoisted(() => vi.fn())
const generateLaunchKitDayArticleMock = vi.hoisted(() => vi.fn())
const trackMock = vi.hoisted(() => vi.fn())

const primaryModel: IdentityModelCard = {
  id: 'identity_1',
  title: 'Primary Identity',
  targetAudiencePain: 'Pain',
  contentPillars: ['P1', 'P2', 'P3'],
  toneStyleKeywords: ['calm', 'clear'],
  toneExamples: ['e1', 'e2', 'e3', 'e4', 'e5'],
  longTermViews: ['v1', 'v2', 'v3', 'v4', 'v5'],
  differentiation: 'Different',
  growthPath: { firstQuarter: 'q1', yearOne: 'y1' },
  monetizationValidationOrder: ['m1'],
  monetizationMap: 'm1',
  riskBoundaries: ['r1'],
}

const persona: PersonaConstitution = {
  commonWords: ['clarity'],
  forbiddenWords: ['promise'],
  sentencePreferences: ['one idea per paragraph'],
  immutablePositions: ['no fake claims'],
  narrativeMainline: 'Build trust over time',
  growthArc: [{ stage: '0-3m', storyTemplate: 'chaos to stable output' }],
}

const sampleLaunchKit: LaunchKit = {
  days: [
    { day: 1, theme: 'Theme 1', draftOutline: 'Outline 1', opening: 'Opening 1' },
    { day: 2, theme: 'Theme 2', draftOutline: 'Outline 2', opening: 'Opening 2' },
  ],
  sustainableColumns: ['Column 1', 'Column 2', 'Column 3'],
  growthExperiment: {
    hypothesis: 'Hypothesis',
    variables: ['Title', 'Cover'],
    executionCycle: '7d',
    successMetric: 'Save rate',
  },
}

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
  identityModels: [primaryModel],
  selectedPrimaryId: primaryModel.id,
  persona,
  draftToCheck: '',
  events: [],
})

const state = ref<MvpFlowState>(createFlowState())
const selectedPrimaryModel = computed(() =>
  state.value.identityModels.find(model => model.id === state.value.selectedPrimaryId)
)

vi.mock('../../app/services/api/client', () => ({
  useApiClient: () => ({
    generateLaunchKit: generateLaunchKitMock,
    generateLaunchKitDayArticle: generateLaunchKitDayArticleMock,
  }),
}))

mockNuxtImport('useAnalytics', () => () => ({
  track: trackMock,
}))

mockNuxtImport('useMvpFlow', () => () => ({
  state,
  selectedPrimaryModel,
}))

const createDeferred = <T>() => {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

describe('launch kit page', () => {
  beforeEach(() => {
    state.value = createFlowState()
    generateLaunchKitMock.mockReset()
    generateLaunchKitMock.mockResolvedValue({ launchKit: sampleLaunchKit })
    generateLaunchKitDayArticleMock.mockReset()
    generateLaunchKitDayArticleMock.mockResolvedValue({
      dayNo: 1,
      title: 'Day 1 Article',
      markdown: '# Day 1\n\nContent body',
    })
    trackMock.mockReset()
    trackMock.mockResolvedValue({})
  })

  it('shows loading feedback and blocks duplicate launch-kit generation requests', async () => {
    const deferred = createDeferred<{ launchKit: LaunchKit }>()
    generateLaunchKitMock.mockReturnValueOnce(deferred.promise)

    const LaunchKitPage = (await import('../../app/pages/launch-kit.vue')).default
    const wrapper = await mountSuspended(LaunchKitPage)
    const generateButton = wrapper.find('[data-testid="launch-kit-generate-button"]')

    expect(generateButton.exists()).toBe(true)
    await generateButton.trigger('click')
    await generateButton.trigger('click')
    await flushPromises()

    expect(generateLaunchKitMock).toHaveBeenCalledTimes(1)
    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(true)

    deferred.resolve({ launchKit: sampleLaunchKit })
    await flushPromises()

    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Week 1 Schedule (Day 1-7)')
    expect(trackMock).toHaveBeenCalledWith(
      'launch_kit_generated',
      primaryModel.id,
      expect.objectContaining({
        ui_feedback_variant: 'card_skeleton',
        loading_duration_ms: expect.any(Number),
        article_cache_cleared: true,
      })
    )
  })

  it('shows error and hides feedback when launch-kit generation fails', async () => {
    generateLaunchKitMock.mockRejectedValueOnce(new Error('Launch kit generation failed.'))

    const LaunchKitPage = (await import('../../app/pages/launch-kit.vue')).default
    const wrapper = await mountSuspended(LaunchKitPage)
    const generateButton = wrapper.find('[data-testid="launch-kit-generate-button"]')

    await generateButton.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Launch kit generation failed.')
    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(false)
  })

  it('uses in-memory cache after first day article success and still opens modal', async () => {
    state.value.launchKit = sampleLaunchKit

    const LaunchKitPage = (await import('../../app/pages/launch-kit.vue')).default
    const wrapper = await mountSuspended(LaunchKitPage)

    const dayOneButton = wrapper.find('[data-testid="day-article-generate-1"]')
    await dayOneButton.trigger('click')
    await flushPromises()

    expect(generateLaunchKitDayArticleMock).toHaveBeenCalledTimes(1)
    expect(wrapper.find('[data-testid="day-article-modal"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="day-article-title"]').text()).toContain('Day 1 Article')

    await wrapper.find('[data-testid="day-article-close"]').trigger('click')
    await flushPromises()

    await dayOneButton.trigger('click')
    await flushPromises()

    expect(generateLaunchKitDayArticleMock).toHaveBeenCalledTimes(1)
    expect(wrapper.find('[data-testid="day-article-modal"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="day-article-preview"]').text()).toContain('Content body')
  })

  it('clears day article cache after launch-kit regeneration success', async () => {
    state.value.launchKit = sampleLaunchKit

    const LaunchKitPage = (await import('../../app/pages/launch-kit.vue')).default
    const wrapper = await mountSuspended(LaunchKitPage)

    const dayOneButton = wrapper.find('[data-testid="day-article-generate-1"]')
    await dayOneButton.trigger('click')
    await flushPromises()
    expect(generateLaunchKitDayArticleMock).toHaveBeenCalledTimes(1)

    const regenerateButton = wrapper.find('[data-testid="launch-kit-regenerate-button"]')
    await regenerateButton.trigger('click')
    await flushPromises()

    await dayOneButton.trigger('click')
    await flushPromises()

    expect(generateLaunchKitDayArticleMock).toHaveBeenCalledTimes(2)
  })

  it('does not cache failed day article response and retries next click', async () => {
    state.value.launchKit = sampleLaunchKit
    generateLaunchKitDayArticleMock
      .mockRejectedValueOnce(new Error('Day article generation failed.'))
      .mockResolvedValueOnce({
        dayNo: 1,
        title: 'Day 1 Article Retry',
        markdown: '# Retry',
      })

    const LaunchKitPage = (await import('../../app/pages/launch-kit.vue')).default
    const wrapper = await mountSuspended(LaunchKitPage)

    const dayOneButton = wrapper.find('[data-testid="day-article-generate-1"]')
    await dayOneButton.trigger('click')
    await flushPromises()

    expect(generateLaunchKitDayArticleMock).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Day article generation failed.')

    await dayOneButton.trigger('click')
    await flushPromises()

    expect(generateLaunchKitDayArticleMock).toHaveBeenCalledTimes(2)
    expect(wrapper.find('[data-testid="day-article-title"]').text()).toContain('Day 1 Article Retry')
  })
})
