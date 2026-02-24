<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    title: string
    description: string
    hint: string
    icon?: string
    color?: 'primary' | 'info' | 'neutral'
  }>(),
  {
    icon: 'i-lucide-loader-circle',
    color: 'primary',
  }
)

const iconColorClass = computed(() => {
  if (props.color === 'info') {
    return 'text-sky-500'
  }
  if (props.color === 'neutral') {
    return 'text-slate-500'
  }
  return 'text-primary-500'
})
</script>

<template>
  <UCard class="mb-6 ring-1 ring-slate-200 dark:ring-slate-800" data-testid="generation-feedback-card">
    <div class="space-y-4">
      <div class="flex items-start gap-3">
        <div class="p-2 rounded-xl bg-slate-100 dark:bg-slate-900">
          <UIcon :name="icon" class="w-5 h-5 animate-spin" :class="iconColorClass" />
        </div>
        <div class="space-y-1">
          <h3 class="text-sm font-semibold text-slate-900 dark:text-white">
            {{ title }}
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">
            {{ description }}
          </p>
          <UBadge :color="color" variant="soft" class="mt-1">
            {{ hint }}
          </UBadge>
        </div>
      </div>

      <div class="space-y-2">
        <USkeleton class="h-3 w-11/12" />
        <USkeleton class="h-3 w-9/12" />
        <USkeleton class="h-3 w-10/12" />
      </div>
    </div>
  </UCard>
</template>
