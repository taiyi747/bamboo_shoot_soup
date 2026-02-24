<script setup lang="ts">
import { useApiClient } from '../services/api/client'
import { generationFeedbackCopy } from '../constants/generation-feedback'
import type { PersonaConstitution } from '../types/flow'

const api = useApiClient()
const { state, selectedPrimaryModel } = useMvpFlow()

const loading = ref(false)
const errorMessage = ref('')
const feedbackCopy = generationFeedbackCopy.personaConstitution
const {
  currentHint: currentLoadingHint,
  start: startLoadingFeedback,
  stop: stopLoadingFeedback,
  reset: resetLoadingFeedback,
} = useLoadingFeedback(feedbackCopy.hints)

const form = reactive({
  commonWords: '',
  forbiddenWords: '',
  sentencePreferences: '',
  immutablePositions: '',
  narrativeMainline: '',
  growthArc: '',
})

const fillForm = (constitution: PersonaConstitution) => {
  form.commonWords = constitution.commonWords.join('\n')
  form.forbiddenWords = constitution.forbiddenWords.join('\n')
  form.sentencePreferences = constitution.sentencePreferences.join('\n')
  form.immutablePositions = constitution.immutablePositions.join('\n')
  form.narrativeMainline = constitution.narrativeMainline
  form.growthArc = constitution.growthArc.map(item => item.stage + "：" + item.storyTemplate).join('\n')
}

const splitLines = (value: string) =>
  value
    .split('\n')
    .map(item => item.trim())
    .filter(Boolean)

const saveDraft = () => {
  state.value.persona = {
    commonWords: splitLines(form.commonWords),
    forbiddenWords: splitLines(form.forbiddenWords),
    sentencePreferences: splitLines(form.sentencePreferences),
    immutablePositions: splitLines(form.immutablePositions),
    narrativeMainline: form.narrativeMainline.trim(),
    growthArc: splitLines(form.growthArc).map(line => {
      const [stage, ...rest] = line.split('：')
      return {
        stage: stage || '阶段',
        storyTemplate: rest.join('：') || line,
      }
    }),
  }
}

const generateConstitution = async () => {
  if (loading.value) {
    return
  }

  if (!selectedPrimaryModel.value) {
    errorMessage.value = '请先在上一页选择主身份。'
    return
  }

  loading.value = true
  errorMessage.value = ''
  resetLoadingFeedback()
  startLoadingFeedback()
  try {
    const result = await api.generatePersonaConstitution({
      identityModel: selectedPrimaryModel.value,
    })
    state.value.persona = result.constitution
    fillForm(result.constitution)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '人格宪法生成失败。'
  } finally {
    loading.value = false
    stopLoadingFeedback()
    resetLoadingFeedback()
  }
}

const nextStep = async () => {
  if (loading.value) {
    return
  }
  saveDraft()
  await navigateTo('/launch-kit')
}

if (state.value.persona) {
  fillForm(state.value.persona)
}
</script>

<template>
  <div class="max-w-4xl mx-auto w-full">
    <UCard class="surface-card ring-1 ring-slate-200 dark:ring-slate-800">
      <template #header>
        <div class="flex items-center gap-4">
          <div class="p-3 bg-emerald-50 dark:bg-emerald-950/50 rounded-2xl">
            <UIcon name="i-lucide-scroll" class="w-8 h-8 text-primary-500" />
          </div>
          <div class="flex-1">
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">
              人格宪法
            </h2>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              为选定的主身份生成不可动摇的人设护城河：口吻词典、观点立场与叙事主线。
            </p>
          </div>
          
           <div class="hidden sm:flex items-center gap-3">
            <UButton 
              class="touch-target font-medium shadow-sm" 
              color="neutral" 
              variant="outline" 
              icon="i-lucide-sparkles"
              :loading="loading" 
              @click="generateConstitution"
            >
              一键生成宪法
            </UButton>
            <UButton 
              color="primary" 
              class="touch-target font-semibold shadow-md" 
              trailing-icon="i-lucide-arrow-right"
              :disabled="loading"
              @click="nextStep"
            >
              保存并进入启动包
            </UButton>
          </div>
        </div>
      </template>

      <UAlert
        v-if="errorMessage"
        color="error"
        variant="soft"
        title="操作失败"
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

      <div v-if="!state.persona && !loading" class="flex flex-col items-center justify-center py-12 px-4 text-center border border-dashed border-slate-300 dark:border-slate-800 rounded-3xl">
         <div class="w-16 h-16 bg-slate-100 dark:bg-slate-900 rounded-2xl flex items-center justify-center mb-4">
           <UIcon name="i-lucide-feather" class="w-8 h-8 text-slate-400" />
         </div>
         <h3 class="text-lg font-semibold mb-2">等待生成宪法</h3>
         <p class="text-slate-500 dark:text-slate-400 max-w-sm mx-auto mb-6 text-sm">
           确保你已经选择了主身份模型，然后点击生成，Agent 会输出符合设定的人格语言规则。
         </p>
         <UButton 
            size="lg" 
            :loading="loading" 
            class="touch-target shadow-md font-semibold" 
            color="primary"
            icon="i-lucide-sparkles" 
            @click="generateConstitution"
          >
            立即生成人格宪法
          </UButton>
      </div>

      <div v-else-if="state.persona" class="space-y-6 lg:space-y-8">
        <div class="grid gap-6 md:grid-cols-2 lg:gap-8">
          <UFormField label="口吻词典：常用词" name="commonWords" class="w-full">
            <template #description><span class="text-xs text-emerald-600 dark:text-emerald-400">强化你的身份特质的积极词汇（每行一个）</span></template>
            <UTextarea v-model="form.commonWords" :rows="5" class="w-full touch-target transition-shadow focus:ring-primary-500 font-mono text-sm" />
          </UFormField>
          
          <UFormField label="口吻词典：禁用词" name="forbiddenWords" class="w-full">
            <template #description><span class="text-xs text-rose-500 dark:text-rose-400">绝对不能说、会破坏人设的词汇（每行一个）</span></template>
            <UTextarea v-model="form.forbiddenWords" :rows="5" class="w-full touch-target transition-shadow focus:ring-rose-500 font-mono text-sm border-rose-100 dark:border-rose-900/50" />
          </UFormField>
          
          <UFormField label="句式偏好" name="sentencePreferences" class="w-full">
             <template #description><span class="text-xs text-slate-500">你的招牌说话方式，如排比、问句等（每行一个）</span></template>
            <UTextarea v-model="form.sentencePreferences" :rows="5" class="w-full touch-target font-mono text-sm" />
          </UFormField>
          
          <UFormField label="观点护城河" name="immutablePositions" class="w-full">
             <template #description><span class="text-xs text-amber-600 dark:text-amber-500">即使掉粉也绝对不能动摇的强观点（每行一个）</span></template>
            <UTextarea v-model="form.immutablePositions" :rows="5" class="w-full touch-target font-mono text-sm" />
          </UFormField>
        </div>

        <div class="bg-slate-50 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 space-y-6">
          <div class="flex items-center gap-2 mb-2">
            <UIcon name="i-lucide-route" class="w-5 h-5 text-primary-500" />
            <h3 class="font-bold text-slate-900 dark:text-white">叙事与成长路径</h3>
          </div>
          
          <UFormField label="叙事主线" class="w-full">
            <UTextarea v-model="form.narrativeMainline" :rows="3" class="w-full touch-target text-sm" />
          </UFormField>
          
          <UFormField label="成长 Arc" class="w-full">
            <template #description><span class="text-xs text-slate-500">格式：阶段：模板，每行一个</span></template>
            <UTextarea v-model="form.growthArc" :rows="4" class="w-full touch-target font-mono text-sm" />
          </UFormField>
        </div>
      </div>

       <div v-if="state.persona || loading" class="mt-8 sm:hidden flex flex-col gap-3 pt-6 border-t border-slate-200 dark:border-slate-800">
           <UButton 
              class="touch-target justify-center font-medium shadow-sm" 
              color="neutral" 
              variant="outline" 
              icon="i-lucide-sparkles"
              size="lg"
              :loading="loading" 
              @click="generateConstitution"
            >
              重新生成
            </UButton>
            <UButton 
              color="primary" 
              class="touch-target justify-center font-semibold shadow-md" 
              size="lg"
              trailing-icon="i-lucide-arrow-right"
              :disabled="loading"
              @click="nextStep"
            >
              保存并进入启动包
            </UButton>
      </div>
    </UCard>
  </div>
</template>

