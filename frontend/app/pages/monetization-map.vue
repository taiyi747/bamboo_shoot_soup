<script setup lang="ts">
import type { MonetizationMap } from '../types/flow'

const config = useRuntimeConfig()
const baseURL = String(config.public.apiBase || 'http://127.0.0.1:8000')
const userId = useStableUserId()
const { state } = useMvpFlow()

const title = ref('12 周变现路线图')
const loading = ref(false)
const errorMessage = ref('')

const fetchList = async () => {
  const list = await $fetch<Array<Record<string, any>>>('/v1/monetization-maps', {
    baseURL,
    params: { user_id: userId.value },
  })
  state.value.monetizationMaps = list.map(item => ({
    id: String(item.id),
    title: String(item.title || ''),
    status: String(item.status || ''),
    weeks: [],
  }))
}

const generateMap = async () => {
  if (loading.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const map = await $fetch<Record<string, any>>('/v1/monetization-maps/generate', {
      baseURL,
      method: 'POST',
      body: {
        user_id: userId.value,
        identity_model_id: state.value.selectedPrimaryId,
        title: title.value,
      },
    })
    state.value.monetizationMaps.unshift({
      id: String(map.id),
      title: String(map.title || ''),
      status: String(map.status || ''),
      weeks: Array.isArray(map.weeks)
        ? map.weeks.map((week: any) => ({
            weekNo: Number(week.week_no || 0),
            objective: String(week.objective || ''),
            expectedOutput: String(week.expected_output || ''),
            validationGoal: String(week.validation_goal || ''),
            status: String(week.status || ''),
          }))
        : [],
    })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '生成变现路线图失败。'
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
        <h2 class="text-xl font-bold">变现路线图</h2>
      </template>
      <div class="space-y-4">
        <UInput v-model="title" placeholder="路线图名称" />
        <UButton :loading="loading" @click="generateMap">生成路线图</UButton>
        <UAlert v-if="errorMessage" color="error" :description="errorMessage" />
      </div>
    </UCard>

    <UCard>
      <template #header>
        <h3 class="font-semibold">路线图列表</h3>
      </template>
      <div v-if="state.monetizationMaps.length === 0" class="text-sm text-slate-500">暂无路线图</div>
      <div v-else class="space-y-2">
        <div
          v-for="map in state.monetizationMaps"
          :key="map.id"
          class="p-3 rounded-lg border border-slate-200 dark:border-slate-800"
        >
          <p class="font-medium">{{ map.title }}</p>
          <p class="text-xs text-slate-500">状态：{{ map.status }} · 周节点：{{ map.weeks.length || 12 }}</p>
        </div>
      </div>
    </UCard>
  </div>
</template>
