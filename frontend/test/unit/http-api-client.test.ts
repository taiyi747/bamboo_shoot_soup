import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createHttpApiClient } from '../../app/services/api/http'

describe('createHttpApiClient', () => {
  beforeEach(() => {
    vi.unstubAllGlobals()
  })

  it('maps onboarding requests/responses with /v1 endpoints', async () => {
    const fetchMock = vi.fn(async (path: string) => {
      if (path === '/v1/onboarding/sessions') {
        return { id: 'session_1' }
      }
      if (path === '/v1/onboarding/sessions/session_1/complete') {
        return { session_id: 'session_1', status: 'completed', profile_id: 'profile_1' }
      }
      if (path === '/v1/onboarding/sessions/session_1/profile') {
        return {
          skill_stack_json: '["写作","项目管理"]',
          interest_energy_curve_json: '[{"interest":"职场策略"},{"interest":"案例复盘"}]',
          cognitive_style: '结构化表达',
          value_boundaries_json: '["不夸大","不侵权"]',
          risk_tolerance: 3,
          time_investment_hours: 8,
        }
      }
      throw new Error(`unexpected path: ${path}`)
    })
    vi.stubGlobal('$fetch', fetchMock)

    const client = createHttpApiClient('http://127.0.0.1:8000', () => 'user_1')
    const session = await client.createOnboardingSession({
      targetPersona: 'career_creator',
      goals: ['验证主线'],
    })
    expect(session.sessionId).toBe('session_1')

    const completed = await client.completeOnboarding({
      sessionId: session.sessionId,
      input: {
        skills: ['写作', '项目管理'],
        interests: ['职场策略', '案例复盘'],
        cognitiveStyle: '结构化表达',
        valueBoundaries: ['不夸大', '不侵权'],
        riskTolerance: 'medium',
        weeklyHours: 8,
        goals: ['验证主线'],
      },
    })

    expect(completed.profile.skillStack).toEqual(['写作', '项目管理'])
    expect(completed.profile.energyCurve).toEqual(['职场策略', '案例复盘'])
    expect(completed.profile.riskTolerance).toBe('medium')

    const [firstPath, firstOptions] = fetchMock.mock.calls[0] as [string, Record<string, unknown>]
    expect(firstPath).toBe('/v1/onboarding/sessions')
    expect(firstOptions.body).toEqual({ user_id: 'user_1' })
  })

  it('generates identity models via /v1 and parses json fields', async () => {
    const fetchMock = vi.fn(async (path: string) => {
      if (path === '/v1/identity-models/generate') {
        return [{ id: 'identity_1' }]
      }
      if (path === '/v1/identity-models/users/user_1') {
        return [
          {
            id: 'identity_1',
            title: '职场效率解剖师',
            target_audience_pain: '表达效率低',
            content_pillars_json: '["职业问题拆解","方法模板演示"]',
            tone_keywords_json: '["克制","结构化"]',
            tone_examples_json: '["示例1","示例2","示例3","示例4","示例5"]',
            long_term_views_json: '["观点1","观点2","观点3","观点4","观点5"]',
            differentiation: '真实周复盘',
            growth_path_0_3m: '先做内容结构',
            growth_path_3_12m: '形成产品化能力',
            monetization_validation_order_json: '["私域线索","咨询"]',
            risk_boundary_json: '["避免夸大收益"]',
          },
          {
            id: 'identity_2',
            title: '职场表达教练',
            target_audience_pain: '表达不成体系',
            content_pillars_json: '["结构思维","表达模板"]',
            tone_keywords_json: '["克制"]',
            tone_examples_json: '1. 开头先给结论\n2. 每段只说一件事\n3. 结尾给出下一步动作',
            long_term_views_json: '["观点1","观点2","观点3","观点4","观点5"]',
            differentiation: '从案例入手',
            growth_path_0_3m: '先打框架',
            growth_path_3_12m: '沉淀方法库',
            monetization_validation_order_json: '["咨询"]',
            risk_boundary_json: '["不承诺结果"]',
          },
          {
            id: 'identity_3',
            title: '职场复盘拆解师',
            target_audience_pain: '复盘无法沉淀',
            content_pillars_json: '["项目复盘","能力映射"]',
            tone_keywords_json: '["客观"]',
            tone_examples_json: '[invalid-json',
            long_term_views_json: '["观点1","观点2","观点3","观点4","观点5"]',
            differentiation: '实践导向',
            growth_path_0_3m: '先做周复盘',
            growth_path_3_12m: '形成课程',
            monetization_validation_order_json: '["私域线索"]',
            risk_boundary_json: '["不过度营销"]',
          },
        ]
      }
      throw new Error(`unexpected path: ${path}`)
    })
    vi.stubGlobal('$fetch', fetchMock)

    const client = createHttpApiClient('http://127.0.0.1:8000', () => 'user_1')
    const result = await client.generateIdentityModels({
      profile: {
        skillStack: ['写作'],
        energyCurve: ['方法拆解'],
        cognitiveStyle: '结构化',
        valueBoundaries: ['不夸大'],
        riskTolerance: 'medium',
        weeklyHours: 6,
        recommendedPlatforms: ['小红书'],
      },
    })

    expect(result.models[0].contentPillars).toEqual(['职业问题拆解', '方法模板演示'])
    expect(result.models[0].toneExamples.length).toBeGreaterThanOrEqual(5)
    expect(result.models[1].toneExamples).toEqual([
      '开头先给结论',
      '每段只说一件事',
      '结尾给出下一步动作',
    ])
    expect(result.models[2].toneExamples).toEqual([])
    expect(fetchMock.mock.calls.some(call => call[0] === '/v1/identity-models/generate')).toBe(true)
    expect(fetchMock.mock.calls.some(call => call[0] === '/v1/identity-models/users/user_1')).toBe(true)
  })

  it('maps persona/launch/consistency/event payloads', async () => {
    const fetchMock = vi.fn(async (path: string) => {
      if (path === '/v1/persona-constitutions/generate') {
        return { id: 'constitution_1' }
      }
      if (path === '/v1/persona-constitutions/constitution_1') {
        return {
          common_words_json: '["结论先行"]',
          forbidden_words_json: '["躺赚"]',
          sentence_preferences_json: '["每段给动作"]',
          moat_positions_json: '["不制造焦虑"]',
          narrative_mainline: '长期稳定输出',
          growth_arc_template: '阶段一：先打基础\n阶段二：再放大',
        }
      }
      if (path === '/v1/launch-kits/generate') {
        return { id: 'kit_1' }
      }
      if (path === '/v1/launch-kits/kit_1') {
        return {
          days: [
            {
              day_no: 1,
              theme: 'Day 1',
              draft_or_outline: '大纲',
              opening_text: '开头',
            },
          ],
          sustainable_columns_json: '["每周拆解"]',
          growth_experiment_suggestion_json:
            '[{"hypothesis":"A/B标题提升收藏","variables":["标题A","标题B"],"duration":"7天","success_metric":"收藏率+20%"}]',
        }
      }
      if (path === '/v1/consistency-checks') {
        return {
          deviation_items: '["偏离项1"]',
          deviation_reasons: ['原因1'],
          suggestions: '建议1',
          risk_warning: '触发风险边界',
        }
      }
      if (path === '/v1/events') {
        return { id: 'event_1' }
      }
      throw new Error(`unexpected path: ${path}`)
    })
    vi.stubGlobal('$fetch', fetchMock)

    const client = createHttpApiClient('http://127.0.0.1:8000', () => 'user_1')

    const constitution = await client.generatePersonaConstitution({
      identityModel: {
        id: 'identity_1',
        title: '标题',
        targetAudiencePain: '痛点',
        contentPillars: [],
        toneStyleKeywords: [],
        toneExamples: [],
        longTermViews: [],
        differentiation: '差异化',
        growthPath: { firstQuarter: '', yearOne: '' },
        monetizationValidationOrder: [],
        monetizationMap: '',
        riskBoundaries: [],
      },
    })
    expect(constitution.constitution.immutablePositions).toEqual(['不制造焦虑'])

    const launchKit = await client.generateLaunchKit({
      identityModel: {
        id: 'identity_1',
        title: '标题',
        targetAudiencePain: '痛点',
        contentPillars: [],
        toneStyleKeywords: [],
        toneExamples: [],
        longTermViews: [],
        differentiation: '差异化',
        growthPath: { firstQuarter: '', yearOne: '' },
        monetizationValidationOrder: [],
        monetizationMap: '',
        riskBoundaries: [],
      },
      constitution: constitution.constitution,
    })
    expect(launchKit.launchKit.days[0].day).toBe(1)
    expect(launchKit.launchKit.growthExperiment.variables).toEqual(['标题A', '标题B'])

    const check = await client.runConsistencyCheck({
      draft: '草稿内容',
      identityModel: {
        id: 'identity_1',
        title: '标题',
        targetAudiencePain: '痛点',
        contentPillars: [],
        toneStyleKeywords: [],
        toneExamples: [],
        longTermViews: [],
        differentiation: '差异化',
        growthPath: { firstQuarter: '', yearOne: '' },
        monetizationValidationOrder: [],
        monetizationMap: '',
        riskBoundaries: [],
      },
      constitution: constitution.constitution,
    })
    expect(check.result.deviations).toEqual(['偏离项1'])
    expect(check.result.reasons).toEqual(['原因1'])
    expect(check.result.suggestions).toEqual(['建议1'])
    expect(check.result.score).toBeGreaterThan(0)

    await client.trackEvent({
      eventName: 'identity_selected',
      userId: 'user_1',
      timestamp: '2026-02-23T00:00:00.000Z',
      identityId: 'identity_1',
      metadata: { from: 'test' },
    })

    const eventCall = fetchMock.mock.calls.find(call => call[0] === '/v1/events')
    expect(eventCall).toBeTruthy()
    expect((eventCall?.[1] as Record<string, unknown>).body).toMatchObject({
      user_id: 'user_1',
      event_name: 'identity_selected',
      stage: 'MVP',
      identity_model_id: 'identity_1',
    })
  })
})
