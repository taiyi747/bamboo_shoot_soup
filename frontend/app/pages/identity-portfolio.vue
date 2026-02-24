<script setup lang="ts">
const config = useRuntimeConfig()
const baseURL = String(config.public.apiBase || 'http://127.0.0.1:8000')
const userId = useStableUserId()
const { state } = useMvpFlow()

const anonymousIdentity = ref('匿名行业观察者')
const toolIdentity = ref('方法论工具号')
const loading = ref(false)
const errorMessage = ref('')

const fetchList = async () => {
  const list = await $fetch<Array<Record<string, any>>>('/v1/identity-portfolios', {
    baseURL,
    params: { user_id: userId.value },
  })
  state.value.identityPortfolios = list.map(item => ({
    id: String(item.id),
    primaryIdentityId: String(item.primary_identity_id),
    backupIdentityId: item.backup_identity_id ? String(item.backup_identity_id) : undefined,
    anonymousIdentity: String(item.anonymous_identity || ''),
    toolIdentity: String(item.tool_identity || ''),
    conflictAvoidance: String(item.conflict_avoidance || ''),
    assetReuseStrategy: String(item.asset_reuse_strategy || ''),
  }))
}

const generatePortfolio = async () => {
  if (loading.value) return
  if (!state.value.selectedPrimaryId) {
    errorMessage.value = '请先完成主身份选择。'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    await $fetch('/v1/identity-portfolios/generate', {
      baseURL,
      method: 'POST',
      body: {
        user_id: userId.value,
        primary_identity_id: state.value.selectedPrimaryId,
        backup_identity_id: state.value.selectedBackupId,
        anonymous_identity: anonymousIdentity.value,
        tool_identity: toolIdentity.value,
      },
    })
    await fetchList()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '生成身份组合失败。'
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
        <h2 class="text-xl font-bold">身份组合策略</h2>
      </template>
      <div class="space-y-4">
        <UInput v-model="anonymousIdentity" placeholder="匿名身份" />
        <UInput v-model="toolIdentity" placeholder="工具身份" />
        <UButton :loading="loading" @click="generatePortfolio">生成身份组合</UButton>
        <UAlert v-if="errorMessage" color="error" :description="errorMessage" />
      </div>
    </UCard>

    <UCard>
      <template #header>
        <h3 class="font-semibold">组合列表</h3>
      </template>
      <div v-if="state.identityPortfolios.length === 0" class="text-sm text-slate-500">暂无组合</div>
      <div v-else class="space-y-3">
        <div
          v-for="portfolio in state.identityPortfolios"
          :key="portfolio.id"
          class="p-3 rounded-lg border border-slate-200 dark:border-slate-800"
        >
          <p class="text-sm font-semibold">主身份：{{ portfolio.primaryIdentityId }}</p>
          <p class="text-xs text-slate-500 mt-1">{{ portfolio.conflictAvoidance }}</p>
        </div>
      </div>
    </UCard>
  </div>
</template>
