import type {
  AnalyticsEventPayload,
  ConsistencyCheckResult,
  IdentityModelCard,
  LaunchKit,
  OnboardingInput,
  OnboardingProfile,
  PersonaConstitution,
} from '../../types/flow'

export interface CreateOnboardingSessionRequest {
  targetPersona: 'career_creator'
  goals: string[]
}

export interface CreateOnboardingSessionResponse {
  sessionId: string
}

export interface CompleteOnboardingRequest {
  sessionId: string
  input: OnboardingInput
}

export interface CompleteOnboardingResponse {
  profile: OnboardingProfile
}

export interface GenerateIdentityModelsRequest {
  profile: OnboardingProfile
}

export interface GenerateIdentityModelsResponse {
  models: IdentityModelCard[]
}

export interface SelectIdentityRequest {
  primaryId: string
  backupId: string
}

export interface SelectIdentityResponse {
  selected: true
}

export interface GeneratePersonaConstitutionRequest {
  identityModel: IdentityModelCard
}

export interface GeneratePersonaConstitutionResponse {
  constitution: PersonaConstitution
}

export interface GenerateLaunchKitRequest {
  identityModel: IdentityModelCard
  constitution: PersonaConstitution
}

export interface GenerateLaunchKitResponse {
  launchKit: LaunchKit
}

export interface GenerateLaunchKitDayArticleRequest {
  identityModel: IdentityModelCard
  constitution: PersonaConstitution
  dayNo: number
  theme: string
  draftOutline: string
  opening: string
}

export interface GenerateLaunchKitDayArticleResponse {
  dayNo: number
  title: string
  markdown: string
}

export interface RunConsistencyCheckRequest {
  draft: string
  identityModel: IdentityModelCard
  constitution: PersonaConstitution
}

export interface RunConsistencyCheckResponse {
  result: ConsistencyCheckResult
}

export interface TrackEventResponse {
  accepted: true
}

export interface ApiClient {
  createOnboardingSession: (input: CreateOnboardingSessionRequest) => Promise<CreateOnboardingSessionResponse>
  completeOnboarding: (input: CompleteOnboardingRequest) => Promise<CompleteOnboardingResponse>
  generateIdentityModels: (input: GenerateIdentityModelsRequest) => Promise<GenerateIdentityModelsResponse>
  selectIdentity: (input: SelectIdentityRequest) => Promise<SelectIdentityResponse>
  generatePersonaConstitution: (
    input: GeneratePersonaConstitutionRequest
  ) => Promise<GeneratePersonaConstitutionResponse>
  generateLaunchKit: (input: GenerateLaunchKitRequest) => Promise<GenerateLaunchKitResponse>
  generateLaunchKitDayArticle: (
    input: GenerateLaunchKitDayArticleRequest
  ) => Promise<GenerateLaunchKitDayArticleResponse>
  runConsistencyCheck: (input: RunConsistencyCheckRequest) => Promise<RunConsistencyCheckResponse>
  trackEvent: (input: AnalyticsEventPayload) => Promise<TrackEventResponse>
}
