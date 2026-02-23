<script setup lang="ts">
import { useApiClient } from '../services/api/client'

const api = useApiClient()
const { track } = useAnalytics()
const { state, selectedPrimaryModel } = useMvpFlow()

const loading = ref(false)
const errorMessage = ref('')

const generateLaunchKit = async () => {
  if (!selectedPrimaryModel.value || !state.value.persona) {
    errorMessage.value = '请先完成主身份和人格宪法。'
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    const result = await api.generateLaunchKit({
      identityModel: selectedPrimaryModel.value,
      constitution: state.value.persona,
    })
    state.value.launchKit = result.launchKit
    await track('launch_kit_generated', selectedPrimaryModel.value.id)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '启动包生成失败。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <UCard class="surface-card">
    <template #header>
      <h2 class="text-xl font-semibold text-slate-900">
        7-Day Launch Kit
      </h2>
      <p class="mt-1 text-sm text-slate-600">
        自动生成 7 天主题、草稿骨架、可持续栏目与增长实验建议。
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
      <UButton class="touch-target" :loading="loading" @click="generateLaunchKit">
        生成 7 天启动包
      </UButton>
      <NuxtLink to="/consistency-check">
        <UButton
          class="touch-target"
          color="neutral"
          variant="outline"
          :disabled="!state.launchKit"
        >
          进入一致性检查
        </UButton>
      </NuxtLink>
    </div>

    <div v-if="state.launchKit" class="space-y-4">
      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <UCard
          v-for="day in state.launchKit.days"
          :key="day.day"
          class="surface-card"
        >
          <template #header>
            <h3 class="text-base font-semibold text-slate-900">
              Day {{ day.day }}
            </h3>
          </template>
          <div class="space-y-2 text-sm text-slate-700">
            <p><span class="font-semibold">主题：</span>{{ day.theme }}</p>
            <p><span class="font-semibold">草稿大纲：</span>{{ day.draftOutline }}</p>
            <p><span class="font-semibold">开头示例：</span>{{ day.opening }}</p>
          </div>
        </UCard>
      </div>

      <UCard class="surface-card">
        <template #header>
          <h3 class="text-base font-semibold text-slate-900">
            可持续栏目与增长实验
          </h3>
        </template>

        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <p class="mb-2 text-sm font-semibold text-slate-800">
              3 个可持续栏目
            </p>
            <ul class="list-disc space-y-1 pl-5 text-sm text-slate-700">
              <li v-for="column in state.launchKit.sustainableColumns" :key="column">
                {{ column }}
              </li>
            </ul>
          </div>

          <div class="text-sm text-slate-700">
            <p><span class="font-semibold">假设：</span>{{ state.launchKit.growthExperiment.hypothesis }}</p>
            <p class="mt-1">
              <span class="font-semibold">变量：</span>
              {{ state.launchKit.growthExperiment.variables.join(' / ') }}
            </p>
            <p class="mt-1">
              <span class="font-semibold">执行周期：</span>
              {{ state.launchKit.growthExperiment.executionCycle }}
            </p>
            <p class="mt-1">
              <span class="font-semibold">成功指标：</span>
              {{ state.launchKit.growthExperiment.successMetric }}
            </p>
          </div>
        </div>
      </UCard>
    </div>
  </UCard>
</template>
