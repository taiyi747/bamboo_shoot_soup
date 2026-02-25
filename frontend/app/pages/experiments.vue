<script setup lang="ts">
import { z } from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import { useApiClient } from '../services/api/client'

const api = useApiClient()
const { track } = useAnalytics()
const { state, selectedPrimaryModel } = useMvpFlow()

const createSchema = z.object({
  hypothesis: z.string().min(6, '请填写实验假设'),
  variables: z.string().min(3, '请至少填写一个变量'),
  executionCycle: z.string().min(2, '请填写执行周期'),
})

type CreateSchema = z.output<typeof createSchema>

const createForm = reactive<CreateSchema>({
  hypothesis: '更具体的标题提升收藏率',
  variables: '标题,开头钩子',
  executionCycle: '7d',
})

const resultForm = reactive<Record<string, { result: string; conclusion: string }>>({})
const loading = ref(false)
const errorMessage = ref('')

const splitVariables = (value: string): string[] =>
  value
    .split(/[\n,，]/g)
    .map(item => item.trim())
    .filter(Boolean)

const refreshExperiments = async () => {
  const listed = await api.getExperiments()
  state.value.experiments = listed.experiments
}

watch(
  () => state.value.experiments,
  (experiments) => {
    for (const item of experiments) {
      if (!resultForm[item.id]) {
        resultForm[item.id] = {
          result: item.result || '',
          conclusion: item.conclusion || '',
        }
      }
    }
  },
  { immediate: true, deep: true }
)

const createExperiment = async (event: FormSubmitEvent<CreateSchema>) => {
  if (loading.value) {
    return
  }
  if (!selectedPrimaryModel.value) {
    errorMessage.value = '请先完成主身份选择。'
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    await api.createExperiment({
      identityModel: selectedPrimaryModel.value,
      hypothesis: event.data.hypothesis,
      variables: splitVariables(event.data.variables),
      executionCycle: event.data.executionCycle,
    })
    await refreshExperiments()
    await track('experiment_created', selectedPrimaryModel.value.id, {
      experiments_count: state.value.experiments.length,
    })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '创建实验失败。'
  } finally {
    loading.value = false
  }
}

const saveExperimentResult = async (experimentId: string) => {
  const form = resultForm[experimentId]
  if (!form?.result?.trim() || !form?.conclusion?.trim()) {
    errorMessage.value = '请填写结果与结论后再保存。'
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    await api.updateExperimentResult({
      experimentId,
      result: form.result,
      conclusion: form.conclusion,
    })
    await refreshExperiments()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新实验结果失败。'
  } finally {
    loading.value = false
  }
}

const goNext = async () => {
  if (state.value.experiments.length === 0) {
    errorMessage.value = '请至少创建一个实验后再继续。'
    return
  }
  await navigateTo('/monetization-map')
}

onMounted(async () => {
  if (state.value.experiments.length === 0) {
    try {
      await refreshExperiments()
    } catch {
      // ignore initial load failure and let user retry
    }
  }
})
</script>

<template>
  <div class="max-w-6xl mx-auto w-full">
    <UCard class="surface-card ring-1 ring-slate-200 dark:ring-slate-800">
      <template #header>
        <div class="flex items-center gap-4">
          <div class="p-3 bg-amber-50 dark:bg-amber-950/50 rounded-2xl">
            <UIcon name="i-lucide-flask-conical" class="w-8 h-8 text-amber-500" />
          </div>
          <div class="flex-1">
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">增长实验面板</h2>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              管理假设-变量-执行周期-结果-结论，避免无结论实验进入下一轮。
            </p>
          </div>
          <UButton
            color="primary"
            class="hidden sm:inline-flex touch-target font-semibold shadow-md"
            trailing-icon="i-lucide-arrow-right"
            :disabled="loading || state.experiments.length === 0"
            @click="goNext"
          >
            继续到变现路线图
          </UButton>
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

      <UCard class="surface-card border border-slate-200 dark:border-slate-800 mb-6">
        <template #header>
          <h3 class="font-semibold text-slate-900 dark:text-white">创建新实验</h3>
        </template>

        <UForm :schema="createSchema" :state="createForm" class="space-y-4" @submit="createExperiment">
          <UFormField label="假设" name="hypothesis" class="w-full">
            <UInput v-model="createForm.hypothesis" class="w-full touch-target" />
          </UFormField>
          <UFormField label="变量" name="variables" class="w-full">
            <UInput v-model="createForm.variables" class="w-full touch-target" />
          </UFormField>
          <UFormField label="执行周期" name="executionCycle" class="w-full">
            <UInput v-model="createForm.executionCycle" class="w-full touch-target" />
          </UFormField>
          <UButton type="submit" :loading="loading" class="touch-target" icon="i-lucide-plus">
            创建实验
          </UButton>
        </UForm>
      </UCard>

      <div class="space-y-4">
        <UCard
          v-for="experiment in state.experiments"
          :key="experiment.id"
          class="surface-card border border-slate-200 dark:border-slate-800"
        >
          <template #header>
            <div class="flex items-center justify-between gap-3">
              <h3 class="font-semibold text-slate-900 dark:text-white">{{ experiment.hypothesis }}</h3>
              <UBadge :color="experiment.status === 'completed' ? 'success' : 'warning'" variant="soft">
                {{ experiment.status === 'completed' ? '已完成' : '待验证' }}
              </UBadge>
            </div>
          </template>

          <div class="space-y-3 text-sm text-slate-600 dark:text-slate-300">
            <p>变量：{{ experiment.variables.join(' / ') }}</p>
            <p>执行周期：{{ experiment.executionCycle }}</p>
          </div>

          <div class="mt-4 grid gap-3 md:grid-cols-2">
            <UTextarea
              v-model="resultForm[experiment.id].result"
              :rows="3"
              class="w-full"
              placeholder="填写实验结果"
            />
            <UTextarea
              v-model="resultForm[experiment.id].conclusion"
              :rows="3"
              class="w-full"
              placeholder="填写实验结论"
            />
          </div>

          <template #footer>
            <UButton
              color="neutral"
              variant="outline"
              class="touch-target"
              :loading="loading"
              @click="saveExperimentResult(experiment.id)"
            >
              保存结果与结论
            </UButton>
          </template>
        </UCard>

        <UAlert
          v-if="state.experiments.length === 0"
          color="warning"
          variant="soft"
          title="暂无实验"
          description="请先创建至少一个实验。"
        />
      </div>

      <div class="mt-8 sm:hidden flex flex-col gap-3 pt-6 border-t border-slate-200 dark:border-slate-800">
        <UButton
          color="primary"
          class="touch-target justify-center font-semibold"
          trailing-icon="i-lucide-arrow-right"
          :disabled="loading || state.experiments.length === 0"
          @click="goNext"
        >
          继续
        </UButton>
      </div>
    </UCard>
  </div>
</template>
