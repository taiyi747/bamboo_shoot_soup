import { describe, expect, it } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import ReviewPage from '../../app/pages/review.vue'

describe('review page', () => {
  it('renders event table without stage column', async () => {
    const wrapper = await mountSuspended(ReviewPage)
    expect(wrapper.text()).toContain('事件名')
    expect(wrapper.text()).toContain('时间')
    expect(wrapper.text()).toContain('身份 ID')
    expect(wrapper.text()).not.toContain('阶段')
  })
})
