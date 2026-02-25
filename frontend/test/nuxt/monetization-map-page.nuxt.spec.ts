import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { computed, ref } from 'vue'
import type { IdentityModelCard, MvpFlowState, PersonaConstitution } from '../../app/types/flow'

const generateMonetizationMapMock = vi.hoisted(() => vi.fn())
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
  experiments: [
    {
      id: 'exp_1',
      hypothesis: '更具体标题提升收藏率',
      variables: ['标题', '开头'],
      executionCycle: '7d',
      result: '收藏率提升',
      conclusion: '保留具体收益型标题',
      status: 'completed',
    },
  ],
  draftToCheck: '',
  events: [],
})

const state = ref<MvpFlowState>(createFlowState())
const selectedPrimaryModel = computed(() =>
  state.value.identityModels.find(model => model.id === state.value.selectedPrimaryId)
)

vi.mock('../../app/services/api/client', () => ({
  useApiClient: () => ({
    generateMonetizationMap: generateMonetizationMapMock,
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

describe('monetization map page', () => {
  beforeEach(() => {
    state.value = createFlowState()
    generateMonetizationMapMock.mockReset()
    generateMonetizationMapMock.mockResolvedValue({
      monetizationMap: {
        primaryPath: '咨询服务 -> 小班营',
        backupPath: '模板产品',
        weeks: [
          {
            weekNo: 1,
            goal: 'goal-1',
            task: 'task-1',
            deliverable: 'deliverable-1',
            validationMetric: 'metric-1',
          },
        ],
      },
    })
    trackMock.mockReset()
    trackMock.mockResolvedValue({})
  })

  it('generates monetization map and renders weekly plan table', async () => {
    const Page = (await import('../../app/pages/monetization-map.vue')).default
    const wrapper = await mountSuspended(Page)

    const button = wrapper.findAll('button').find(item => item.text().includes('一键生成变现路线图'))
    expect(button).toBeTruthy()

    await button!.trigger('click')
    await flushPromises()

    expect(generateMonetizationMapMock).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('12 周执行计划')
    expect(wrapper.text()).toContain('goal-1')
    expect(trackMock).toHaveBeenCalledWith(
      'monetization_plan_started',
      primaryModel.id,
      expect.objectContaining({ weeks: 1 })
    )
  })
})
