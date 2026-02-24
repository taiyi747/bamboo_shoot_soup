import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { computed, ref } from 'vue'
import type { IdentityModelCard, LaunchKit, MvpFlowState, PersonaConstitution } from '../../app/types/flow'

const generateLaunchKitMock = vi.hoisted(() => vi.fn())
const trackMock = vi.hoisted(() => vi.fn())

const primaryModel: IdentityModelCard = {
  id: 'identity_1',
  title: '职场效率解剖师',
  targetAudiencePain: '表达效率低',
  contentPillars: ['职业问题拆解', '方法模板演示', '复盘体系'],
  toneStyleKeywords: ['克制', '结构化'],
  toneExamples: ['先给结论，再展开步骤。'],
  longTermViews: ['观点1', '观点2', '观点3', '观点4', '观点5'],
  differentiation: '真实周复盘',
  growthPath: { firstQuarter: '先做内容结构', yearOne: '形成产品化能力' },
  monetizationValidationOrder: ['私域线索', '咨询'],
  monetizationMap: '私域线索 -> 咨询',
  riskBoundaries: ['避免夸大收益'],
}

const persona: PersonaConstitution = {
  commonWords: ['拆解', '验证'],
  forbiddenWords: ['暴富'],
  sentencePreferences: ['先结论后步骤'],
  immutablePositions: ['不做虚假承诺'],
  narrativeMainline: '从执行者到系统构建者',
  growthArc: [{ stage: '0-3月', storyTemplate: '从混乱到稳定输出' }],
}

const sampleLaunchKit: LaunchKit = {
  days: [
    { day: 1, theme: '主题1', draftOutline: '大纲1', opening: '开头1' },
    { day: 2, theme: '主题2', draftOutline: '大纲2', opening: '开头2' },
  ],
  sustainableColumns: ['栏目1', '栏目2', '栏目3'],
  growthExperiment: {
    hypothesis: '假设',
    variables: ['标题', '封面'],
    executionCycle: '7天',
    successMetric: '收藏率',
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
  contentMatrixes: [],
  experiments: [],
  monetizationMaps: [],
  identityPortfolios: [],
  simulatorEvaluations: [],
  viewpointAssets: [],
  events: [],
})

const state = ref<MvpFlowState>(createFlowState())
const selectedPrimaryModel = computed(() =>
  state.value.identityModels.find(model => model.id === state.value.selectedPrimaryId)
)

vi.mock('../../app/services/api/client', () => ({
  useApiClient: () => ({
    generateLaunchKit: generateLaunchKitMock,
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
    trackMock.mockReset()
    trackMock.mockResolvedValue({})
  })

  it('shows loading feedback and blocks duplicate generation requests', async () => {
    const deferred = createDeferred<{ launchKit: LaunchKit }>()
    generateLaunchKitMock.mockReturnValueOnce(deferred.promise)

    const LaunchKitPage = (await import('../../app/pages/launch-kit.vue')).default
    const wrapper = await mountSuspended(LaunchKitPage)
    const generateButton = wrapper.findAll('button').find(button => button.text().includes('一键生成 7 天启动包'))

    expect(generateButton).toBeTruthy()
    await generateButton!.trigger('click')
    await generateButton!.trigger('click')
    await flushPromises()

    expect(generateLaunchKitMock).toHaveBeenCalledTimes(1)
    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('正在生成 7-Day Launch Kit')

    deferred.resolve({ launchKit: sampleLaunchKit })
    await flushPromises()

    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('首周内容排期 (Day 1-7)')
    expect(trackMock).toHaveBeenCalledWith(
      'launch_kit_generated',
      primaryModel.id,
      expect.objectContaining({
        ui_feedback_variant: 'card_skeleton',
        loading_duration_ms: expect.any(Number),
      })
    )
  })

  it('shows error and hides feedback when generation fails', async () => {
    generateLaunchKitMock.mockRejectedValueOnce(new Error('启动包生成失败'))

    const LaunchKitPage = (await import('../../app/pages/launch-kit.vue')).default
    const wrapper = await mountSuspended(LaunchKitPage)
    const generateButton = wrapper.findAll('button').find(button => button.text().includes('一键生成 7 天启动包'))

    await generateButton!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('启动包生成失败')
    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(false)
  })
})
