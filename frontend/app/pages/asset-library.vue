<script setup lang="ts">
const config = useRuntimeConfig()
const baseURL = String(config.public.apiBase || 'http://127.0.0.1:8000')
const userId = useStableUserId()
const { state } = useMvpFlow()

const topic = ref('AI 提效')
const platform = ref('all')
const sourceText = ref('')
const query = ref('')
const loading = ref(false)
const errorMessage = ref('')

const searchAssets = async () => {
  const list = await $fetch<Array<Record<string, any>>>('/v1/viewpoint-assets/search', {
    baseURL,
    params: {
      user_id: userId.value,
      query: query.value || undefined,
      identity_model_id: state.value.selectedPrimaryId || undefined,
      platform: platform.value === 'all' ? undefined : platform.value,
    },
  })
  state.value.viewpointAssets = list.map(item => ({
    id: String(item.id),
    topic: String(item.topic || ''),
    platform: String(item.platform || ''),
    stance: String(item.stance || ''),
    summary: String(item.summary || ''),
    tags: Array.isArray(item.tags) ? item.tags.map(String) : [],
  }))
}

const extractAssets = async () => {
  if (loading.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    await $fetch('/v1/viewpoint-assets/extract', {
      baseURL,
      method: 'POST',
      body: {
        user_id: userId.value,
        identity_model_id: state.value.selectedPrimaryId,
        topic: topic.value,
        platform: platform.value,
        source_contents: sourceText.value
          ? sourceText.value.split('\n').map(v => v.trim()).filter(Boolean)
          : [],
      },
    })
    await searchAssets()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '资产提炼失败。'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await searchAssets()
})
</script>

<template>
  <div class="max-w-5xl mx-auto w-full space-y-6">
    <UCard>
      <template #header>
        <h2 class="text-xl font-bold">观点资产库</h2>
      </template>
      <div class="space-y-4">
        <UInput v-model="topic" placeholder="主题" />
        <UInput v-model="platform" placeholder="平台" />
        <UTextarea v-model="sourceText" :rows="6" placeholder="每行一条历史内容样本" />
        <div class="flex gap-3">
          <UButton :loading="loading" @click="extractAssets">提炼资产</UButton>
          <UButton color="neutral" variant="outline" @click="searchAssets">检索资产</UButton>
        </div>
        <UAlert v-if="errorMessage" color="error" :description="errorMessage" />
      </div>
    </UCard>

    <UCard>
      <template #header>
        <div class="flex gap-3 items-center">
          <h3 class="font-semibold">资产列表</h3>
          <UInput v-model="query" class="max-w-sm" placeholder="按主题或摘要搜索" @keyup.enter="searchAssets" />
        </div>
      </template>
      <div v-if="state.viewpointAssets.length === 0" class="text-sm text-slate-500">暂无资产</div>
      <div v-else class="space-y-2">
        <div
          v-for="asset in state.viewpointAssets"
          :key="asset.id"
          class="p-3 rounded-lg border border-slate-200 dark:border-slate-800"
        >
          <p class="font-medium">{{ asset.topic }} · {{ asset.platform }}</p>
          <p class="text-sm mt-1">{{ asset.summary }}</p>
          <p class="text-xs text-slate-500 mt-1">{{ asset.tags.join(' / ') }}</p>
        </div>
      </div>
    </UCard>
  </div>
</template>
