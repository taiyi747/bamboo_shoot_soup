import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { computed, ref } from 'vue'
import type { IdentityModelCard, MvpFlowState, PersonaConstitution } from '../../app/types/flow'

const generatePersonaConstitutionMock = vi.hoisted(() => vi.fn())
const navigateToMock = vi.hoisted(() => vi.fn())

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
  draftToCheck: '',
  events: [],
})

const sampleConstitution: PersonaConstitution = {
  commonWords: ['拆解', '验证'],
  forbiddenWords: ['暴富'],
  sentencePreferences: ['先结论后步骤'],
  immutablePositions: ['不做虚假承诺'],
  narrativeMainline: '从执行者到系统构建者',
  growthArc: [{ stage: '0-3月', storyTemplate: '从混乱到稳定输出' }],
}

const state = ref<MvpFlowState>(createFlowState())
const selectedPrimaryModel = computed(() =>
  state.value.identityModels.find(model => model.id === state.value.selectedPrimaryId)
)

vi.mock('../../app/services/api/client', () => ({
  useApiClient: () => ({
    generatePersonaConstitution: generatePersonaConstitutionMock,
  }),
}))

mockNuxtImport('useMvpFlow', () => () => ({
  state,
  selectedPrimaryModel,
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

describe('persona constitution page', () => {
  beforeEach(() => {
    state.value = createFlowState()
    generatePersonaConstitutionMock.mockReset()
    generatePersonaConstitutionMock.mockResolvedValue({ constitution: sampleConstitution })
    navigateToMock.mockReset()
    navigateToMock.mockResolvedValue(undefined)
  })

  it('shows loading feedback and renders constitution fields after success', async () => {
    const deferred = createDeferred<{ constitution: PersonaConstitution }>()
    generatePersonaConstitutionMock.mockReturnValueOnce(deferred.promise)

    const PersonaConstitutionPage = (await import('../../app/pages/persona-constitution.vue')).default
    const wrapper = await mountSuspended(PersonaConstitutionPage)
    const generateButton = wrapper.findAll('button').find(button => button.text().includes('立即生成人格宪法'))

    expect(generateButton).toBeTruthy()
    await generateButton!.trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('正在生成人格宪法')

    deferred.resolve({ constitution: sampleConstitution })
    await flushPromises()

    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('叙事与成长路径')
  })

  it('shows error and hides feedback when generation fails', async () => {
    generatePersonaConstitutionMock.mockRejectedValueOnce(new Error('人格宪法生成失败'))

    const PersonaConstitutionPage = (await import('../../app/pages/persona-constitution.vue')).default
    const wrapper = await mountSuspended(PersonaConstitutionPage)
    const generateButton = wrapper.findAll('button').find(button => button.text().includes('立即生成人格宪法'))

    await generateButton!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('人格宪法生成失败')
    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(false)
  })
})
