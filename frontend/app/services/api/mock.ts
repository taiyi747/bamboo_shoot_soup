import type { ApiClient, RunConsistencyCheckRequest } from './types'
import type { GrowthArcItem, IdentityModelCard, OnboardingProfile } from '../../types/flow'

const pause = (ms = 180) => new Promise(resolve => setTimeout(resolve, ms))

const newId = (prefix: string) => `${prefix}_${Math.random().toString(36).slice(2, 10)}`

const pick = <T>(items: T[], count: number): T[] => items.slice(0, count)

const buildGrowthArc = (title: string): GrowthArcItem[] => [
  { stage: '0-4 周', storyTemplate: `从个人观察切入，建立 ${title} 的基础可信度。` },
  { stage: '2-3 月', storyTemplate: `持续发布案例复盘，形成 ${title} 的稳定栏目。` },
  { stage: '3-12 月', storyTemplate: `沉淀方法论与服务产品，让身份具备可复制收益。` },
]

const buildModels = (profile: OnboardingProfile): IdentityModelCard[] => {
  const candidates: Array<Pick<IdentityModelCard, 'title' | 'targetAudiencePain' | 'differentiation'>> = [
    {
      title: '职场效率解剖师',
      targetAudiencePain: '有能力但表达效率低，内容难以持续产出。',
      differentiation: '用真实周复盘替代鸡汤，强调可复制 SOP 与交付模板。',
    },
    {
      title: '行业趋势翻译官',
      targetAudiencePain: '看得懂趋势新闻，但不知道如何落地到工作。',
      differentiation: '每条观点都附带“本周可执行动作”，降低认知到执行距离。',
    },
    {
      title: '高客单咨询产品化教练',
      targetAudiencePain: '服务能力强，但缺少稳定获客与叙事系统。',
      differentiation: '把咨询案例拆成公开方法资产，构建低门槛引流入口。',
    },
  ]

  const pillars = [
    '职业问题拆解',
    '方法模板演示',
    '失败复盘与修正',
    '行业趋势应用',
    '个人成长纪实',
  ]

  return candidates.map((item, idx) => ({
    id: newId(`identity_${idx + 1}`),
    title: item.title,
    targetAudiencePain: item.targetAudiencePain,
    contentPillars: pick(pillars, 4),
    toneStyleKeywords: ['克制', '结构化', '可落地', '不夸张', '反空话'],
    toneExamples: [
      '先说结论，再给一段你今天就能执行的动作。',
      '我会告诉你为什么这样做，而不只是给你模板。',
      '这不是万能解法，但它适合时间有限的上班族。',
      '如果你只能做一件事，先完成这个最小版本。',
      '每次复盘都要落到“下周行动”而不是感受。',
    ],
    longTermViews: [
      '稳定输出比偶发爆款更重要。',
      '方法资产要能被反复复用。',
      '信任来自长期一致，而不是高频刺激。',
      '内容要服务真实业务目标。',
      '风险边界要先于增长冲动。',
    ],
    differentiation: item.differentiation,
    growthPath: {
      firstQuarter: '完成 24 条结构化内容，验证 2 个固定栏目。',
      yearOne: '形成“公开内容 + 服务产品”双轮结构并持续迭代。',
    },
    monetizationValidationOrder: ['私域线索验证', '小额咨询验证', '标准化服务验证'],
    monetizationMap: '公开内容 -> 低门槛诊断 -> 标准化咨询包 -> 长期顾问',
    riskBoundaries: [
      `避免触碰与 ${profile.riskTolerance === 'low' ? '高争议公共议题' : '无证据断言'} 相关表达`,
      '不得使用无法核实的数据结论',
      '不得冒充或暗示平台官方身份',
    ],
  }))
}

const checkConsistency = (input: RunConsistencyCheckRequest) => {
  const deviations: string[] = []
  const reasons: string[] = []
  const suggestions: string[] = []

  if (input.draft.length < 120) {
    deviations.push('草稿信息密度偏低，难以支撑“可执行性”。')
    reasons.push('篇幅偏短，缺少动作步骤。')
    suggestions.push('补充 3 个具体动作和 1 个验证标准。')
  }

  if (!input.identityModel.toneStyleKeywords.some(k => input.draft.includes(k))) {
    deviations.push('草稿未体现身份既定语气关键词。')
    reasons.push('表达风格与人格宪法脱节。')
    suggestions.push('补充“先结论后步骤”的句式，减少空泛修饰。')
  }

  const riskRegex = /(违法|冒充|侵权|保证收益|内幕|代发|虚假)/
  const riskWarning = riskRegex.test(input.draft)
    ? '草稿触发风险边界关键词，请先修改后发布。'
    : undefined

  const score = Math.max(25, 92 - deviations.length * 18 - (riskWarning ? 22 : 0))

  return {
    deviations,
    reasons,
    suggestions,
    riskWarning,
    score,
  }
}

export const mockApiClient: ApiClient = {
  async createOnboardingSession() {
    await pause()
    return { sessionId: newId('session') }
  },

  async completeOnboarding({ input }) {
    await pause()
    return {
      profile: {
        skillStack: input.skills,
        energyCurve: input.interests,
        cognitiveStyle: input.cognitiveStyle,
        valueBoundaries: input.valueBoundaries,
        riskTolerance: input.riskTolerance,
        weeklyHours: input.weeklyHours,
        recommendedPlatforms: ['小红书', '公众号', '视频号'],
      },
    }
  },

  async generateIdentityModels({ profile }) {
    await pause(260)
    return { models: buildModels(profile) }
  },

  async selectIdentity() {
    await pause()
    return { selected: true }
  },

  async generatePersonaConstitution({ identityModel }) {
    await pause(220)
    return {
      constitution: {
        commonWords: ['结论先行', '可执行', '复盘', '本周动作', '最小版本'],
        forbiddenWords: ['躺赚', '无脑', '闭眼冲', '唯一真相'],
        sentencePreferences: ['先结论后拆解', '每段给动作', '少形容词，多证据'],
        immutablePositions: [
          '不制造焦虑来换取流量',
          '不提供无法验证的收益承诺',
          '尊重平台规则和法律边界',
        ],
        narrativeMainline: `${identityModel.title}：把专业经验转化为可执行内容资产。`,
        growthArc: buildGrowthArc(identityModel.title),
      },
    }
  },

  async generateLaunchKit({ identityModel }) {
    await pause(260)
    return {
      launchKit: {
        days: Array.from({ length: 7 }).map((_, idx) => ({
          day: idx + 1,
          theme: `Day ${idx + 1}：${identityModel.title} 启动主题`,
          draftOutline: '痛点场景 -> 拆解框架 -> 3 步动作 -> 本周验证指标',
          opening: '如果你最近也遇到这个问题，这条内容给你一个可执行起点。',
        })),
        sustainableColumns: ['每周问题拆解', '真实案例复盘', '工具模板共创'],
        growthExperiment: {
          hypothesis: '标题中加入“可执行动作”能提升收藏率。',
          variables: ['标题 A/B', '发布时间', '结尾提问方式'],
          executionCycle: '7 天',
          successMetric: '收藏率提升 >= 20%',
        },
      },
    }
  },

  async runConsistencyCheck(input) {
    await pause(200)
    return { result: checkConsistency(input) }
  },

  async trackEvent() {
    return { accepted: true }
  },
}
