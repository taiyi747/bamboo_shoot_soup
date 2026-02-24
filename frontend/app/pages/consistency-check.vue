<script setup lang="ts">
import { z } from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import { useApiClient } from '../services/api/client'
import { generationFeedbackCopy } from '../constants/generation-feedback'

const api = useApiClient()
const { track } = useAnalytics()
const { state, selectedPrimaryModel } = useMvpFlow()

const schema = z.object({
  draft: z.string().min(40, '请先输入草稿（至少 40 字），再执行一致性检查。'),
})

type Schema = z.output<typeof schema>

const formState = reactive<Schema>({
  draft:
    state.value.draftToCheck ||
    '先说结论：上班族做内容不需要追求花哨表达，先建立每周稳定发布，再逐步优化转化。',
})

const loading = ref(false)
const errorMessage = ref('')
const feedbackMeta = { ui_feedback_variant: 'card_skeleton' }
const feedbackCopy = generationFeedbackCopy.consistencyCheck
const {
  currentHint: currentLoadingHint,
  start: startLoadingFeedback,
  stop: stopLoadingFeedback,
  reset: resetLoadingFeedback,
} = useLoadingFeedback(feedbackCopy.hints)

const onSubmit = async (event: FormSubmitEvent<Schema>) => {
  if (loading.value) {
    return
  }

  if (!selectedPrimaryModel.value || !state.value.persona) {
    errorMessage.value = '请先完成主身份、人格宪法与启动包。'
    return
  }

  const startedAt = Date.now()
  loading.value = true
  errorMessage.value = ''
  resetLoadingFeedback()
  startLoadingFeedback()
  try {
    state.value.draftToCheck = event.data.draft
    const result = await api.runConsistencyCheck({
      draft: event.data.draft,
      identityModel: selectedPrimaryModel.value,
      constitution: state.value.persona,
    })

    state.value.consistencyCheck = result.result
    await track('consistency_check_triggered', selectedPrimaryModel.value.id, {
      ...feedbackMeta,
      loading_duration_ms: Date.now() - startedAt,
    })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '一致性检查失败。'
  } finally {
    loading.value = false
    stopLoadingFeedback()
    resetLoadingFeedback()
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto w-full">
    <UCard class="surface-card ring-1 ring-slate-200 dark:ring-slate-800">
      <template #header>
        <div class="flex items-center gap-4">
          <div class="p-3 bg-sky-50 dark:bg-sky-950/50 rounded-2xl">
             <UIcon name="i-lucide-check-circle" class="w-8 h-8 text-sky-500" />
          </div>
          <div class="flex-1">
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">
              内容草稿一致性检查
            </h2>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              发文前必备。AI 将依据你的『人格宪法』校验草稿里的每一句话是否破除人设护城河，是否触碰风险禁区。
            </p>
          </div>
        </div>
      </template>

      <UAlert
        v-if="errorMessage"
        color="error"
        variant="soft"
        title="检查失败"
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

      <UForm :schema="schema" :state="formState" class="space-y-6" @submit="onSubmit">
        <UFormField label="输入待发布草稿文本区" name="draft" class="w-full">
           <template #description><span class="text-xs text-slate-500">可粘贴你准备发送的文章正文、脚本段落或是观点长文。</span></template>
          <UTextarea 
            v-model="formState.draft" 
            :rows="8" 
            class="w-full touch-target shadow-sm focus:ring-primary-500" 
            placeholder="将准备发在社交媒体的初版草稿粘贴在这里..."
          />
        </UFormField>

        <div class="flex flex-col sm:flex-row gap-3 pt-2">
          <UButton 
            type="submit" 
            class="touch-target flex-1 sm:flex-none justify-center px-8 font-semibold shadow-md" 
            :loading="loading"
            size="lg"
            icon="i-lucide-eye"
            color="info"
          >
            执行人格一致性检查
          </UButton>
          <NuxtLink to="/review" class="flex-1 sm:flex-none">
            <UButton 
              color="neutral" 
              variant="outline" 
              class="touch-target justify-center w-full font-medium h-full" 
              size="lg"
              trailing-icon="i-lucide-arrow-right"
              :disabled="loading || !state.consistencyCheck"
            >
              继续前往交付汇总
            </UButton>
          </NuxtLink>
        </div>
      </UForm>

      <div v-if="state.consistencyCheck" class="mt-8 space-y-6 pt-6 border-t border-slate-200 dark:border-slate-800">
        <UAlert
          v-if="state.consistencyCheck.riskWarning"
          color="warning"
          variant="soft"
          title="触发风险/禁区警告"
          :description="state.consistencyCheck.riskWarning"
          icon="i-lucide-shield-alert"
          class="ring-1 ring-amber-500/20"
        />

        <UCard class="surface-card border-none bg-slate-50 dark:bg-slate-900/50">
          <template #header>
            <div class="flex items-center justify-between">
               <div class="flex items-center gap-2">
                  <UIcon name="i-lucide-file-search" class="text-slate-500" />
                  <h3 class="text-lg font-bold text-slate-900 dark:text-white">
                    Agent 诊断报告
                  </h3>
               </div>
              <div class="flex items-center gap-3">
                 <span class="text-sm font-semibold text-slate-500 dark:text-slate-400">人设吻合度</span>
                 <div class="flex items-center gap-1.5 px-3 py-1 rounded-full text-white font-bold" 
                    :class="state.consistencyCheck.score >= 80 ? 'bg-emerald-500' : state.consistencyCheck.score >= 60 ? 'bg-amber-500' : 'bg-rose-500'">
                    <span>{{ state.consistencyCheck.score }}</span>
                 </div>
              </div>
            </div>
          </template>

          <div class="grid gap-6 md:grid-cols-3">
            <div class="bg-white dark:bg-slate-900 p-4 rounded-xl shadow-sm ring-1 ring-slate-200 dark:ring-slate-800">
              <div class="flex items-center gap-2 mb-3 text-rose-600 dark:text-rose-400">
                 <UIcon name="i-lucide-zap-off" />
                 <p class="text-sm font-bold uppercase tracking-wider">发现偏离项</p>
              </div>
              <ul v-if="state.consistencyCheck.deviations.length" class="list-disc space-y-2 pl-4 text-sm text-slate-700 dark:text-slate-300">
                <li v-for="item in state.consistencyCheck.deviations" :key="item" class="leading-relaxed">
                  {{ item }}
                </li>
              </ul>
              <p v-else class="text-sm text-slate-400 italic">当前草稿无可感知的严重偏离。</p>
            </div>

            <div class="bg-white dark:bg-slate-900 p-4 rounded-xl shadow-sm ring-1 ring-slate-200 dark:ring-slate-800">
              <div class="flex items-center gap-2 mb-3 text-amber-600 dark:text-amber-500">
                 <UIcon name="i-lucide-help-circle" />
                 <p class="text-sm font-bold uppercase tracking-wider">偏离原因 / 冲突</p>
              </div>
              <ul v-if="state.consistencyCheck.reasons.length" class="list-disc space-y-2 pl-4 text-sm text-slate-700 dark:text-slate-300">
                <li v-for="item in state.consistencyCheck.reasons" :key="item" class="leading-relaxed">
                  {{ item }}
                </li>
              </ul>
              <p v-else class="text-sm text-slate-400 italic">这通常意味着目前的表述非常符合人设设定。</p>
            </div>

            <div class="bg-white dark:bg-slate-900 p-4 rounded-xl shadow-sm ring-1 ring-slate-200 dark:ring-slate-800">
              <div class="flex items-center gap-2 mb-3 text-emerald-600 dark:text-emerald-400">
                 <UIcon name="i-lucide-lightbulb" />
                 <p class="text-sm font-bold uppercase tracking-wider">重构建议修改项</p>
              </div>
              <ul v-if="state.consistencyCheck.suggestions.length" class="list-disc space-y-2 pl-4 text-sm text-slate-700 dark:text-slate-300">
                <li v-for="item in state.consistencyCheck.suggestions" :key="item" class="leading-relaxed">
                  {{ item }}
                </li>
              </ul>
              <p v-else class="text-sm text-slate-400 italic">保持当前语感，直接发布！</p>
            </div>
          </div>
        </UCard>
      </div>
    </UCard>
  </div>
</template>
