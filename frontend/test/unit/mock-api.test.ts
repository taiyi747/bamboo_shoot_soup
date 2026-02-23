import { describe, expect, it } from 'vitest'
import { mockApiClient } from '../../app/services/api/mock'

describe('mockApiClient', () => {
  it('generates 3-5 identity models with required fields', async () => {
    const { models } = await mockApiClient.generateIdentityModels({
      profile: {
        skillStack: ['内容策划', '项目管理'],
        energyCurve: ['方法拆解', '案例复盘'],
        cognitiveStyle: '结构化表达',
        valueBoundaries: ['不制造焦虑'],
        riskTolerance: 'medium',
        weeklyHours: 8,
        recommendedPlatforms: ['小红书'],
      },
    })

    expect(models.length).toBeGreaterThanOrEqual(3)
    expect(models.length).toBeLessThanOrEqual(5)

    for (const model of models) {
      expect(model.differentiation.trim().length).toBeGreaterThan(0)
      expect(model.toneExamples.length).toBeGreaterThanOrEqual(5)
    }
  })

  it('returns explicit risk warning for risky drafts', async () => {
    const identityModel = (
      await mockApiClient.generateIdentityModels({
        profile: {
          skillStack: ['写作'],
          energyCurve: ['职场分析'],
          cognitiveStyle: '拆解型',
          valueBoundaries: ['不虚假陈述'],
          riskTolerance: 'low',
          weeklyHours: 6,
          recommendedPlatforms: ['公众号'],
        },
      })
    ).models[0]

    const constitution = (
      await mockApiClient.generatePersonaConstitution({
        identityModel,
      })
    ).constitution

    const result = await mockApiClient.runConsistencyCheck({
      draft: '这是一条保证收益的内幕消息，闭眼冲。',
      identityModel,
      constitution,
    })

    expect(result.result.riskWarning).toBeTruthy()
    expect(result.result.suggestions.length).toBeGreaterThan(0)
  })
})
