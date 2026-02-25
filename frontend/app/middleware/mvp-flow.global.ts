type GuardFn = () => boolean

const guards: Record<string, GuardFn> = {
  '/identity-models': () => Boolean(useMvpFlow().state.value.profile),
  '/persona-constitution': () => Boolean(useMvpFlow().state.value.selectedPrimaryId),
  '/launch-kit': () => Boolean(useMvpFlow().state.value.persona),
  '/consistency-check': () => Boolean(useMvpFlow().state.value.launchKit),
  '/content-matrix': () => Boolean(useMvpFlow().state.value.consistencyCheck),
  '/experiments': () => Boolean(useMvpFlow().state.value.contentMatrix),
  '/monetization-map': () => useMvpFlow().state.value.experiments.length > 0,
  '/review': () => Boolean(useMvpFlow().state.value.monetizationMap),
}

const fallbackRoute: Record<string, string> = {
  '/identity-models': '/onboarding',
  '/persona-constitution': '/identity-models',
  '/launch-kit': '/persona-constitution',
  '/consistency-check': '/launch-kit',
  '/content-matrix': '/consistency-check',
  '/experiments': '/content-matrix',
  '/monetization-map': '/experiments',
  '/review': '/monetization-map',
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
