import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import type { MvpFlowState } from '../../app/types/flow'

const selectIdentityMock = vi.hoisted(() => vi.fn())
const generateIdentityModelsMock = vi.hoisted(() => vi.fn())
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
  identityModels: [
    {
      id: 'identity_1',
      title: '职场效率解剖师',
      targetAudiencePain: '表达效率低',
      contentPillars: ['职业问题拆解', '方法模板演示', '复盘体系'],
      toneStyleKeywords: ['克制', '结构化'],
      toneExamples: ['先给结论，再展开步骤。', '每段只解释一个动作。'],
      longTermViews: ['观点1', '观点2', '观点3', '观点4', '观点5'],
      differentiation: '真实周复盘',
      growthPath: { firstQuarter: '先做内容结构', yearOne: '形成产品化能力' },
      monetizationValidationOrder: ['私域线索', '咨询'],
      monetizationMap: '私域线索 -> 咨询',
      riskBoundaries: ['避免夸大收益'],
    },
    {
      id: 'identity_2',
      title: '表达系统搭建者',
      targetAudiencePain: '内容框架不稳定',
      contentPillars: ['表达框架', '案例拆解', '内容复盘'],
      toneStyleKeywords: ['务实'],
      toneExamples: [
        '结论先行，再给依据。',
        '每次只说一个重点。',
        '结尾给出行动建议。',
        '先定义问题边界。',
        '避免情绪化用词。',
      ],
      longTermViews: ['观点1', '观点2', '观点3', '观点4', '观点5'],
      differentiation: '方法论沉淀',
      growthPath: { firstQuarter: '稳定更新', yearOne: '形成矩阵' },
      monetizationValidationOrder: ['训练营'],
      monetizationMap: '训练营',
      riskBoundaries: ['不虚假承诺'],
    },
  ],
  selectedPrimaryId: undefined,
  selectedBackupId: undefined,
  draftToCheck: '',
  events: [],
})

const state = ref<MvpFlowState>(createFlowState())

const createDeferred = <T>() => {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

vi.mock('../../app/services/api/client', () => ({
  useApiClient: () => ({
    generateIdentityModels: generateIdentityModelsMock,
    selectIdentity: selectIdentityMock,
  }),
}))

mockNuxtImport('useAnalytics', () => () => ({
  track: trackMock,
}))

mockNuxtImport('useMvpFlow', () => () => ({
  state,
}))

mockNuxtImport('navigateTo', () => navigateToMock)

describe('identity models page', () => {
  beforeEach(() => {
    state.value = createFlowState()
    generateIdentityModelsMock.mockReset()
    generateIdentityModelsMock.mockResolvedValue({ models: [] })
    selectIdentityMock.mockReset()
    selectIdentityMock.mockResolvedValue({ selected: true })
    trackMock.mockReset()
    trackMock.mockResolvedValue({})
    navigateToMock.mockReset()
    navigateToMock.mockResolvedValue(undefined)
  })

  it('renders tone style keywords and tone examples', async () => {
    const IdentityModelsPage = (await import('../../app/pages/identity-models.vue')).default
    const wrapper = await mountSuspended(IdentityModelsPage)

    expect(wrapper.text()).toContain('语气关键词')
    expect(wrapper.text()).toContain('克制')
    expect(wrapper.text()).toContain('先给结论，再展开步骤。')
  })

  it('shows loading feedback during generation and blocks duplicate trigger', async () => {
    state.value = {
      ...createFlowState(),
      profile: {
        skillStack: ['技能'],
        energyCurve: ['兴趣'],
        cognitiveStyle: '结构化',
        valueBoundaries: ['边界'],
        riskTolerance: 'medium',
        weeklyHours: 6,
        recommendedPlatforms: ['公众号'],
      },
      identityModels: [],
    }
    const deferred = createDeferred<{ models: MvpFlowState['identityModels'] }>()
    generateIdentityModelsMock.mockReturnValueOnce(deferred.promise)

    const IdentityModelsPage = (await import('../../app/pages/identity-models.vue')).default
    const wrapper = await mountSuspended(IdentityModelsPage)
    const generateButton = wrapper.findAll('button').find(button => button.text().includes('立即生成身份模型'))

    expect(generateButton).toBeTruthy()
    await generateButton!.trigger('click')
    await generateButton!.trigger('click')
    await flushPromises()

    expect(generateIdentityModelsMock).toHaveBeenCalledTimes(1)
    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('正在生成身份模型')

    deferred.resolve({ models: createFlowState().identityModels })
    await flushPromises()

    expect(wrapper.find('[data-testid="generation-feedback-card"]').exists()).toBe(false)
    expect(trackMock).toHaveBeenCalledWith(
      'identity_models_generated',
      undefined,
      expect.objectContaining({
        ui_feedback_variant: 'card_skeleton',
        loading_duration_ms: expect.any(Number),
      })
    )
  })

  it('renders primary and backup badges in card header without clipped offset classes', async () => {
    const IdentityModelsPage = (await import('../../app/pages/identity-models.vue')).default
    const wrapper = await mountSuspended(IdentityModelsPage)

    const primaryButtons = wrapper.findAll('button').filter(button => button.text().includes('设为主身份'))
    await primaryButtons[0]!.trigger('click')
    await flushPromises()

    const primaryBadge = wrapper.find('[data-testid="identity-card-primary-badge"]')
    expect(primaryBadge.exists()).toBe(true)
    expect(primaryBadge.text()).toContain('主身份')

    const backupButtons = wrapper.findAll('button').filter(button => button.text().includes('设为备身份'))
    await backupButtons[1]!.trigger('click')
    await flushPromises()

    const backupBadge = wrapper.find('[data-testid="identity-card-backup-badge"]')
    expect(backupBadge.exists()).toBe(true)
    expect(backupBadge.text()).toContain('备身份')

    const html = wrapper.html()
    expect(html).not.toContain('-top-3')
    expect(html).not.toContain('-right-3')
  })

  it('shows warning for primary tone examples below 5 and still allows save', async () => {
    const IdentityModelsPage = (await import('../../app/pages/identity-models.vue')).default
    const wrapper = await mountSuspended(IdentityModelsPage)

    const primaryButtons = wrapper.findAll('button').filter(button => button.text().includes('设为主身份'))
    await primaryButtons[0]!.trigger('click')
    await flushPromises()

    const backupButtons = wrapper.findAll('button').filter(button => button.text().includes('设为备身份'))
    await backupButtons[1]!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('当前主身份仅有 2 条有效语气示例，建议补齐到 5 条以上。')

    const saveButton = wrapper.findAll('button').find(button => button.text().includes('保存选择并继续'))
    expect(saveButton).toBeTruthy()
    await saveButton!.trigger('click')
    await flushPromises()

    expect(selectIdentityMock).toHaveBeenCalledWith({
      primaryId: 'identity_1',
      backupId: 'identity_2',
    })
    expect(trackMock).toHaveBeenCalledWith(
      'identity_selected',
      'identity_1',
      expect.objectContaining({
        tone_examples_count: 2,
        tone_examples_below_5: true,
      })
    )
    expect(navigateToMock).toHaveBeenCalledWith('/persona-constitution')
  })
})
