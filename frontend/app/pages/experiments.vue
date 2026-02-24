<script setup lang="ts">
import type { GrowthExperimentRecord } from '../types/flow'

const config = useRuntimeConfig()
const baseURL = String(config.public.apiBase || 'http://127.0.0.1:8000')
const userId = useStableUserId()
const { state } = useMvpFlow()

const loading = ref(false)
const errorMessage = ref('')
const hypothesis = ref('')
const variablesText = ref('')
const duration = ref('7d')

const fetchList = async () => {
  const list = await $fetch<Array<Record<string, any>>>('/v1/experiments', {
    baseURL,
    params: { user_id: userId.value },
  })
  state.value.experiments = list.map(item => ({
    id: String(item.id),
    hypothesis: String(item.hypothesis || ''),
    variables: Array.isArray(item.variables) ? item.variables.map(String) : [],
    duration: String(item.duration || ''),
    result: String(item.result || ''),
    conclusion: String(item.conclusion || ''),
    nextIteration: String(item.next_iteration || ''),
    status: String(item.status || ''),
  }))
}

const createExperiment = async () => {
  if (loading.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    await $fetch('/v1/experiments', {
      baseURL,
      method: 'POST',
      body: {
        user_id: userId.value,
        identity_model_id: state.value.selectedPrimaryId,
        hypothesis: hypothesis.value,
        variables: variablesText.value.split(',').map(v => v.trim()).filter(Boolean),
        duration: duration.value,
      },
    })
    hypothesis.value = ''
    variablesText.value = ''
    await fetchList()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '实验创建失败。'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchList()
})
</script>

<template>
  <div class="max-w-5xl mx-auto w-full space-y-6">
    <UCard>
      <template #header>
        <h2 class="text-xl font-bold">增长实验</h2>
      </template>
      <div class="space-y-4">
        <UInput v-model="hypothesis" placeholder="实验假设" />
        <UInput v-model="variablesText" placeholder="变量，逗号分隔" />
        <UInput v-model="duration" placeholder="执行周期" />
        <UButton :loading="loading" @click="createExperiment">创建实验</UButton>
        <UAlert v-if="errorMessage" color="error" :description="errorMessage" />
      </div>
    </UCard>

    <UCard>
      <template #header>
        <h3 class="font-semibold">实验列表</h3>
      </template>
      <div v-if="state.experiments.length === 0" class="text-sm text-slate-500">暂无实验</div>
      <div v-else class="space-y-2">
        <div
          v-for="exp in state.experiments"
          :key="exp.id"
          class="p-3 rounded-lg border border-slate-200 dark:border-slate-800"
        >
          <p class="font-medium">{{ exp.hypothesis }}</p>
          <p class="text-xs text-slate-500">状态：{{ exp.status }} · 周期：{{ exp.duration }}</p>
        </div>
      </div>
    </UCard>
  </div>
</template>
