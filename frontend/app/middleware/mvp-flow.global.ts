type GuardFn = () => boolean

const guards: Record<string, GuardFn> = {
  '/identity-models': () => Boolean(useMvpFlow().state.value.profile),
  '/persona-constitution': () => Boolean(useMvpFlow().state.value.selectedPrimaryId),
  '/launch-kit': () => Boolean(useMvpFlow().state.value.persona),
  '/consistency-check': () => Boolean(useMvpFlow().state.value.launchKit),
  '/review': () => Boolean(useMvpFlow().state.value.consistencyCheck),
}

const fallbackRoute: Record<string, string> = {
  '/identity-models': '/onboarding',
  '/persona-constitution': '/identity-models',
  '/launch-kit': '/persona-constitution',
  '/consistency-check': '/launch-kit',
  '/review': '/consistency-check',
}

export default defineNuxtRouteMiddleware((to) => {
  const guard = guards[to.path]
  if (!guard) {
    return
  }

  if (!guard()) {
    return navigateTo(fallbackRoute[to.path] || '/onboarding')
  }
})
