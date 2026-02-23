<script setup lang="ts">
import { z } from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import { useApiClient } from '../services/api/client'

const api = useApiClient()
const { track } = useAnalytics()
const { state, selectedPrimaryModel } = useMvpFlow()

const schema = z.object({
  draft: z.string().min(40, '请先输入草稿，再执行一致性检查。'),
})

type Schema = z.output<typeof schema>

const formState = reactive<Schema>({
  draft:
    state.value.draftToCheck ||
    '先说结论：上班族做内容不需要追求花哨表达，先建立每周稳定发布，再逐步优化转化。',
})

const loading = ref(false)
const errorMessage = ref('')

const onSubmit = async (event: FormSubmitEvent<Schema>) => {
  if (!selectedPrimaryModel.value || !state.value.persona) {
    errorMessage.value = '请先完成主身份、人格宪法与启动包。'
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    state.value.draftToCheck = event.data.draft
    const result = await api.runConsistencyCheck({
      draft: event.data.draft,
      identityModel: selectedPrimaryModel.value,
      constitution: state.value.persona,
    })

    state.value.consistencyCheck = result.result
    await track('consistency_check_triggered', selectedPrimaryModel.value.id)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '一致性检查失败。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <UCard class="surface-card">
    <template #header>
      <h2 class="text-xl font-semibold text-slate-900">
        人格一致性检查
      </h2>
      <p class="mt-1 text-sm text-slate-600">
        输出至少包含：偏离项、偏离原因、修改建议；命中风险边界时给出明确提醒。
      </p>
    </template>

    <UAlert
      v-if="errorMessage"
      color="error"
      variant="soft"
      title="检查失败"
      :description="errorMessage"
      class="mb-4"
    />

    <UForm :schema="schema" :state="formState" class="space-y-4" @submit="onSubmit">
      <UFormField label="输入待发布草稿" name="draft">
        <UTextarea v-model="formState.draft" :rows="8" class="touch-target" />
      </UFormField>

      <div class="flex flex-wrap gap-3">
        <UButton type="submit" class="touch-target" :loading="loading">
          执行一致性检查
        </UButton>
        <NuxtLink to="/review">
          <UButton color="neutral" variant="outline" class="touch-target" :disabled="!state.consistencyCheck">
            前往 MVP 汇总
          </UButton>
        </NuxtLink>
      </div>
    </UForm>

    <div v-if="state.consistencyCheck" class="mt-5 space-y-4">
      <UAlert
        v-if="state.consistencyCheck.riskWarning"
        color="warning"
        variant="soft"
        title="风险边界提醒"
        :description="state.consistencyCheck.riskWarning"
      />

      <UCard class="surface-card">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold text-slate-900">
              检查结果
            </h3>
            <UBadge color="primary">
              一致性分数：{{ state.consistencyCheck.score }}
            </UBadge>
          </div>
        </template>

        <div class="grid gap-4 md:grid-cols-3">
          <div>
            <p class="mb-2 text-sm font-semibold text-slate-800">
              偏离项
            </p>
            <ul class="list-disc space-y-1 pl-5 text-sm text-slate-700">
              <li v-for="item in state.consistencyCheck.deviations" :key="item">
                {{ item }}
              </li>
            </ul>
          </div>
          <div>
            <p class="mb-2 text-sm font-semibold text-slate-800">
              偏离原因
            </p>
            <ul class="list-disc space-y-1 pl-5 text-sm text-slate-700">
              <li v-for="item in state.consistencyCheck.reasons" :key="item">
                {{ item }}
              </li>
            </ul>
          </div>
          <div>
            <p class="mb-2 text-sm font-semibold text-slate-800">
              修改建议
            </p>
            <ul class="list-disc space-y-1 pl-5 text-sm text-slate-700">
              <li v-for="item in state.consistencyCheck.suggestions" :key="item">
                {{ item }}
              </li>
            </ul>
          </div>
        </div>
      </UCard>
    </div>
  </UCard>
</template>
