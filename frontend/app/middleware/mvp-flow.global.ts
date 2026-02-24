type GuardFn = () => boolean

const guards: Record<string, GuardFn> = {
  '/identity-models': () => Boolean(useMvpFlow().state.value.profile),
  '/persona-constitution': () => Boolean(useMvpFlow().state.value.selectedPrimaryId),
  '/launch-kit': () => Boolean(useMvpFlow().state.value.persona),
  '/consistency-check': () => Boolean(useMvpFlow().state.value.launchKit),
  '/review': () => Boolean(useMvpFlow().state.value.consistencyCheck),
  '/content-matrix': () => Boolean(useMvpFlow().state.value.consistencyCheck),
  '/experiments': () => useMvpFlow().state.value.contentMatrixes.length > 0,
  '/monetization-map': () => useMvpFlow().state.value.experiments.length > 0,
  '/identity-portfolio': () => Boolean(useMvpFlow().state.value.selectedPrimaryId),
  '/simulator': () => Boolean(useMvpFlow().state.value.launchKit),
  '/asset-library': () => useMvpFlow().state.value.simulatorEvaluations.length > 0
    || useMvpFlow().state.value.viewpointAssets.length > 0,
}

const fallbackRoute: Record<string, string> = {
  '/identity-models': '/onboarding',
  '/persona-constitution': '/identity-models',
  '/launch-kit': '/persona-constitution',
  '/consistency-check': '/launch-kit',
  '/review': '/consistency-check',
  '/content-matrix': '/review',
  '/experiments': '/content-matrix',
  '/monetization-map': '/experiments',
  '/identity-portfolio': '/monetization-map',
  '/simulator': '/review',
  '/asset-library': '/simulator',
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
