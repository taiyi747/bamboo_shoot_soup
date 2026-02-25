import type {
  AnalyticsEventPayload,
  ContentMatrix,
  ExperimentRecord,
  ConsistencyCheckResult,
  IdentityModelCard,
  LaunchKit,
  MonetizationMap,
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

export interface GenerateContentMatrixRequest {
  identityModel: IdentityModelCard
  constitution: PersonaConstitution
}

export interface GenerateContentMatrixResponse {
  contentMatrix: ContentMatrix
}

export interface GetContentMatricesResponse {
  matrices: ContentMatrix[]
}

export interface CreateExperimentRequest {
  identityModel: IdentityModelCard
  hypothesis: string
  variables: string[]
  executionCycle: string
}

export interface CreateExperimentResponse {
  experimentId: string
}

export interface UpdateExperimentResultRequest {
  experimentId: string
  result: string
  conclusion: string
}

export interface UpdateExperimentResultResponse {
  updated: true
}

export interface GetExperimentsResponse {
  experiments: ExperimentRecord[]
}

export interface GenerateMonetizationMapRequest {
  identityModel: IdentityModelCard
  constitution: PersonaConstitution
}

export interface GenerateMonetizationMapResponse {
  monetizationMap: MonetizationMap
}

export interface GetMonetizationMapsResponse {
  maps: MonetizationMap[]
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
  generateContentMatrix: (input: GenerateContentMatrixRequest) => Promise<GenerateContentMatrixResponse>
  getContentMatrices: () => Promise<GetContentMatricesResponse>
  createExperiment: (input: CreateExperimentRequest) => Promise<CreateExperimentResponse>
  updateExperimentResult: (
    input: UpdateExperimentResultRequest
  ) => Promise<UpdateExperimentResultResponse>
  getExperiments: () => Promise<GetExperimentsResponse>
  generateMonetizationMap: (
    input: GenerateMonetizationMapRequest
  ) => Promise<GenerateMonetizationMapResponse>
  getMonetizationMaps: () => Promise<GetMonetizationMapsResponse>
  runConsistencyCheck: (input: RunConsistencyCheckRequest) => Promise<RunConsistencyCheckResponse>
  trackEvent: (input: AnalyticsEventPayload) => Promise<TrackEventResponse>
}
