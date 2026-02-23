import { describe, expect, it } from 'vitest'
import { $fetch, setup } from '@nuxt/test-utils/e2e'

describe('route flow', async () => {
  await setup({
    browser: false,
  })

  it('redirects root route to onboarding flow', async () => {
    const html = await $fetch('/')
    expect(html).toContain('身份诊断')
    expect(html).not.toContain('M0')
    expect(html).not.toContain('Stage: MVP')
    expect(html).not.toContain('MVP 汇总')
    expect(html).not.toContain('stage:"MVP"')
  })

  it('blocks review route before prerequisites are met', async () => {
    const html = await $fetch('/review')
    expect(html).toContain('身份诊断')
  })
})
