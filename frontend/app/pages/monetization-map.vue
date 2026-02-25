<script setup lang="ts">
import { generationFeedbackCopy } from '../constants/generation-feedback'
import { useApiClient } from '../services/api/client'

const api = useApiClient()
const { track } = useAnalytics()
const { state, selectedPrimaryModel } = useMvpFlow()

const loading = ref(false)
const errorMessage = ref('')
const feedbackCopy = generationFeedbackCopy.monetizationMap
const {
  currentHint: currentLoadingHint,
  start: startLoadingFeedback,
  stop: stopLoadingFeedback,
  reset: resetLoadingFeedback,
} = useLoadingFeedback(feedbackCopy.hints)

const generateMonetizationMap = async () => {
  if (loading.value) {
    return
  }

  if (!selectedPrimaryModel.value || !state.value.persona) {
    errorMessage.value = '请先完成主身份与人格宪法。'
    return
  }

  loading.value = true
  errorMessage.value = ''
  resetLoadingFeedback()
  startLoadingFeedback()
  try {
    const result = await api.generateMonetizationMap({
      identityModel: selectedPrimaryModel.value,
      constitution: state.value.persona,
    })
    state.value.monetizationMap = result.monetizationMap
    await track('monetization_plan_started', selectedPrimaryModel.value.id, {
      weeks: result.monetizationMap.weeks.length,
    })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '变现路线图生成失败。'
  } finally {
    loading.value = false
    stopLoadingFeedback()
    resetLoadingFeedback()
  }
}

const goReview = async () => {
  if (!state.value.monetizationMap) {
    return
  }
  await navigateTo('/review')
}
</script>

<template>
  <div class="max-w-6xl mx-auto w-full">
    <UCard class="surface-card ring-1 ring-slate-200 dark:ring-slate-800">
      <template #header>
        <div class="flex items-center gap-4">
          <div class="p-3 bg-teal-50 dark:bg-teal-950/50 rounded-2xl">
            <UIcon name="i-lucide-trending-up" class="w-8 h-8 text-teal-500" />
          </div>
          <div class="flex-1">
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">12 周变现路线图</h2>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              生成主路径与备选路径，并给出每周任务、交付物和验证指标。
            </p>
          </div>
          <div class="hidden sm:flex items-center gap-3">
            <UButton
              color="neutral"
              variant="outline"
              class="touch-target"
              icon="i-lucide-refresh-cw"
              :loading="loading"
              @click="generateMonetizationMap"
            >
              重新生成
            </UButton>
            <UButton
              color="primary"
              class="touch-target shadow-md font-semibold"
              trailing-icon="i-lucide-arrow-right"
              :disabled="loading || !state.monetizationMap"
              @click="goReview"
            >
              进入交付汇总
            </UButton>
          </div>
        </div>
      </template>

      <UAlert
        v-if="errorMessage"
        color="error"
        variant="soft"
        title="生成失败"
        :description="errorMessage"
        icon="i-lucide-alert-circle"
        class="mb-6"
      />

      <GenerationFeedbackCard
        v-if="loading"
        :title="feedbackCopy.title"
        :description="feedbackCopy.description"
        :hint="currentLoadingHint"
        :icon="feedbackCopy.icon"
        :color="feedbackCopy.color"
      />

      <div v-if="!state.monetizationMap && !loading" class="flex flex-col items-center justify-center py-14 text-center border border-dashed border-slate-300 dark:border-slate-800 rounded-3xl">
        <h3 class="text-xl font-semibold">生成 12 周变现图</h3>
        <p class="mt-2 text-sm text-slate-500 dark:text-slate-400 max-w-md">
          输出周任务、周交付和验证指标，帮助你在 8-12 周内验证第一条变现路径。
        </p>
        <UButton class="mt-6 touch-target shadow-md" size="lg" icon="i-lucide-sparkles" @click="generateMonetizationMap">
          一键生成变现路线图
        </UButton>
      </div>

      <div v-else-if="state.monetizationMap" class="space-y-6">
        <div class="grid gap-4 md:grid-cols-2">
          <UCard class="surface-card border border-teal-100 dark:border-teal-900/30 bg-teal-50/10 dark:bg-teal-950/5">
            <template #header>
              <h3 class="font-semibold text-slate-900 dark:text-white">主路径</h3>
            </template>
            <p class="text-sm text-slate-700 dark:text-slate-300">{{ state.monetizationMap.primaryPath }}</p>
          </UCard>
          <UCard class="surface-card border border-sky-100 dark:border-sky-900/30 bg-sky-50/10 dark:bg-sky-950/5">
            <template #header>
              <h3 class="font-semibold text-slate-900 dark:text-white">备选路径</h3>
            </template>
            <p class="text-sm text-slate-700 dark:text-slate-300">{{ state.monetizationMap.backupPath }}</p>
          </UCard>
        </div>

        <UCard class="surface-card border border-slate-200 dark:border-slate-800">
          <template #header>
            <h3 class="font-semibold text-slate-900 dark:text-white">12 周执行计划</h3>
          </template>

          <div class="overflow-auto">
            <table class="w-full min-w-[720px] text-left text-sm">
              <thead>
                <tr class="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                  <th class="px-3 py-2">Week</th>
                  <th class="px-3 py-2">Goal</th>
                  <th class="px-3 py-2">Task</th>
                  <th class="px-3 py-2">Deliverable</th>
                  <th class="px-3 py-2">Metric</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="week in state.monetizationMap.weeks"
                  :key="week.weekNo"
                  class="border-b border-slate-100 dark:border-slate-800/60"
                >
                  <td class="px-3 py-2 font-mono">{{ week.weekNo }}</td>
                  <td class="px-3 py-2">{{ week.goal }}</td>
                  <td class="px-3 py-2">{{ week.task }}</td>
                  <td class="px-3 py-2">{{ week.deliverable }}</td>
                  <td class="px-3 py-2">{{ week.validationMetric }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </UCard>
      </div>

      <div class="mt-8 sm:hidden flex flex-col gap-3 pt-6 border-t border-slate-200 dark:border-slate-800">
        <UButton
          color="primary"
          class="touch-target justify-center font-semibold"
          trailing-icon="i-lucide-arrow-right"
          :disabled="loading || !state.monetizationMap"
          @click="goReview"
        >
          进入交付汇总
        </UButton>
      </div>
    </UCard>
  </div>
</template>
