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
          skill_stack_json: '["writing","pm"]',
          interest_energy_curve_json: '[{"interest":"strategy"},{"interest":"review"}]',
          cognitive_style: 'structured',
          value_boundaries_json: '["no hype","no infringement"]',
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
      goals: ['validate mainline'],
    })
    expect(session.sessionId).toBe('session_1')

    const completed = await client.completeOnboarding({
      sessionId: session.sessionId,
      input: {
        skills: ['writing', 'pm'],
        interests: ['strategy', 'review'],
        cognitiveStyle: 'structured',
        valueBoundaries: ['no hype', 'no infringement'],
        riskTolerance: 'medium',
        weeklyHours: 8,
        goals: ['validate mainline'],
      },
    })

    expect(completed.profile.skillStack).toEqual(['writing', 'pm'])
    expect(completed.profile.energyCurve).toEqual(['strategy', 'review'])
    expect(completed.profile.riskTolerance).toBe('medium')

    const [firstPath, firstOptions] = fetchMock.mock.calls[0] as [string, Record<string, unknown>]
    expect(firstPath).toBe('/v1/onboarding/sessions')
    expect(firstOptions.body).toEqual({ user_id: 'user_1' })
  })

  it('generates identity models via /v1 and parses tone examples', async () => {
    const fetchMock = vi.fn(async (path: string) => {
      if (path === '/v1/identity-models/generate') {
        return [{ id: 'identity_1' }]
      }
      if (path === '/v1/identity-models/users/user_1') {
        return [
          {
            id: 'identity_1',
            title: 'Model 1',
            target_audience_pain: 'pain',
            content_pillars_json: '["p1","p2"]',
            tone_keywords_json: '["calm","clear"]',
            tone_examples_json: '["e1","e2","e3","e4","e5"]',
            long_term_views_json: '["v1","v2","v3","v4","v5"]',
            differentiation: 'diff',
            growth_path_0_3m: 'q1',
            growth_path_3_12m: 'y1',
            monetization_validation_order_json: '["lead"]',
            risk_boundary_json: '["boundary"]',
          },
          {
            id: 'identity_2',
            title: 'Model 2',
            target_audience_pain: 'pain',
            content_pillars_json: '["p1","p2"]',
            tone_keywords_json: '["calm"]',
            tone_examples_json: '1. first\n2. second\n3. third',
            long_term_views_json: '["v1","v2","v3","v4","v5"]',
            differentiation: 'diff',
            growth_path_0_3m: 'q1',
            growth_path_3_12m: 'y1',
            monetization_validation_order_json: '["lead"]',
            risk_boundary_json: '["boundary"]',
          },
          {
            id: 'identity_3',
            title: 'Model 3',
            target_audience_pain: 'pain',
            content_pillars_json: '["p1","p2"]',
            tone_keywords_json: '["calm"]',
            tone_examples_json: '[invalid-json',
            long_term_views_json: '["v1","v2","v3","v4","v5"]',
            differentiation: 'diff',
            growth_path_0_3m: 'q1',
            growth_path_3_12m: 'y1',
            monetization_validation_order_json: '["lead"]',
            risk_boundary_json: '["boundary"]',
          },
        ]
      }
      throw new Error(`unexpected path: ${path}`)
    })
    vi.stubGlobal('$fetch', fetchMock)

    const client = createHttpApiClient('http://127.0.0.1:8000', () => 'user_1')
    const result = await client.generateIdentityModels({
      profile: {
        skillStack: ['writing'],
        energyCurve: ['strategy'],
        cognitiveStyle: 'structured',
        valueBoundaries: ['no hype'],
        riskTolerance: 'medium',
        weeklyHours: 6,
        recommendedPlatforms: ['xhs'],
      },
    })

    expect(result.models[0].toneExamples.length).toBeGreaterThanOrEqual(5)
    expect(result.models[1].toneExamples).toEqual(['first', 'second', 'third'])
    expect(result.models[2].toneExamples).toEqual([])
    expect(fetchMock.mock.calls.some(call => call[0] === '/v1/identity-models/generate')).toBe(true)
    expect(fetchMock.mock.calls.some(call => call[0] === '/v1/identity-models/users/user_1')).toBe(true)
  })

  it('maps persona/launch/day-article/consistency/event payloads', async () => {
    const fetchMock = vi.fn(async (path: string) => {
      if (path === '/v1/persona-constitutions/generate') {
        return { id: 'constitution_1' }
      }
      if (path === '/v1/persona-constitutions/constitution_1') {
        return {
          common_words_json: '["clear"]',
          forbidden_words_json: '["hype"]',
          sentence_preferences_json: '["one idea"]',
          moat_positions_json: '["truthful"]',
          narrative_mainline: 'mainline',
          growth_arc_template: 'stage1: start\\nstage2: scale',
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
              draft_or_outline: 'Outline',
              opening_text: 'Opening',
            },
          ],
          sustainable_columns_json: '["Weekly breakdown"]',
          growth_experiment_suggestion_json:
            '[{"hypothesis":"A/B title","variables":["A","B"],"duration":"7d","success_metric":"save +20%"}]',
        }
      }
      if (path === '/v1/launch-kits/day-articles/generate') {
        return {
          day_no: 1,
          title: 'Day 1 Article',
          markdown: '# Day 1',
        }
      }
      if (path === '/v1/consistency-checks') {
        return {
          deviation_items: '["item1"]',
          deviation_reasons: ['reason1'],
          suggestions: 'suggestion1',
          risk_warning: 'warning',
          score: 74,
        }
      }
      if (path === '/v1/events') {
        return { id: 'event_1' }
      }
      throw new Error(`unexpected path: ${path}`)
    })
    vi.stubGlobal('$fetch', fetchMock)

    const identityModel = {
      id: 'identity_1',
      title: 'title',
      targetAudiencePain: 'pain',
      contentPillars: [],
      toneStyleKeywords: [],
      toneExamples: [],
      longTermViews: [],
      differentiation: 'diff',
      growthPath: { firstQuarter: '', yearOne: '' },
      monetizationValidationOrder: [],
      monetizationMap: '',
      riskBoundaries: [],
    }

    const client = createHttpApiClient('http://127.0.0.1:8000', () => 'user_1')

    const constitution = await client.generatePersonaConstitution({ identityModel })
    expect(constitution.constitution.immutablePositions).toEqual(['truthful'])

    const launchKit = await client.generateLaunchKit({
      identityModel,
      constitution: constitution.constitution,
    })
    expect(launchKit.launchKit.days[0].day).toBe(1)
    expect(launchKit.launchKit.growthExperiment.variables).toEqual(['A', 'B'])

    const dayArticle = await client.generateLaunchKitDayArticle({
      identityModel,
      constitution: constitution.constitution,
      dayNo: 1,
      theme: 'Day 1',
      draftOutline: 'Outline',
      opening: 'Opening',
    })
    expect(dayArticle.dayNo).toBe(1)
    expect(dayArticle.title).toBe('Day 1 Article')
    expect(dayArticle.markdown).toBe('# Day 1')

    const dayArticleCall = fetchMock.mock.calls.find(call => call[0] === '/v1/launch-kits/day-articles/generate')
    expect(dayArticleCall).toBeTruthy()
    expect((dayArticleCall?.[1] as Record<string, unknown>).body).toMatchObject({
      user_id: 'user_1',
      identity_model_id: 'identity_1',
      constitution_id: null,
      day_no: 1,
      theme: 'Day 1',
      draft_or_outline: 'Outline',
      opening_text: 'Opening',
    })

    const check = await client.runConsistencyCheck({
      draft: 'draft content',
      identityModel,
      constitution: constitution.constitution,
    })
    expect(check.result.deviations).toEqual(['item1'])
    expect(check.result.reasons).toEqual(['reason1'])
    expect(check.result.suggestions).toEqual(['suggestion1'])
    expect(check.result.score).toBe(74)

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
