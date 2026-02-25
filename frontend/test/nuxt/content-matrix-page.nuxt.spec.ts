import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { computed, ref } from 'vue'
import type { ContentMatrix, IdentityModelCard, MvpFlowState, PersonaConstitution } from '../../app/types/flow'

const generateContentMatrixMock = vi.hoisted(() => vi.fn())

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

const sampleMatrix: ContentMatrix = {
  pillars: [
    {
      pillar: '职业问题拆解',
      topics: ['topic-1', 'topic-2'],
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
  experiments: [],
  selectedPrimaryId: primaryModel.id,
  persona,
  consistencyCheck: {
    deviations: ['d1'],
    reasons: ['r1'],
    suggestions: ['s1'],
    score: 80,
  },
  draftToCheck: '',
  events: [],
})

const state = ref<MvpFlowState>(createFlowState())
const selectedPrimaryModel = computed(() =>
  state.value.identityModels.find(model => model.id === state.value.selectedPrimaryId)
)

vi.mock('../../app/services/api/client', () => ({
  useApiClient: () => ({
    generateContentMatrix: generateContentMatrixMock,
  }),
}))

mockNuxtImport('useMvpFlow', () => () => ({
  state,
  selectedPrimaryModel,
}))

mockNuxtImport('navigateTo', () => vi.fn())

describe('content matrix page', () => {
  beforeEach(() => {
    state.value = createFlowState()
    generateContentMatrixMock.mockReset()
    generateContentMatrixMock.mockResolvedValue({ contentMatrix: sampleMatrix })
  })

  it('renders generated content matrix', async () => {
    const Page = (await import('../../app/pages/content-matrix.vue')).default
    const wrapper = await mountSuspended(Page)

    const generateButton = wrapper.findAll('button').find(button => button.text().includes('一键生成内容矩阵'))
    expect(generateButton).toBeTruthy()

    await generateButton!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('选题池')
    expect(wrapper.text()).toContain('topic-1')
    expect(wrapper.text()).toContain('rewrite-a')
  })
})
