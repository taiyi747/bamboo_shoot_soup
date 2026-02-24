<script setup lang="ts">
const route = useRoute()
const { state } = useMvpFlow()

const steps = [
  { to: '/onboarding', label: '身份诊断', icon: 'i-lucide-clipboard-list' },
  { to: '/identity-models', label: '身份模型', icon: 'i-lucide-users' },
  { to: '/persona-constitution', label: '人格宪法', icon: 'i-lucide-scroll' },
  { to: '/launch-kit', label: '启动包', icon: 'i-lucide-rocket' },
  { to: '/consistency-check', label: '一致性检查', icon: 'i-lucide-check-circle' },
  { to: '/review', label: '交付汇总', icon: 'i-lucide-package-check' },
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

const colorMode = useColorMode()
const isDark = computed({
  get () {
    return colorMode.value === 'dark'
  },
  set () {
    colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
  }
})
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div class="flex items-center gap-3">
          <div class="bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 p-2 rounded-xl">
            <UIcon name="i-lucide-sprout" class="w-6 h-6" />
          </div>
          <div>
            <h1 class="text-xl font-bold bg-gradient-to-r from-primary-600 to-emerald-400 bg-clip-text text-transparent">
              Bamboo Shoot Soup
            </h1>
            <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-widest mt-0.5">
              职场创作者身份工作台
            </p>
          </div>
        </div>
        <UButton
          :icon="isDark ? 'i-lucide-moon' : 'i-lucide-sun'"
          color="neutral"
          variant="ghost"
          class="self-end sm:self-auto rounded-full"
          @click="isDark = !isDark"
          aria-label="Toggle color mode"
        />
      </div>

      <nav class="step-nav">
        <NuxtLink
          v-for="step in steps"
          :key="step.to"
          :to="canVisit(step.to) ? step.to : route.path"
          class="block"
        >
          <UButton
            :color="route.path === step.to ? 'primary' : 'neutral'"
            :variant="route.path === step.to ? 'soft' : 'ghost'"
            :icon="step.icon"
            class="touch-target w-full justify-start font-medium transition-all duration-200"
            :class="[route.path === step.to ? 'ring-1 ring-primary-500/20 shadow-sm' : 'opacity-70 hover:opacity-100']"
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
