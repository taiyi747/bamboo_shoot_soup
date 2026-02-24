import { beforeEach, describe, expect, it } from 'vitest'
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { reactive, ref } from 'vue'
import type { MvpFlowState } from '../../app/types/flow'

const routeState = reactive({ path: '/onboarding' })
const colorModeState = reactive<{ value: 'light' | 'dark'; preference: 'light' | 'dark' }>({
  value: 'light',
  preference: 'light',
})

const createFlowState = (): MvpFlowState => ({
  onboardingInput: {
    skills: [],
    interests: [],
    cognitiveStyle: '',
    valueBoundaries: [],
    riskTolerance: 'medium',
    weeklyHours: 6,
    goals: [],
  },
  identityModels: [],
  draftToCheck: '',
  events: [],
})

const state = ref<MvpFlowState>(createFlowState())

mockNuxtImport('useRoute', () => () => routeState)
mockNuxtImport('useColorMode', () => () => colorModeState)
mockNuxtImport('useMvpFlow', () => () => ({
  state,
}))

describe('default layout', () => {
  beforeEach(() => {
    routeState.path = '/onboarding'
    state.value = createFlowState()
    colorModeState.value = 'light'
    colorModeState.preference = 'light'
  })

  it('renders all six mvp step entries with compact nav classes', async () => {
    const DefaultLayout = (await import('../../app/layouts/default.vue')).default
    const wrapper = await mountSuspended(DefaultLayout, {
      slots: {
        default: '<div data-testid="layout-slot-content">slot content</div>',
      },
    })

    const labels = ['身份诊断', '身份模型', '人格宪法', '启动包', '一致性检查', '交付汇总']
    for (const label of labels) {
      expect(wrapper.text()).toContain(label)
    }

    const nav = wrapper.find('[data-testid="mvp-step-nav"]')
    expect(nav.exists()).toBe(true)

    const navLinks = wrapper.findAll('.step-nav-link')
    expect(navLinks).toHaveLength(6)

    const stepButtons = wrapper.findAll('.step-nav-button')
    expect(stepButtons).toHaveLength(6)
    for (const button of stepButtons) {
      expect(button.classes()).toContain('touch-target')
    }

    const colorModeToggle = wrapper.find('[aria-label="Toggle color mode"]')
    expect(colorModeToggle.exists()).toBe(true)
    expect(colorModeToggle.classes()).toContain('hidden')
    expect(colorModeToggle.classes()).toContain('sm:inline-flex')
  })
})
