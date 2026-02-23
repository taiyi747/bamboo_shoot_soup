<script setup lang="ts">
import { useApiClient } from '../services/api/client'

const api = useApiClient()
const { track } = useAnalytics()
const { state } = useMvpFlow()

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')

const selectedPrimaryId = ref<string | undefined>(state.value.selectedPrimaryId)
const selectedBackupId = ref<string | undefined>(state.value.selectedBackupId)

const generateModels = async () => {
  if (!state.value.profile) {
    errorMessage.value = '请先完成诊断问卷。'
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    const result = await api.generateIdentityModels({ profile: state.value.profile })
    state.value.identityModels = result.models
    await track('identity_models_generated')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '身份模型生成失败。'
  } finally {
    loading.value = false
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
  if (primary.toneExamples.filter(Boolean).length < 5) {
    return '主身份语气示例不足 5 条。'
  }
  return ''
}

const saveSelection = async () => {
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

    await track('identity_selected', selectedPrimaryId.value)
    await navigateTo('/persona-constitution')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '身份选择保存失败。'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UCard class="surface-card">
    <template #header>
      <h2 class="text-xl font-semibold text-slate-900">
        M1 身份模型生成与选择
      </h2>
      <p class="mt-1 text-sm text-slate-600">
        系统将生成 3 个候选身份模型，支持主/备身份选择并做强规则校验。
      </p>
    </template>

    <UAlert
      v-if="errorMessage"
      color="error"
      variant="soft"
      title="操作失败"
      :description="errorMessage"
      class="mb-4"
    />

    <div class="mb-4 flex flex-wrap gap-3">
      <UButton :loading="loading" class="touch-target" @click="generateModels">
        生成 3-5 个身份模型
      </UButton>
      <UButton
        color="neutral"
        variant="outline"
        class="touch-target"
        :disabled="state.identityModels.length === 0"
        @click="saveSelection"
      >
        保存选择并进入人格宪法
      </UButton>
    </div>

    <div class="grid gap-4 lg:grid-cols-3">
      <UCard
        v-for="model in state.identityModels"
        :key="model.id"
        class="surface-card"
      >
        <template #header>
          <div class="flex items-center justify-between gap-2">
            <h3 class="text-base font-semibold text-slate-900">
              {{ model.title }}
            </h3>
            <UBadge v-if="selectedPrimaryId === model.id" color="primary">
              主身份
            </UBadge>
          </div>
        </template>

        <div class="space-y-2 text-sm text-slate-700">
          <p><span class="font-semibold">目标痛点：</span>{{ model.targetAudiencePain }}</p>
          <p><span class="font-semibold">差异化定位：</span>{{ model.differentiation }}</p>
          <p><span class="font-semibold">内容支柱：</span>{{ model.contentPillars.join(' / ') }}</p>
          <p>
            <span class="font-semibold">语气示例条数：</span>{{ model.toneExamples.length }}
          </p>
        </div>

        <template #footer>
          <div class="flex gap-2">
            <UButton
              class="touch-target"
              size="sm"
              :color="selectedPrimaryId === model.id ? 'primary' : 'neutral'"
              :variant="selectedPrimaryId === model.id ? 'solid' : 'outline'"
              @click="selectedPrimaryId = model.id"
            >
              设为主身份
            </UButton>
            <UButton
              class="touch-target"
              size="sm"
              :color="selectedBackupId === model.id ? 'secondary' : 'neutral'"
              :variant="selectedBackupId === model.id ? 'solid' : 'outline'"
              @click="selectedBackupId = model.id"
            >
              设为备身份
            </UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="state.identityModels.length > 0" class="mt-4">
      <UAlert
        color="info"
        variant="soft"
        title="当前选择"
        :description="`主身份：${selectedPrimaryId || '未选择'}；备身份：${selectedBackupId || '未选择'}`"
      />
    </div>
  </UCard>
</template>
