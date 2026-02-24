<script setup lang="ts">
const config = useRuntimeConfig()
const baseURL = String(config.public.apiBase || 'http://127.0.0.1:8000')
const userId = useStableUserId()
const { state } = useMvpFlow()

const platform = ref('xiaohongshu')
const stageGoal = ref('增长')
const draftText = ref('')
const loading = ref(false)
const errorMessage = ref('')

const evaluate = async () => {
  if (loading.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const result = await $fetch<Record<string, any>>('/v1/simulator/prepublish-evaluations', {
      baseURL,
      method: 'POST',
      body: {
        user_id: userId.value,
        identity_model_id: state.value.selectedPrimaryId,
        draft_text: draftText.value,
        platform: platform.value,
        stage_goal: stageGoal.value,
      },
    })

    state.value.simulatorEvaluations.unshift({
      id: String(result.id),
      growthPredictionRange: String(result.growth_prediction_range || ''),
      controversyProb: Number(result.controversy_prob || 0),
      brandRisk: Number(result.brand_risk || 0),
      trustImpact: Number(result.trust_impact || 0),
      recommendation: String(result.recommendation || ''),
      triggerFactors: Array.isArray(result.trigger_factors) ? result.trigger_factors.map(String) : [],
      rewrite: String(result.rewrite || ''),
      manualConfirmationRequired: Boolean(result.manual_confirmation_required),
    })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '模拟评估失败。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto w-full space-y-6">
    <UCard>
      <template #header>
        <h2 class="text-xl font-bold">发布前模拟器</h2>
      </template>
      <div class="space-y-4">
        <UInput v-model="platform" placeholder="平台" />
        <UInput v-model="stageGoal" placeholder="阶段目标" />
        <UTextarea v-model="draftText" :rows="8" placeholder="粘贴待发布草稿" />
        <UButton :loading="loading" @click="evaluate">开始评估</UButton>
        <UAlert v-if="errorMessage" color="error" :description="errorMessage" />
      </div>
    </UCard>

    <UCard>
      <template #header>
        <h3 class="font-semibold">评估结果</h3>
      </template>
      <div v-if="state.simulatorEvaluations.length === 0" class="text-sm text-slate-500">暂无评估</div>
      <div v-else class="space-y-3">
        <div
          v-for="evaluation in state.simulatorEvaluations"
          :key="evaluation.id"
          class="p-3 rounded-lg border border-slate-200 dark:border-slate-800"
        >
          <p class="font-medium">建议：{{ evaluation.recommendation }}</p>
          <p class="text-xs text-slate-500">增长预测区间：{{ evaluation.growthPredictionRange }}</p>
          <p class="text-xs text-slate-500">风险：争议 {{ evaluation.controversyProb }} / 品牌 {{ evaluation.brandRisk }}</p>
        </div>
      </div>
    </UCard>
  </div>
</template>
