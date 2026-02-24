import type { IdentityModelCard, MvpFlowState } from '../types/flow'

const FLOW_STATE_VERSION = 1
const FLOW_STORAGE_KEY = 'bss-mvp-flow-state-v1'

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
  contentMatrixes: [],
  experiments: [],
  monetizationMaps: [],
  identityPortfolios: [],
  simulatorEvaluations: [],
  viewpointAssets: [],
  events: [],
})

const toPersistedState = (raw: unknown): MvpFlowState | null => {
  if (!raw || typeof raw !== 'object') {
    return null
  }
  const record = raw as { version?: unknown; state?: unknown }
  if (record.version !== FLOW_STATE_VERSION || !record.state || typeof record.state !== 'object') {
    return null
  }
  return {
    ...defaultState(),
    ...(record.state as Partial<MvpFlowState>),
    onboardingInput: {
      ...defaultInput(),
      ...((record.state as Partial<MvpFlowState>).onboardingInput || {}),
    },
    identityModels: Array.isArray((record.state as Partial<MvpFlowState>).identityModels)
      ? ((record.state as Partial<MvpFlowState>).identityModels as IdentityModelCard[])
      : [],
    events: Array.isArray((record.state as Partial<MvpFlowState>).events)
      ? (record.state as Partial<MvpFlowState>).events || []
      : [],
  }
}

export const useMvpFlow = () => {
  const state = useState<MvpFlowState>('mvp-flow-state', defaultState)
  const hydrated = useState<boolean>('mvp-flow-state-hydrated', () => false)

  if (import.meta.client && !hydrated.value) {
    const raw = localStorage.getItem(FLOW_STORAGE_KEY)
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as unknown
        const persistedState = toPersistedState(parsed)
        if (persistedState) {
          state.value = persistedState
        }
      } catch {
        localStorage.removeItem(FLOW_STORAGE_KEY)
      }
    }
    hydrated.value = true
  }

  if (import.meta.client) {
    watch(
      state,
      (value) => {
        localStorage.setItem(
          FLOW_STORAGE_KEY,
          JSON.stringify({
            version: FLOW_STATE_VERSION,
            state: value,
          })
        )
      },
      { deep: true }
    )
  }

  const reset = () => {
    state.value = defaultState()
    if (import.meta.client) {
      localStorage.removeItem(FLOW_STORAGE_KEY)
    }
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
