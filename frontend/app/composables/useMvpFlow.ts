import type { IdentityModelCard, MvpFlowState } from '../types/flow'

const defaultInput = () => ({
  skills: [] as string[],
  interests: [] as string[],
  cognitiveStyle: '',
  valueBoundaries: [] as string[],
  riskTolerance: 'medium' as const,
  weeklyHours: 6,
  goals: [] as string[],
})

const defaultState = (): MvpFlowState => ({
  onboardingInput: defaultInput(),
  identityModels: [],
  draftToCheck: '',
  events: [],
})

export const useMvpFlow = () => {
  const state = useState<MvpFlowState>('mvp-flow-state', defaultState)

  const reset = () => {
    state.value = defaultState()
  }

  const selectedPrimaryModel = computed<IdentityModelCard | undefined>(() =>
    state.value.identityModels.find(model => model.id === state.value.selectedPrimaryId)
  )

  const selectedBackupModel = computed<IdentityModelCard | undefined>(() =>
    state.value.identityModels.find(model => model.id === state.value.selectedBackupId)
  )

  return {
    state,
    reset,
    selectedPrimaryModel,
    selectedBackupModel,
  }
}
