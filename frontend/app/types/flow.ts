export type Stage = 'CURRENT' | 'MVP' | 'V1' | 'V2'
export type RiskTolerance = 'low' | 'medium' | 'high'

export interface OnboardingInput {
  skills: string[]
  interests: string[]
  cognitiveStyle: string
  valueBoundaries: string[]
  riskTolerance: RiskTolerance
  weeklyHours: number
  goals: string[]
}

export interface OnboardingProfile {
  skillStack: string[]
  energyCurve: string[]
  cognitiveStyle: string
  valueBoundaries: string[]
  riskTolerance: RiskTolerance
  weeklyHours: number
  recommendedPlatforms: string[]
}

export interface IdentityGrowthPath {
  firstQuarter: string
  yearOne: string
}

export interface IdentityModelCard {
  id: string
  title: string
  targetAudiencePain: string
  contentPillars: string[]
  toneStyleKeywords: string[]
  toneExamples: string[]
  longTermViews: string[]
  differentiation: string
  growthPath: IdentityGrowthPath
  monetizationValidationOrder: string[]
  monetizationMap: string
  riskBoundaries: string[]
}

export interface GrowthArcItem {
  stage: string
  storyTemplate: string
}

export interface PersonaConstitution {
  commonWords: string[]
  forbiddenWords: string[]
  sentencePreferences: string[]
  immutablePositions: string[]
  narrativeMainline: string
  growthArc: GrowthArcItem[]
}

export interface LaunchKitDay {
  day: number
  theme: string
  draftOutline: string
  opening: string
}

export interface GrowthExperiment {
  hypothesis: string
  variables: string[]
  executionCycle: string
  successMetric: string
}

export interface LaunchKit {
  days: LaunchKitDay[]
  sustainableColumns: string[]
  growthExperiment: GrowthExperiment
}

export interface ConsistencyCheckResult {
  deviations: string[]
  reasons: string[]
  suggestions: string[]
  riskWarning?: string
  score: number
}

export type AnalyticsEventName =
  | 'onboarding_started'
  | 'onboarding_completed'
  | 'identity_models_generated'
  | 'identity_selected'
  | 'launch_kit_generated'
  | 'consistency_check_triggered'
  | 'content_published'
  | 'experiment_created'
  | 'monetization_plan_started'
  | 'first_revenue_or_lead_confirmed'

export interface AnalyticsEventPayload {
  eventName: AnalyticsEventName
  userId: string
  timestamp: string
  stage: Stage
  identityId?: string
  metadata?: Record<string, unknown>
}

export interface MvpFlowState {
  sessionId?: string
  onboardingInput: OnboardingInput
  profile?: OnboardingProfile
  identityModels: IdentityModelCard[]
  selectedPrimaryId?: string
  selectedBackupId?: string
  persona?: PersonaConstitution
  launchKit?: LaunchKit
  draftToCheck: string
  consistencyCheck?: ConsistencyCheckResult
  events: AnalyticsEventPayload[]
}
