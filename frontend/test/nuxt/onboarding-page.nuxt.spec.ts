import { describe, expect, it } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import OnboardingPage from '../../app/pages/onboarding.vue'

describe('onboarding page', () => {
  it('renders onboarding content', async () => {
    const wrapper = await mountSuspended(OnboardingPage)
    expect(wrapper.text()).toContain('身份诊断')
    expect(wrapper.text()).not.toContain('M0')
    expect(wrapper.text()).toContain('技能栈')
  })
})
