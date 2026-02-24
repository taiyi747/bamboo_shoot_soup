import { describe, expect, it } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import ReviewPage from '../../app/pages/review.vue'

describe('review page', () => {
  it('renders event table without stage column', async () => {
    const wrapper = await mountSuspended(ReviewPage)
    expect(wrapper.text()).toContain('Event Name')
    expect(wrapper.text()).toContain('Timestamp')
    expect(wrapper.text()).toContain('Identity ID')
    expect(wrapper.text()).not.toContain('Stage')
  })
})
