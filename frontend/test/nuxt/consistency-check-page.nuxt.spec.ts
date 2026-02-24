import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { computed, ref } from 'vue'
import type { ConsistencyCheckResult, IdentityModelCard, MvpFlowState, PersonaConstitution } from '../../app/types/flow'

const runConsistencyCheckMock = vi.hoisted(() => vi.fn())
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

const sampleResult: ConsistencyCheckResult = {
  deviations: ['偏离项1'],
  reasons: ['原因1'],
  suggestions: ['建议1'],
  score: 78,
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
    runConsistencyCheck: runConsistencyCheckMock,
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

describe('consistency check page', () => {
  beforeEach(() => {
    state.value = createFlowState()
    runConsistencyCheckMock.mockReset()
    runConsistencyCheckMock.mockResolvedValue({ result: sampleResult })
    trackMock.mockReset()
    trackMock.mockResolvedValue({})
  })

  it('shows loading feedback and result after successful check', async () => {
    const deferred = createDeferred<{ result: ConsistencyCheckResult }>()
    runConsistencyCheckMock.mockReturnValueOnce(deferred.promise)

    const ConsistencyCheckPage = (await import('../../app/pages/consistency-check.vue')).default
    const wrapper = await mountSuspended(ConsistencyCheckPage)
    const form = wrapper.findComponent({ name: 'UForm' })
    expect(form.exists()).toBe(true)
    form.vm.$emit('submit', { data: { draft: 'a'.repeat(80) } })
    await flushPromises()

    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('正在执行一致性检查')

    deferred.resolve({ result: sampleResult })
    await flushPromises()

    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Agent 诊断报告')
    expect(trackMock).toHaveBeenCalledWith(
      'consistency_check_triggered',
      primaryModel.id,
      expect.objectContaining({
        ui_feedback_variant: 'card_skeleton',
        loading_duration_ms: expect.any(Number),
      })
    )
  })

  it('shows error and hides feedback when check fails', async () => {
    runConsistencyCheckMock.mockRejectedValueOnce(new Error('一致性检查失败'))

    const ConsistencyCheckPage = (await import('../../app/pages/consistency-check.vue')).default
    const wrapper = await mountSuspended(ConsistencyCheckPage)
    const form = wrapper.findComponent({ name: 'UForm' })
    form.vm.$emit('submit', { data: { draft: 'b'.repeat(80) } })
    await flushPromises()

    expect(wrapper.text()).toContain('一致性检查失败')
    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(false)
  })
})
