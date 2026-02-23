<script setup lang="ts">
const route = useRoute()
const { state } = useMvpFlow()

const steps = [
  { to: '/onboarding', label: '身份诊断' },
  { to: '/identity-models', label: '身份模型' },
  { to: '/persona-constitution', label: '人格宪法' },
  { to: '/launch-kit', label: '启动包' },
  { to: '/consistency-check', label: '一致性检查' },
  { to: '/review', label: '交付汇总' },
]

const canVisit = (to: string) => {
  const s = state.value
  if (to === '/identity-models') return Boolean(s.profile)
  if (to === '/persona-constitution') return Boolean(s.selectedPrimaryId)
  if (to === '/launch-kit') return Boolean(s.persona)
  if (to === '/consistency-check') return Boolean(s.launchKit)
  if (to === '/review') return Boolean(s.consistencyCheck)
  return true
}
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="mb-3 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-xs font-semibold tracking-[0.18em] text-slate-600">
            BAMBOO SHOOT SOUP
          </p>
          <h1 class="text-lg font-semibold text-slate-900">
            职场创作者身份设计工作台
          </h1>
        </div>
      </div>

      <nav class="step-nav">
        <NuxtLink
          v-for="step in steps"
          :key="step.to"
          :to="canVisit(step.to) ? step.to : route.path"
        >
          <UButton
            :color="route.path === step.to ? 'primary' : 'neutral'"
            :variant="route.path === step.to ? 'solid' : 'outline'"
            class="touch-target w-full justify-start"
            :disabled="!canVisit(step.to)"
          >
            {{ step.label }}
          </UButton>
        </NuxtLink>
      </nav>
    </header>

    <main class="main-panel">
      <slot />
    </main>
  </div>
</template>
