<script setup lang="ts">
import { useApiClient } from '../services/api/client'
import { generationFeedbackCopy } from '../constants/generation-feedback'
import { computed, ref } from 'vue'

const api = useApiClient()
const { track } = useAnalytics()
const { state } = useMvpFlow()

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const feedbackMeta = { ui_feedback_variant: 'card_skeleton' }
const feedbackCopy = generationFeedbackCopy.identityModels
const {
  currentHint: currentLoadingHint,
  start: startLoadingFeedback,
  stop: stopLoadingFeedback,
  reset: resetLoadingFeedback,
} = useLoadingFeedback(feedbackCopy.hints)

const selectedPrimaryId = ref<string | undefined>(state.value.selectedPrimaryId)
const selectedBackupId = ref<string | undefined>(state.value.selectedBackupId)

const toValidToneExamples = (examples: string[]): string[] =>
  examples
    .map(example => example.trim())
    .filter(Boolean)

const getToneExampleCount = (examples: string[]): number =>
  toValidToneExamples(examples).length

const getToneExamplePreview = (examples: string[]): string[] =>
  toValidToneExamples(examples).slice(0, 5)

const generateModels = async () => {
  if (loading.value) {
    return
  }

  if (!state.value.profile) {
    errorMessage.value = '请先完成诊断问卷。'
    return
  }

  const startedAt = Date.now()
  loading.value = true
  errorMessage.value = ''
  resetLoadingFeedback()
  startLoadingFeedback()
  try {
    const result = await api.generateIdentityModels({ profile: state.value.profile })
    state.value.identityModels = result.models
    await track('identity_models_generated', undefined, {
      ...feedbackMeta,
      loading_duration_ms: Date.now() - startedAt,
    })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '身份模型生成失败。'
  } finally {
    loading.value = false
    stopLoadingFeedback()
    resetLoadingFeedback()
  }
}

const validatePrimaryModel = () => {
  const primary = state.value.identityModels.find(model => model.id === selectedPrimaryId.value)
  if (!primary) {
    return '请先选择主身份。'
  }
  if (!primary.differentiation.trim()) {
    return '主身份缺少“差异化定位”。'
  }
  return ''
}

const selectedPrimaryModel = computed(() =>
  state.value.identityModels.find(model => model.id === selectedPrimaryId.value)
)

const toneExampleWarning = computed(() => {
  if (!selectedPrimaryModel.value) {
    return ''
  }

  const toneExamplesCount = getToneExampleCount(selectedPrimaryModel.value.toneExamples)
  if (toneExamplesCount >= 5) {
    return ''
  }

  return `当前主身份仅有 ${toneExamplesCount} 条有效语气示例，建议补齐到 5 条以上。`
})

const saveSelection = async () => {
  if (loading.value || saving.value) {
    return
  }

  const validationError = validatePrimaryModel()
  if (validationError) {
    errorMessage.value = validationError
    return
  }

  if (!selectedBackupId.value) {
    errorMessage.value = '请同时选择备选身份。'
    return
  }

  if (selectedPrimaryId.value === selectedBackupId.value) {
    errorMessage.value = '主身份和备身份不能相同。'
    return
  }

  saving.value = true
  errorMessage.value = ''
  try {
    await api.selectIdentity({
      primaryId: selectedPrimaryId.value!,
      backupId: selectedBackupId.value!,
    })
    state.value.selectedPrimaryId = selectedPrimaryId.value
    state.value.selectedBackupId = selectedBackupId.value

    const toneExamplesCount = selectedPrimaryModel.value
      ? getToneExampleCount(selectedPrimaryModel.value.toneExamples)
      : 0

    await track('identity_selected', selectedPrimaryId.value, {
      tone_examples_count: toneExamplesCount,
      tone_examples_below_5: toneExamplesCount < 5,
    })
    await navigateTo('/persona-constitution')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '身份选择保存失败。'
  } finally {
    saving.value = false
  }
}

const hasModels = computed(() => state.value.identityModels.length > 0)
</script>

<template>
  <div class="space-y-6 max-w-[1200px] mx-auto w-full">
    <UCard class="surface-card ring-1 ring-slate-200 dark:ring-slate-800">
      <template #header>
         <div class="flex items-center gap-4">
          <div class="p-3 bg-primary-50 dark:bg-primary-950 rounded-2xl">
            <UIcon name="i-lucide-users" class="w-8 h-8 text-primary-500" />
          </div>
          <div class="flex-1">
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">
              身份模型生成与选择
            </h2>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              基于你的能力画像，我们将生成 3 个潜力身份模型。请挑选 1 个主身份和 1 个备选身份。
            </p>
          </div>
          
          <div v-if="hasModels" class="hidden sm:flex items-center gap-3">
               <UButton
                color="neutral"
                variant="outline"
                class="touch-target"
                size="lg"
                icon="i-lucide-refresh-cw"
                :loading="loading"
                @click="generateModels"
              >
                重新生成
              </UButton>
              <UButton
                color="primary"
                class="touch-target shadow-md font-semibold"
                size="lg"
                trailing-icon="i-lucide-arrow-right"
                :loading="saving"
                :disabled="loading || saving"
                @click="saveSelection"
              >
                保存选择并继续
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

      <UAlert
        v-if="toneExampleWarning"
        color="warning"
        variant="soft"
        title="语气风格示例建议"
        :description="toneExampleWarning"
        icon="i-lucide-alert-triangle"
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

      <div v-if="!hasModels" class="flex flex-col items-center justify-center py-16 px-4 text-center border border-dashed border-slate-300 dark:border-slate-800 rounded-3xl">
         <div class="w-20 h-20 bg-emerald-50 dark:bg-emerald-950/30 rounded-full flex items-center justify-center mb-6">
           <UIcon name="i-lucide-sparkles" class="w-10 h-10 text-emerald-500" />
         </div>
         <h3 class="text-xl font-semibold mb-2">还未生成身份模型</h3>
         <p class="text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-8">
           点击下方按钮，我们的 Agent 将根据你填写的画像信息，智能推演出适合你的多维身份模型。
         </p>
         <UButton 
            size="xl" 
            :loading="loading" 
            class="touch-target shadow-lg px-8 font-semibold" 
            color="primary"
            icon="i-lucide-wand-2" 
            @click="generateModels"
          >
            立即生成身份模型
          </UButton>
      </div>

      <div v-else class="grid gap-6 lg:grid-cols-3">
        <UCard
          v-for="model in state.identityModels"
          :key="model.id"
          class="relative flex flex-col group transition-all duration-300"
          :class="{
            'ring-2 ring-primary-500 shadow-xl dark:bg-primary-950/10': selectedPrimaryId === model.id,
            'ring-2 ring-emerald-300/50 shadow-lg': selectedBackupId === model.id,
            'ring-1 ring-slate-200 dark:ring-slate-800 hover:shadow-lg': selectedPrimaryId !== model.id && selectedBackupId !== model.id
          }"
        >
          <template #header>
            <div class="flex items-start justify-between gap-3">
              <h3 class="min-w-0 text-lg font-bold text-slate-900 dark:text-white leading-tight break-words">
                {{ model.title }}
              </h3>
              <div v-if="selectedPrimaryId === model.id" data-testid="identity-card-primary-badge" class="shrink-0">
                <UBadge color="primary" size="lg" class="shadow-lg font-bold px-3 py-1">
                   <UIcon name="i-lucide-star" class="mr-1" /> 主身份
                </UBadge>
              </div>
              <div v-else-if="selectedBackupId === model.id" data-testid="identity-card-backup-badge" class="shrink-0">
                <UBadge color="success" variant="soft" size="lg" class="shadow-md font-bold px-3 py-1 ring-1 ring-emerald-300">
                   <UIcon name="i-lucide-shield-plus" class="mr-1" /> 备身份
                </UBadge>
              </div>
            </div>
          </template>

          <div class="flex-1 space-y-4 text-sm text-slate-600 dark:text-slate-300">
            <div class="bg-slate-50 dark:bg-slate-900/50 p-3 rounded-lg">
              <p class="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1 uppercase tracking-wider">差异化定位</p>
              <p class="font-medium">{{ model.differentiation }}</p>
            </div>
            
            <div>
               <p class="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1 uppercase tracking-wider">目标受众痛点</p>
               <p>{{ model.targetAudiencePain }}</p>
            </div>

            <div>
               <p class="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider">内容支柱 (Pillars)</p>
               <div class="flex flex-wrap gap-2">
                 <UBadge v-for="pillar in model.contentPillars.slice(0,3)" :key="pillar" color="neutral" variant="soft">{{ pillar }}</UBadge>
                 <span v-if="model.contentPillars.length > 3" class="text-xs pt-1">...</span>
               </div>
            </div>

            <div>
              <p class="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider">语气关键词</p>
              <div class="flex flex-wrap gap-2">
                <UBadge
                  v-for="keyword in model.toneStyleKeywords"
                  :key="`${model.id}-${keyword}`"
                  color="primary"
                  variant="soft"
                >
                  {{ keyword }}
                </UBadge>
                <span v-if="model.toneStyleKeywords.length === 0" class="text-xs text-slate-400">未提供</span>
              </div>
            </div>

            <div>
              <p class="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider">语气风格示例</p>
              <ul v-if="getToneExamplePreview(model.toneExamples).length > 0" class="space-y-2 text-xs leading-relaxed">
                <li v-for="example in getToneExamplePreview(model.toneExamples)" :key="`${model.id}-${example}`">
                  “{{ example }}”
                </li>
              </ul>
              <p v-else class="text-xs text-slate-400">暂无示例</p>
            </div>

            <div class="flex items-center gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
              <UIcon name="i-lucide-message-square-quote" class="w-4 h-4 text-slate-400" />
              <p class="text-xs font-medium">
                有效语气示例 <span class="text-emerald-600 dark:text-emerald-400 font-bold">{{ getToneExampleCount(model.toneExamples) }}</span> 条
              </p>
            </div>
          </div>

          <template #footer>
            <div class="grid grid-cols-2 gap-2 mt-auto">
              <UButton
                class="touch-target justify-center font-medium transition-colors"
                :color="selectedPrimaryId === model.id ? 'primary' : 'neutral'"
                :variant="selectedPrimaryId === model.id ? 'solid' : 'outline'"
                :disabled="loading || saving"
                @click="selectedPrimaryId = model.id; if(selectedBackupId === model.id) selectedBackupId = undefined"
              >
                设为主身份
              </UButton>
              <UButton
                class="touch-target justify-center font-medium transition-colors"
                :color="selectedBackupId === model.id ? 'success' : 'neutral'"
                :variant="selectedBackupId === model.id ? 'soft' : 'outline'"
                :disabled="loading || saving"
                @click="selectedBackupId = model.id; if(selectedPrimaryId === model.id) selectedPrimaryId = undefined"
              >
                设为备身份
              </UButton>
            </div>
          </template>
        </UCard>
      </div>

       <div v-if="hasModels" class="mt-6 sm:hidden flex flex-col gap-3 pt-6 border-t border-slate-200 dark:border-slate-800">
           <UButton
            color="neutral"
            variant="outline"
            class="touch-target justify-center"
            size="lg"
            icon="i-lucide-refresh-cw"
            :loading="loading"
            @click="generateModels"
          >
            重新生成
          </UButton>
          <UButton
            color="primary"
            class="touch-target shadow-md font-semibold justify-center"
            size="lg"
            trailing-icon="i-lucide-arrow-right"
            :loading="saving"
            :disabled="loading || saving"
            @click="saveSelection"
          >
            保存选择并继续
          </UButton>
      </div>
    </UCard>
  </div>
</template>
