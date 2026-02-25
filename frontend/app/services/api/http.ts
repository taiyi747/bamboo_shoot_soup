import type {
  ContentMatrix,
  ExperimentRecord,
  IdentityModelCard,
  LaunchKit,
  MonetizationMap,
  OnboardingProfile,
  PersonaConstitution,
  RiskTolerance,
} from '../../types/flow'
import type { ApiClient } from './types'

type Dict = Record<string, unknown>

interface OnboardingProfileDto {
  skill_stack_json: unknown
  interest_energy_curve_json: unknown
  cognitive_style: string
  value_boundaries_json: unknown
  risk_tolerance: number
  time_investment_hours: number
}

interface IdentityModelDto {
  id: string
  title: string
  target_audience_pain: string
  content_pillars_json: unknown
  tone_keywords_json: unknown
  tone_examples_json: unknown
  long_term_views_json: unknown
  differentiation: string
  growth_path_0_3m: string
  growth_path_3_12m: string
  monetization_validation_order_json: unknown
  risk_boundary_json: unknown
}

interface PersonaConstitutionDto {
  common_words_json: unknown
  forbidden_words_json: unknown
  sentence_preferences_json: unknown
  moat_positions_json: unknown
  narrative_mainline: string
  growth_arc_template: string
}

interface LaunchKitDayDto {
  day_no: number
  theme: string
  draft_or_outline: string
  opening_text: string
}

interface LaunchKitDto {
  days: LaunchKitDayDto[]
  sustainable_columns_json: unknown
  growth_experiment_suggestion_json: unknown
}

interface ContentMatrixDto {
  matrix_json: unknown
}

interface ExperimentDto {
  id: string
  hypothesis: string
  variables_json: unknown
  execution_cycle: string
  result: string
  conclusion: string
  status: string
}

interface MonetizationMapDto {
  primary_path: string
  backup_path: string
  weeks_json: unknown
}

const toErrorMessage = (data: unknown): string => {
  if (!data) {
    return ''
  }

  if (typeof data === 'string') {
    return data
  }

  if (typeof data === 'object') {
    const detail = (data as Dict).detail
    if (typeof detail === 'string') {
      return detail
    }

    if (Array.isArray(detail)) {
      return detail
        .map(item => {
          if (typeof item === 'string') {
            return item
          }
          if (item && typeof item === 'object' && typeof (item as Dict).msg === 'string') {
            return String((item as Dict).msg)
          }
          return ''
        })
        .filter(Boolean)
        .join('；')
    }
  }

  return ''
}

const normalizeApiError = (error: unknown): Error => {
  const apiError = error as {
    statusCode?: number
    status?: number
    data?: unknown
    response?: { status?: number; _data?: unknown }
    message?: string
  }

  const status = apiError.statusCode ?? apiError.status ?? apiError.response?.status
  const detail = toErrorMessage(apiError.data ?? apiError.response?._data)

  if (!status) {
    return new Error('后端连接失败，请确认服务已启动。')
  }
  if (status === 400) {
    return new Error(detail || '请求参数错误。')
  }
  if (status === 404) {
    return new Error(detail || '请求资源不存在。')
  }
  if (status === 422) {
    return new Error(detail || '请求参数校验失败。')
  }
  if (status >= 500) {
    return new Error(detail || '后端服务异常，请稍后重试。')
  }

  return new Error(detail || apiError.message || '请求失败，请稍后重试。')
}

const parseJsonArray = (value: unknown): unknown[] => {
  if (Array.isArray(value)) {
    return value
  }
  if (typeof value !== 'string') {
    return []
  }

  try {
    const parsed = JSON.parse(value)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const toStringArray = (value: unknown): string[] => {
  const items = (() => {
    if (Array.isArray(value)) {
      return value
    }
    if (typeof value === 'string') {
      const parsed = parseJsonArray(value)
      return parsed.length > 0 ? parsed : [value]
    }
    return parseJsonArray(value)
  })()

  return items
    .map(item => {
      if (typeof item === 'string') {
        return item.trim()
      }
      if (typeof item === 'number' || typeof item === 'boolean') {
        return String(item)
      }
      if (item && typeof item === 'object') {
        return JSON.stringify(item)
      }
      return ''
    })
    .filter(Boolean)
}

const parseToneExamples = (value: unknown): string[] => {
  if (Array.isArray(value)) {
    return toStringArray(value)
  }

  if (typeof value !== 'string') {
    return []
  }

  const raw = value.trim()
  if (!raw) {
    return []
  }

  try {
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) {
      return toStringArray(parsed)
    }
    return []
  } catch {
    if (raw.startsWith('[') || raw.startsWith('{')) {
      return []
    }
  }

  return raw
    .split(/\r?\n+/)
    .map(line => line.replace(/^\s*(?:[-*]|[（(]\d+[）)]|\d+[.)、])\s*/u, '').trim())
    .filter(Boolean)
}

const riskToleranceToNumber = (value: RiskTolerance): number => {
  if (value === 'low') {
    return 1
  }
  if (value === 'high') {
    return 5
  }
  return 3
}

const numberToRiskTolerance = (value: number): RiskTolerance => {
  if (value <= 2) {
    return 'low'
  }
  if (value >= 5) {
    return 'high'
  }
  return 'medium'
}

const parseEnergyCurve = (value: unknown): string[] =>
  parseJsonArray(value)
    .map(item => {
      if (typeof item === 'string') {
        return item
      }
      if (item && typeof item === 'object') {
        const dict = item as Dict
        const firstString = ['interest', 'name', 'label', 'value']
          .map(key => dict[key])
          .find(entry => typeof entry === 'string')
        if (typeof firstString === 'string') {
          return firstString
        }
        return JSON.stringify(item)
      }
      return ''
    })
    .filter(Boolean)

const parseGrowthArc = (raw: string): PersonaConstitution['growthArc'] => {
  const lines = raw
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)
  if (lines.length === 0) {
    return []
  }

  return lines.map(line => {
    const [stage, ...rest] = line.split('：')
    if (rest.length === 0) {
      return { stage: '阶段', storyTemplate: line }
    }
    return {
      stage: stage?.trim() || '阶段',
      storyTemplate: rest.join('：').trim() || line,
    }
  })
}

const buildConsistencyScore = (deviations: string[], reasons: string[], riskWarning?: string): number => {
  const riskPenalty = riskWarning ? 22 : 0
  return Math.max(25, Math.min(100, 92 - deviations.length * 18 - reasons.length * 4 - riskPenalty))
}

const requestJson = async <T>(
  baseURL: string,
  path: string,
  options?: { method?: 'GET' | 'POST' | 'PATCH'; body?: unknown }
): Promise<T> => {
  try {
    return await $fetch<T>(path, {
      baseURL,
      method: options?.method,
      body: options?.body as any,
    })
  } catch (error) {
    throw normalizeApiError(error)
  }
}

const mapProfile = (dto: OnboardingProfileDto): OnboardingProfile => ({
  skillStack: toStringArray(dto.skill_stack_json),
  energyCurve: parseEnergyCurve(dto.interest_energy_curve_json),
  cognitiveStyle: dto.cognitive_style || '',
  valueBoundaries: toStringArray(dto.value_boundaries_json),
  riskTolerance: numberToRiskTolerance(dto.risk_tolerance ?? 3),
  weeklyHours: Number(dto.time_investment_hours || 0),
  recommendedPlatforms: ['小红书', '公众号', '视频号'],
})

const mapIdentityModel = (dto: IdentityModelDto): IdentityModelCard => {
  const monetizationValidationOrder = toStringArray(dto.monetization_validation_order_json)
  return {
    id: dto.id,
    title: dto.title || '未命名身份',
    targetAudiencePain: dto.target_audience_pain || '',
    contentPillars: toStringArray(dto.content_pillars_json),
    toneStyleKeywords: toStringArray(dto.tone_keywords_json),
    toneExamples: parseToneExamples(dto.tone_examples_json),
    longTermViews: toStringArray(dto.long_term_views_json),
    differentiation: dto.differentiation || '',
    growthPath: {
      firstQuarter: dto.growth_path_0_3m || '',
      yearOne: dto.growth_path_3_12m || '',
    },
    monetizationValidationOrder,
    monetizationMap: monetizationValidationOrder.join(' -> '),
    riskBoundaries: toStringArray(dto.risk_boundary_json),
  }
}

const mapPersona = (dto: PersonaConstitutionDto): PersonaConstitution => ({
  commonWords: toStringArray(dto.common_words_json),
  forbiddenWords: toStringArray(dto.forbidden_words_json),
  sentencePreferences: toStringArray(dto.sentence_preferences_json),
  immutablePositions: toStringArray(dto.moat_positions_json),
  narrativeMainline: dto.narrative_mainline || '',
  growthArc: parseGrowthArc(dto.growth_arc_template || ''),
})

const mapLaunchKit = (dto: LaunchKitDto): LaunchKit => {
  const growthExperiments = parseJsonArray(dto.growth_experiment_suggestion_json)
  const growthExperiment = growthExperiments[0] && typeof growthExperiments[0] === 'object' ? (growthExperiments[0] as Dict) : {}
  const variables = Array.isArray(growthExperiment.variables)
    ? growthExperiment.variables.filter(item => typeof item === 'string').map(item => String(item))
    : []

  return {
    days: (dto.days || []).map(day => ({
      day: day.day_no,
      theme: day.theme || '',
      draftOutline: day.draft_or_outline || '',
      opening: day.opening_text || '',
    })),
    sustainableColumns: toStringArray(dto.sustainable_columns_json),
    growthExperiment: {
      hypothesis: String(growthExperiment.hypothesis || ''),
      variables,
      executionCycle: String(growthExperiment.duration || growthExperiment.execution_cycle || ''),
      successMetric: String(growthExperiment.success_metric || growthExperiment.successMetric || ''),
    },
  }
}

const mapContentMatrix = (dto: ContentMatrixDto): ContentMatrix => {
  const pillars = parseJsonArray(dto.matrix_json)
    .map(item => {
      if (!item || typeof item !== 'object') {
        return null
      }
      const dict = item as Dict
      const platformRewrites: Record<string, string[]> = {}
      const rewritesRaw = dict.platform_rewrites
      if (rewritesRaw && typeof rewritesRaw === 'object' && !Array.isArray(rewritesRaw)) {
        for (const [platform, values] of Object.entries(rewritesRaw as Dict)) {
          platformRewrites[platform] = toStringArray(values)
        }
      }

      return {
        pillar: String(dict.pillar || ''),
        topics: toStringArray(dict.topics),
        platformRewrites,
      }
    })
    .filter((item): item is ContentMatrix['pillars'][number] => Boolean(item?.pillar))

  return { pillars }
}

const mapExperiment = (dto: ExperimentDto): ExperimentRecord => ({
  id: dto.id,
  hypothesis: dto.hypothesis || '',
  variables: toStringArray(dto.variables_json),
  executionCycle: dto.execution_cycle || '',
  result: dto.result || '',
  conclusion: dto.conclusion || '',
  status: dto.status === 'completed' ? 'completed' : 'planned',
})

const mapMonetizationMap = (dto: MonetizationMapDto): MonetizationMap => {
  const weeks = parseJsonArray(dto.weeks_json)
    .map(item => {
      if (!item || typeof item !== 'object') {
        return null
      }
      const dict = item as Dict
      return {
        weekNo: Number(dict.week_no || 0),
        goal: String(dict.goal || ''),
        task: String(dict.task || ''),
        deliverable: String(dict.deliverable || ''),
        validationMetric: String(dict.validation_metric || ''),
      }
    })
    .filter((item): item is MonetizationMap['weeks'][number] => Boolean(item && item.weekNo > 0))

  return {
    primaryPath: dto.primary_path || '',
    backupPath: dto.backup_path || '',
    weeks,
  }
}

export const createHttpApiClient = (baseURL: string, getUserId: () => string): ApiClient => ({
  async createOnboardingSession() {
    const userId = getUserId()
    const response = await requestJson<{ id: string }>(baseURL, '/v1/onboarding/sessions', {
      method: 'POST',
      body: { user_id: userId },
    })
    return { sessionId: String(response.id) }
  },

  async completeOnboarding(input) {
    const userId = getUserId()
    await requestJson(baseURL, `/v1/onboarding/sessions/${input.sessionId}/complete`, {
      method: 'POST',
      body: {
        session_id: input.sessionId,
        questionnaire_responses: {
          goals: input.input.goals,
          source: 'frontend_mvp',
        },
        skill_stack: input.input.skills,
        interest_energy_curve: input.input.interests.map(interest => ({ interest })),
        cognitive_style: input.input.cognitiveStyle,
        value_boundaries: input.input.valueBoundaries,
        risk_tolerance: riskToleranceToNumber(input.input.riskTolerance),
        time_investment_hours: input.input.weeklyHours,
      },
    })

    const profile = await requestJson<OnboardingProfileDto>(
      baseURL,
      `/v1/onboarding/sessions/${input.sessionId}/profile`,
      { method: 'GET' }
    )

    return { profile: mapProfile(profile) }
  },

  async generateIdentityModels(input) {
    const userId = getUserId()
    await requestJson(baseURL, '/v1/identity-models/generate', {
      method: 'POST',
      body: {
        user_id: userId,
        capability_profile: {
          skill_stack: input.profile.skillStack,
          interest_energy_curve: input.profile.energyCurve.map(item => ({ interest: item })),
          cognitive_style: input.profile.cognitiveStyle,
          value_boundaries: input.profile.valueBoundaries,
          risk_tolerance: riskToleranceToNumber(input.profile.riskTolerance),
          time_investment_hours: input.profile.weeklyHours,
        },
        count: 3,
      },
    })

    const models = await requestJson<IdentityModelDto[]>(baseURL, `/v1/identity-models/users/${userId}`, {
      method: 'GET',
    })

    return { models: models.map(mapIdentityModel) }
  },

  async selectIdentity(input) {
    await requestJson(baseURL, '/v1/identity-selections', {
      method: 'POST',
      body: {
        user_id: getUserId(),
        primary_identity_id: input.primaryId,
        backup_identity_id: input.backupId,
      },
    })

    return { selected: true }
  },

  async generatePersonaConstitution(input) {
    const userId = getUserId()
    const created = await requestJson<{ id?: string }>(baseURL, '/v1/persona-constitutions/generate', {
      method: 'POST',
      body: {
        user_id: userId,
        identity_model_id: input.identityModel.id,
      },
    })

    const constitution = created.id
      ? await requestJson<PersonaConstitutionDto>(baseURL, `/v1/persona-constitutions/${created.id}`, { method: 'GET' })
      : await requestJson<PersonaConstitutionDto>(
          baseURL,
          `/v1/persona-constitutions/users/${userId}/latest`,
          { method: 'GET' }
        )

    return { constitution: mapPersona(constitution) }
  },

  async generateLaunchKit(input) {
    const created = await requestJson<{ id: string }>(baseURL, '/v1/launch-kits/generate', {
      method: 'POST',
      body: {
        user_id: getUserId(),
        identity_model_id: input.identityModel.id,
      },
    })

    const launchKit = await requestJson<LaunchKitDto>(baseURL, `/v1/launch-kits/${created.id}`, {
      method: 'GET',
    })

    return { launchKit: mapLaunchKit(launchKit) }
  },

  async generateContentMatrix(input) {
    const created = await requestJson<{ id: string }>(baseURL, '/v1/content-matrices/generate', {
      method: 'POST',
      body: {
        user_id: getUserId(),
        identity_model_id: input.identityModel.id,
      },
    })

    const matrix = await requestJson<ContentMatrixDto>(baseURL, `/v1/content-matrices/${created.id}`, {
      method: 'GET',
    })

    return { contentMatrix: mapContentMatrix(matrix) }
  },

  async getContentMatrices() {
    const matrices = await requestJson<ContentMatrixDto[]>(
      baseURL,
      `/v1/content-matrices/users/${getUserId()}`,
      { method: 'GET' }
    )
    return { matrices: matrices.map(mapContentMatrix) }
  },

  async createExperiment(input) {
    const created = await requestJson<{ id: string }>(baseURL, '/v1/experiments', {
      method: 'POST',
      body: {
        user_id: getUserId(),
        identity_model_id: input.identityModel.id,
        hypothesis: input.hypothesis,
        variables: input.variables,
        execution_cycle: input.executionCycle,
      },
    })
    return { experimentId: created.id }
  },

  async updateExperimentResult(input) {
    await requestJson(baseURL, `/v1/experiments/${input.experimentId}/result`, {
      method: 'PATCH',
      body: {
        result: input.result,
        conclusion: input.conclusion,
      },
    })
    return { updated: true as const }
  },

  async getExperiments() {
    const experiments = await requestJson<ExperimentDto[]>(baseURL, `/v1/experiments/users/${getUserId()}`, {
      method: 'GET',
    })
    return { experiments: experiments.map(mapExperiment) }
  },

  async generateMonetizationMap(input) {
    const created = await requestJson<{ id: string }>(baseURL, '/v1/monetization-maps/generate', {
      method: 'POST',
      body: {
        user_id: getUserId(),
        identity_model_id: input.identityModel.id,
      },
    })

    const map = await requestJson<MonetizationMapDto>(baseURL, `/v1/monetization-maps/${created.id}`, {
      method: 'GET',
    })

    return { monetizationMap: mapMonetizationMap(map) }
  },

  async getMonetizationMaps() {
    const maps = await requestJson<MonetizationMapDto[]>(
      baseURL,
      `/v1/monetization-maps/users/${getUserId()}`,
      { method: 'GET' }
    )
    return { maps: maps.map(mapMonetizationMap) }
  },

  async runConsistencyCheck(input) {
    const response = await requestJson<{
      deviation_items: unknown
      deviation_reasons: unknown
      suggestions: unknown
      risk_warning?: string
    }>(baseURL, '/v1/consistency-checks', {
      method: 'POST',
      body: {
        user_id: getUserId(),
        identity_model_id: input.identityModel.id,
        draft_text: input.draft,
      },
    })

    const deviations = toStringArray(response.deviation_items)
    const reasons = toStringArray(response.deviation_reasons)
    const suggestions = toStringArray(response.suggestions)
    const riskWarning = response.risk_warning?.trim() ? response.risk_warning : undefined

    return {
      result: {
        deviations,
        reasons,
        suggestions,
        riskWarning,
        score: buildConsistencyScore(deviations, reasons, riskWarning),
      },
    }
  },

  async trackEvent(input) {
    await requestJson(baseURL, '/v1/events', {
      method: 'POST',
      body: {
        user_id: input.userId,
        event_name: input.eventName,
        stage: 'MVP',
        identity_model_id: input.identityId,
        payload: {
          timestamp: input.timestamp,
          ...(input.metadata || {}),
        },
      },
    })

    return { accepted: true }
  },
})
