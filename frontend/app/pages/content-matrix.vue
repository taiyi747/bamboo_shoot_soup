<script setup lang="ts">
import { generationFeedbackCopy } from '../constants/generation-feedback'
import { useApiClient } from '../services/api/client'

const api = useApiClient()
const { state, selectedPrimaryModel } = useMvpFlow()

const loading = ref(false)
const errorMessage = ref('')
const activePillarIndex = ref(0)
const feedbackCopy = generationFeedbackCopy.contentMatrix
const {
  currentHint: currentLoadingHint,
  start: startLoadingFeedback,
  stop: stopLoadingFeedback,
  reset: resetLoadingFeedback,
} = useLoadingFeedback(feedbackCopy.hints)

const activePillar = computed(() => state.value.contentMatrix?.pillars?.[activePillarIndex.value])

const generateContentMatrix = async () => {
  if (loading.value) {
    return
  }

  if (!selectedPrimaryModel.value || !state.value.persona) {
    errorMessage.value = '请先完成主身份与人格宪法，再生成内容矩阵。'
    return
  }

  loading.value = true
  errorMessage.value = ''
  resetLoadingFeedback()
  startLoadingFeedback()
  try {
    const result = await api.generateContentMatrix({
      identityModel: selectedPrimaryModel.value,
      constitution: state.value.persona,
    })
    state.value.contentMatrix = result.contentMatrix
    activePillarIndex.value = 0
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '内容矩阵生成失败。'
  } finally {
    loading.value = false
    stopLoadingFeedback()
    resetLoadingFeedback()
  }
}

const nextStep = async () => {
  if (!state.value.contentMatrix) {
    return
  }
  await navigateTo('/experiments')
}
</script>

<template>
  <div class="max-w-6xl mx-auto w-full">
    <UCard class="surface-card ring-1 ring-slate-200 dark:ring-slate-800">
      <template #header>
        <div class="flex items-center gap-4">
          <div class="p-3 bg-indigo-50 dark:bg-indigo-950/50 rounded-2xl">
            <UIcon name="i-lucide-grid-2x2" class="w-8 h-8 text-indigo-500" />
          </div>
          <div class="flex-1">
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">内容矩阵</h2>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              基于身份支柱，生成可持续选题池与多平台改写方向。
            </p>
          </div>
          <div class="hidden sm:flex items-center gap-3">
            <UButton
              color="neutral"
              variant="outline"
              class="touch-target"
              icon="i-lucide-refresh-cw"
              :loading="loading"
              @click="generateContentMatrix"
            >
              重新生成
            </UButton>
            <UButton
              color="primary"
              class="touch-target shadow-md font-semibold"
              trailing-icon="i-lucide-arrow-right"
              :disabled="loading || !state.contentMatrix"
              @click="nextStep"
            >
              继续到实验面板
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

      <div v-if="!state.contentMatrix && !loading" class="flex flex-col items-center justify-center py-14 text-center border border-dashed border-slate-300 dark:border-slate-800 rounded-3xl">
        <h3 class="text-xl font-semibold">生成 V1 内容矩阵</h3>
        <p class="mt-2 text-sm text-slate-500 dark:text-slate-400 max-w-md">
          每个内容支柱将生成 20-50 个可执行选题，并给出小红书、公众号、视频号改写角度。
        </p>
        <UButton class="mt-6 touch-target shadow-md" size="lg" icon="i-lucide-sparkles" @click="generateContentMatrix">
          一键生成内容矩阵
        </UButton>
      </div>

      <div v-else-if="state.contentMatrix" class="space-y-6">
        <div class="flex flex-wrap gap-2">
          <UButton
            v-for="(pillar, index) in state.contentMatrix.pillars"
            :key="pillar.pillar"
            :color="activePillarIndex === index ? 'primary' : 'neutral'"
            :variant="activePillarIndex === index ? 'soft' : 'outline'"
            class="touch-target"
            @click="activePillarIndex = index"
          >
            {{ pillar.pillar }}
          </UButton>
        </div>

        <div v-if="activePillar" class="grid gap-6 lg:grid-cols-2">
          <UCard class="surface-card border border-slate-200 dark:border-slate-800">
            <template #header>
              <h3 class="font-semibold text-slate-900 dark:text-white">选题池（{{ activePillar.topics.length }}）</h3>
            </template>
            <ul class="space-y-2 text-sm text-slate-700 dark:text-slate-300 max-h-96 overflow-auto pr-2">
              <li v-for="topic in activePillar.topics" :key="topic" class="rounded-lg px-3 py-2 bg-slate-50 dark:bg-slate-900/50">
                {{ topic }}
              </li>
            </ul>
          </UCard>

          <UCard class="surface-card border border-slate-200 dark:border-slate-800">
            <template #header>
              <h3 class="font-semibold text-slate-900 dark:text-white">平台改写预览</h3>
            </template>
            <div class="space-y-4">
              <div v-for="(rewrites, platform) in activePillar.platformRewrites" :key="platform">
                <p class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">{{ platform }}</p>
                <ul class="space-y-2 text-sm text-slate-700 dark:text-slate-300">
                  <li v-for="rewrite in rewrites" :key="platform + rewrite" class="rounded-lg px-3 py-2 bg-slate-50 dark:bg-slate-900/50">
                    {{ rewrite }}
                  </li>
                </ul>
              </div>
            </div>
          </UCard>
        </div>
      </div>

      <div class="mt-8 sm:hidden flex flex-col gap-3 pt-6 border-t border-slate-200 dark:border-slate-800">
        <UButton
          color="neutral"
          variant="outline"
          class="touch-target justify-center"
          icon="i-lucide-refresh-cw"
          :loading="loading"
          @click="generateContentMatrix"
        >
          重新生成
        </UButton>
        <UButton
          color="primary"
          class="touch-target justify-center font-semibold"
          trailing-icon="i-lucide-arrow-right"
          :disabled="loading || !state.contentMatrix"
          @click="nextStep"
        >
          继续
        </UButton>
      </div>
    </UCard>
  </div>
</template>
