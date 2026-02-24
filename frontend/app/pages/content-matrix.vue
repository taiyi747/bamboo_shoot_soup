<script setup lang="ts">
import type { ContentMatrix } from '../types/flow'

const config = useRuntimeConfig()
const baseURL = String(config.public.apiBase || 'http://127.0.0.1:8000')
const userId = useStableUserId()
const { state } = useMvpFlow()

const loading = ref(false)
const errorMessage = ref('')
const pillarsText = ref('职业洞察,工具方法,案例拆解')
const platformsText = ref('xiaohongshu,twitter')
const formatsText = ref('post,thread')

const fetchList = async () => {
  const list = await $fetch<Array<Record<string, any>>>('/v1/content-matrixes', {
    baseURL,
    params: { user_id: userId.value },
  })
  state.value.contentMatrixes = list.map(item => ({
    id: String(item.id),
    pillar: String(item.pillar || ''),
    platform: String(item.platform || ''),
    format: String(item.format || ''),
    status: String(item.status || ''),
    topics: [],
  }))
}

const generate = async () => {
  if (loading.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    await $fetch('/v1/content-matrixes/generate', {
      baseURL,
      method: 'POST',
      body: {
        user_id: userId.value,
        identity_model_id: state.value.selectedPrimaryId,
        pillars: pillarsText.value.split(',').map(v => v.trim()).filter(Boolean),
        platforms: platformsText.value.split(',').map(v => v.trim()).filter(Boolean),
        formats: formatsText.value.split(',').map(v => v.trim()).filter(Boolean),
        count_per_pillar: 20,
      },
    })
    await fetchList()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '内容矩阵生成失败。'
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
        <h2 class="text-xl font-bold">内容矩阵</h2>
      </template>
      <div class="space-y-4">
        <UInput v-model="pillarsText" placeholder="支柱，逗号分隔" />
        <UInput v-model="platformsText" placeholder="平台，逗号分隔" />
        <UInput v-model="formatsText" placeholder="格式，逗号分隔" />
        <UButton :loading="loading" @click="generate">生成内容矩阵</UButton>
        <UAlert v-if="errorMessage" color="error" :description="errorMessage" />
      </div>
    </UCard>

    <UCard>
      <template #header>
        <h3 class="font-semibold">已生成矩阵</h3>
      </template>
      <div v-if="state.contentMatrixes.length === 0" class="text-sm text-slate-500">暂无数据</div>
      <div v-else class="space-y-2">
        <div
          v-for="matrix in state.contentMatrixes"
          :key="matrix.id"
          class="p-3 rounded-lg border border-slate-200 dark:border-slate-800"
        >
          <p class="font-medium">{{ matrix.pillar }} · {{ matrix.platform }} · {{ matrix.format }}</p>
          <p class="text-xs text-slate-500">状态：{{ matrix.status }}</p>
        </div>
      </div>
    </UCard>
  </div>
</template>
