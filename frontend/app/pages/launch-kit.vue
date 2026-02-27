<script setup lang="ts">
import { useApiClient } from '../services/api/client'
import { generationFeedbackCopy } from '../constants/generation-feedback'
import type { LaunchKitDay } from '../types/flow'

const api = useApiClient()
const { track } = useAnalytics()
const { state, selectedPrimaryModel } = useMvpFlow()

const loading = ref(false)
const errorMessage = ref('')
const feedbackMeta = { ui_feedback_variant: 'card_skeleton' }
const feedbackCopy = generationFeedbackCopy.launchKit
const {
  currentHint: currentLoadingHint,
  start: startLoadingFeedback,
  stop: stopLoadingFeedback,
  reset: resetLoadingFeedback,
} = useLoadingFeedback(feedbackCopy.hints)

type ArticleTab = 'preview' | 'markdown'
type ArticleCacheItem = { title: string; markdown: string }

const articleCache = ref<Record<number, ArticleCacheItem>>({})
const articleLoadingDay = ref<number | null>(null)
const articleError = ref('')
const articleModalOpen = ref(false)
const articleTitle = ref('')
const articleMarkdown = ref('')
const articleTab = ref<ArticleTab>('preview')

const openArticleModal = (article: ArticleCacheItem) => {
  articleTitle.value = article.title
  articleMarkdown.value = article.markdown
  articleTab.value = 'preview'
  articleModalOpen.value = true
}

const generateLaunchKit = async () => {
  if (loading.value) {
    return
  }

  if (!selectedPrimaryModel.value || !state.value.persona) {
    errorMessage.value = 'Please finish identity model and persona first.'
    return
  }

  const startedAt = Date.now()
  loading.value = true
  errorMessage.value = ''
  resetLoadingFeedback()
  startLoadingFeedback()
  try {
    const result = await api.generateLaunchKit({
      identityModel: selectedPrimaryModel.value,
      constitution: state.value.persona,
    })
    state.value.launchKit = result.launchKit
    articleCache.value = {}

    await track('launch_kit_generated', selectedPrimaryModel.value.id, {
      ...feedbackMeta,
      loading_duration_ms: Date.now() - startedAt,
      article_cache_cleared: true,
      article_modal_open_at_regen: articleModalOpen.value,
    })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Launch kit generation failed.'
  } finally {
    loading.value = false
    stopLoadingFeedback()
    resetLoadingFeedback()
  }
}

const generateDayArticle = async (day: LaunchKitDay) => {
  if (!selectedPrimaryModel.value || !state.value.persona) {
    articleError.value = 'Please finish identity model and persona first.'
    return
  }

  const cached = articleCache.value[day.day]
  if (cached) {
    articleError.value = ''
    openArticleModal(cached)
    return
  }

  articleLoadingDay.value = day.day
  articleError.value = ''
  try {
    const result = await api.generateLaunchKitDayArticle({
      identityModel: selectedPrimaryModel.value,
      constitution: state.value.persona,
      dayNo: day.day,
      theme: day.theme,
      draftOutline: day.draftOutline,
      opening: day.opening,
    })

    const article = {
      title: result.title,
      markdown: result.markdown,
    }
    articleCache.value[day.day] = article
    openArticleModal(article)
  } catch (error) {
    articleError.value = error instanceof Error ? error.message : 'Day article generation failed.'
  } finally {
    if (articleLoadingDay.value === day.day) {
      articleLoadingDay.value = null
    }
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto w-full">
    <UCard class="surface-card ring-1 ring-slate-200 dark:ring-slate-800">
      <template #header>
        <div class="flex items-center gap-4">
          <div class="p-3 bg-indigo-50 dark:bg-indigo-950/50 rounded-2xl">
            <UIcon name="i-lucide-rocket" class="w-8 h-8 text-indigo-500 dark:text-indigo-400" />
          </div>
          <div class="flex-1">
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">
              7-Day Launch Kit
            </h2>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              Generate your 7-day schedule and draft starters, then expand each day into a full article.
            </p>
          </div>

          <div v-if="state.launchKit" class="hidden sm:flex items-center gap-3">
            <UButton
              class="touch-target font-medium shadow-sm"
              color="neutral"
              variant="outline"
              icon="i-lucide-refresh-cw"
              :loading="loading"
              data-testid="launch-kit-regenerate-button"
              @click="generateLaunchKit"
            >
              Regenerate
            </UButton>
            <NuxtLink to="/consistency-check">
              <UButton
                color="primary"
                class="touch-target font-semibold shadow-md"
                trailing-icon="i-lucide-arrow-right"
                :disabled="loading"
              >
                Continue
              </UButton>
            </NuxtLink>
          </div>
        </div>
      </template>

      <UAlert
        v-if="errorMessage"
        color="error"
        variant="soft"
        title="Failed"
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

      <div
        v-if="!state.launchKit && !loading"
        class="flex flex-col items-center justify-center py-16 px-4 text-center border border-dashed border-slate-300 dark:border-slate-800 rounded-3xl"
      >
        <div class="w-20 h-20 bg-indigo-50 dark:bg-indigo-950/30 rounded-full flex items-center justify-center mb-6">
          <UIcon name="i-lucide-rocket" class="w-10 h-10 text-indigo-500" />
        </div>
        <h3 class="text-xl font-semibold mb-2">Ready to Start</h3>
        <p class="text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-8">
          Generate your first 7-day launch kit.
        </p>
        <UButton
          size="xl"
          :loading="loading"
          class="touch-target shadow-lg px-8 font-semibold"
          color="primary"
          icon="i-lucide-sparkles"
          data-testid="launch-kit-generate-button"
          @click="generateLaunchKit"
        >
          Generate 7-Day Launch Kit
        </UButton>
      </div>

      <div v-else-if="state.launchKit" class="space-y-8">
        <UAlert
          v-if="articleError"
          color="error"
          variant="soft"
          title="Day Article Failed"
          :description="articleError"
          class="mb-2"
          data-testid="day-article-inline-error"
        />
        <div>
          <div class="flex items-center gap-2 mb-4">
            <UIcon name="i-lucide-calendar-days" class="w-5 h-5 text-slate-700 dark:text-slate-300" />
            <h3 class="text-lg font-bold text-slate-900 dark:text-white">Week 1 Schedule (Day 1-7)</h3>
          </div>
          <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <UCard
              v-for="day in state.launchKit.days"
              :key="day.day"
              class="surface-card ring-1 ring-slate-100 dark:ring-slate-800/60 hover:shadow-md transition-shadow relative overflow-hidden group"
            >
              <div class="absolute top-0 right-0 w-24 h-24 bg-indigo-50 dark:bg-indigo-900/10 rounded-bl-full -z-10 group-hover:bg-indigo-100 dark:group-hover:bg-indigo-900/20 transition-colors"></div>
              <template #header>
                <div class="flex items-center justify-between">
                  <h4 class="text-2xl font-black text-indigo-950/20 dark:text-indigo-100/10 tracking-widest">
                    D{{ day.day }}
                  </h4>
                  <UBadge color="primary" variant="soft" class="font-semibold uppercase tracking-wider">Day {{ day.day }}</UBadge>
                </div>
              </template>
              <div class="space-y-4 text-sm text-slate-600 dark:text-slate-300">
                <div>
                  <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">Theme</p>
                  <p class="font-semibold text-slate-800 dark:text-slate-200 text-base leading-tight">{{ day.theme }}</p>
                </div>

                <div class="bg-slate-50 dark:bg-slate-900/50 p-3 rounded-lg border border-slate-100 dark:border-slate-800">
                  <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">Draft Outline</p>
                  <p class="leading-relaxed">{{ day.draftOutline }}</p>
                </div>
                <div>
                  <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">Opening Hook</p>
                  <div class="flex gap-2 text-indigo-700 dark:text-indigo-400 italic">
                    <UIcon name="i-lucide-quote" class="w-4 h-4 flex-shrink-0 mt-0.5 opacity-50" />
                    <p>{{ day.opening }}</p>
                  </div>
                </div>

                <UButton
                  class="w-full"
                  color="primary"
                  variant="soft"
                  :loading="articleLoadingDay === day.day"
                  :data-testid="`day-article-generate-${day.day}`"
                  @click="generateDayArticle(day)"
                >
                  Generate Day {{ day.day }} Article
                </UButton>
              </div>
            </UCard>
          </div>
        </div>

        <div class="grid gap-6 md:grid-cols-2 pt-6 border-t border-slate-100 dark:border-slate-800">
          <UCard class="surface-card border border-emerald-100 dark:border-emerald-900/30 bg-emerald-50/30 dark:bg-emerald-950/10">
            <template #header>
              <div class="flex items-center gap-2">
                <div class="p-2 bg-emerald-100 dark:bg-emerald-900/50 rounded-lg">
                  <UIcon name="i-lucide-layout-template" class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                </div>
                <h3 class="text-lg font-bold text-slate-900 dark:text-white">Sustainable Columns</h3>
              </div>
            </template>
            <ul class="space-y-3">
              <li v-for="(column, index) in state.launchKit.sustainableColumns" :key="column" class="flex items-start gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl shadow-sm ring-1 ring-emerald-500/10">
                <div class="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-xs font-bold">
                  {{ index + 1 }}
                </div>
                <span class="text-sm font-medium text-slate-700 dark:text-slate-300 pt-0.5">{{ column }}</span>
              </li>
            </ul>
          </UCard>

          <UCard class="surface-card border border-amber-100 dark:border-amber-900/30 bg-amber-50/30 dark:bg-amber-950/10">
            <template #header>
              <div class="flex items-center gap-2">
                <div class="p-2 bg-amber-100 dark:bg-amber-900/50 rounded-lg">
                  <UIcon name="i-lucide-microscope" class="w-5 h-5 text-amber-600 dark:text-amber-500" />
                </div>
                <h3 class="text-lg font-bold text-slate-900 dark:text-white">Growth Experiment</h3>
              </div>
            </template>
            <div class="space-y-4 text-sm">
              <div class="bg-white dark:bg-slate-900 p-4 rounded-xl shadow-sm ring-1 ring-amber-500/10">
                <p class="text-xs font-bold text-amber-600/70 dark:text-amber-500/70 uppercase tracking-wider mb-1">Hypothesis</p>
                <p class="font-semibold text-slate-800 dark:text-slate-200">{{ state.launchKit.growthExperiment.hypothesis }}</p>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="bg-white dark:bg-slate-900 p-3 rounded-lg shadow-sm ring-1 ring-amber-500/10">
                  <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">Variables</p>
                  <p class="font-medium text-slate-700 dark:text-slate-300">{{ state.launchKit.growthExperiment.variables.join(' / ') }}</p>
                </div>
                <div class="bg-white dark:bg-slate-900 p-3 rounded-lg shadow-sm ring-1 ring-amber-500/10">
                  <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">Cycle</p>
                  <p class="font-medium text-slate-700 dark:text-slate-300">{{ state.launchKit.growthExperiment.executionCycle }}</p>
                </div>
                <div class="col-span-2 bg-white dark:bg-slate-900 p-3 rounded-lg shadow-sm ring-1 ring-amber-500/10">
                  <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">Success Metric</p>
                  <p class="font-medium text-amber-700 dark:text-amber-500">{{ state.launchKit.growthExperiment.successMetric }}</p>
                </div>
              </div>
            </div>
          </UCard>
        </div>
      </div>

      <div v-if="state.launchKit || loading" class="mt-8 sm:hidden flex flex-col gap-3 pt-6 border-t border-slate-200 dark:border-slate-800">
        <UButton
          class="touch-target justify-center font-medium shadow-sm"
          color="neutral"
          variant="outline"
          icon="i-lucide-refresh-cw"
          size="lg"
          :loading="loading"
          data-testid="launch-kit-regenerate-button-mobile"
          @click="generateLaunchKit"
        >
          Regenerate
        </UButton>
        <NuxtLink to="/consistency-check" class="w-full block">
          <UButton
            color="primary"
            class="touch-target justify-center font-semibold shadow-md w-full"
            size="lg"
            trailing-icon="i-lucide-arrow-right"
            :disabled="loading"
          >
            Continue
          </UButton>
        </NuxtLink>
      </div>
    </UCard>

    <div
      v-if="articleModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4"
      data-testid="day-article-modal"
    >
      <div class="w-full max-w-3xl max-h-[90vh] overflow-hidden rounded-2xl bg-white dark:bg-slate-950 shadow-2xl ring-1 ring-slate-200 dark:ring-slate-800">
        <div class="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-800">
          <h4 class="text-lg font-semibold text-slate-900 dark:text-slate-100" data-testid="day-article-title">{{ articleTitle }}</h4>
          <UButton color="neutral" variant="ghost" icon="i-lucide-x" data-testid="day-article-close" @click="articleModalOpen = false" />
        </div>

        <div class="px-5 pt-4">
          <UAlert
            v-if="articleError"
            color="error"
            variant="soft"
            title="Article Generation Failed"
            :description="articleError"
            class="mb-4"
            data-testid="day-article-error"
          />

          <div class="flex gap-2 mb-4">
            <UButton
              size="sm"
              :color="articleTab === 'preview' ? 'primary' : 'neutral'"
              :variant="articleTab === 'preview' ? 'solid' : 'outline'"
              data-testid="day-article-tab-preview"
              @click="articleTab = 'preview'"
            >
              Preview
            </UButton>
            <UButton
              size="sm"
              :color="articleTab === 'markdown' ? 'primary' : 'neutral'"
              :variant="articleTab === 'markdown' ? 'solid' : 'outline'"
              data-testid="day-article-tab-markdown"
              @click="articleTab = 'markdown'"
            >
              Markdown
            </UButton>
          </div>
        </div>

        <div class="px-5 pb-5 overflow-y-auto max-h-[68vh]">
          <div v-if="articleTab === 'preview'" class="prose prose-slate dark:prose-invert max-w-none whitespace-pre-wrap" data-testid="day-article-preview">
            {{ articleMarkdown }}
          </div>
          <pre v-else class="text-xs leading-relaxed bg-slate-100 dark:bg-slate-900 rounded-xl p-4 overflow-x-auto" data-testid="day-article-markdown">{{ articleMarkdown }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>
