import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { computed, ref } from 'vue'
import type { ContentMatrix, IdentityModelCard, MvpFlowState, PersonaConstitution } from '../../app/types/flow'

const createExperimentMock = vi.hoisted(() => vi.fn())
const getExperimentsMock = vi.hoisted(() => vi.fn())
const updateExperimentResultMock = vi.hoisted(() => vi.fn())
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

const contentMatrix: ContentMatrix = {
  pillars: [
    {
      pillar: '职业问题拆解',
      topics: ['topic-1'],
      platformRewrites: {
        xiaohongshu: ['rewrite-a'],
        wechat: ['rewrite-b'],
        video_channel: ['rewrite-c'],
      },
    },
  ],
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
  contentMatrix,
  experiments: [],
  draftToCheck: '',
  events: [],
})

const state = ref<MvpFlowState>(createFlowState())
const selectedPrimaryModel = computed(() =>
  state.value.identityModels.find(model => model.id === state.value.selectedPrimaryId)
)

vi.mock('../../app/services/api/client', () => ({
  useApiClient: () => ({
    createExperiment: createExperimentMock,
    getExperiments: getExperimentsMock,
    updateExperimentResult: updateExperimentResultMock,
  }),
}))

mockNuxtImport('useMvpFlow', () => () => ({
  state,
  selectedPrimaryModel,
}))

mockNuxtImport('useAnalytics', () => () => ({
  track: trackMock,
}))

mockNuxtImport('navigateTo', () => vi.fn())

describe('experiments page', () => {
  beforeEach(() => {
    state.value = createFlowState()
    createExperimentMock.mockReset()
    createExperimentMock.mockResolvedValue({ experimentId: 'exp_1' })
    getExperimentsMock.mockReset()
    getExperimentsMock.mockResolvedValue({
      experiments: [
        {
          id: 'exp_1',
          hypothesis: '更具体标题提升收藏率',
          variables: ['标题', '开头'],
          executionCycle: '7d',
          result: '',
          conclusion: '',
          status: 'planned',
        },
      ],
    })
    updateExperimentResultMock.mockReset()
    updateExperimentResultMock.mockResolvedValue({ updated: true })
    trackMock.mockReset()
    trackMock.mockResolvedValue({})
  })

  it('creates experiment and renders list', async () => {
    const Page = (await import('../../app/pages/experiments.vue')).default
    const wrapper = await mountSuspended(Page)

    const form = wrapper.findComponent({ name: 'UForm' })
    expect(form.exists()).toBe(true)

    form.vm.$emit('submit', {
      data: {
        hypothesis: '更具体标题提升收藏率',
        variables: '标题,开头',
        executionCycle: '7d',
      },
    })
    await flushPromises()

    expect(createExperimentMock).toHaveBeenCalledTimes(1)
    expect(getExperimentsMock).toHaveBeenCalled()
    expect(wrapper.text()).toContain('更具体标题提升收藏率')
    expect(trackMock).toHaveBeenCalledWith(
      'experiment_created',
      primaryModel.id,
      expect.objectContaining({ experiments_count: expect.any(Number) })
    )
  })
})
