<script setup lang="ts">
const toast = useToast()
const { state, selectedPrimaryModel, selectedBackupModel, reset } = useMvpFlow()

const hasCoreArtifacts = computed(
  () => Boolean(selectedPrimaryModel.value && state.value.persona && state.value.launchKit && state.value.consistencyCheck)
)

const exportJson = () => {
  if (!hasCoreArtifacts.value) {
    toast.add({
      title: '导出失败',
      description: '请先完成主流程后再导出。',
      color: 'error',
    })
    return
  }

  const payload = JSON.stringify(
    {
      stage: state.value.events.at(-1)?.stage ?? 'CURRENT',
      profile: state.value.profile,
      primaryIdentity: selectedPrimaryModel.value,
      backupIdentity: selectedBackupModel.value,
      constitution: state.value.persona,
      launchKit: state.value.launchKit,
      consistencyCheck: state.value.consistencyCheck,
      events: state.value.events,
    },
    null,
    2
  )

  const blob = new Blob([payload], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `bss-identity-review-${Date.now()}.json`
  link.click()
  URL.revokeObjectURL(url)

  toast.add({
    title: '导出完成',
    description: '交付汇总 JSON 已生成。',
    color: 'success',
  })
}

const startOver = async () => {
  reset()
  await navigateTo('/onboarding')
}
</script>

<template>
  <UCard class="surface-card">
    <template #header>
      <h2 class="text-xl font-semibold text-slate-900">
        交付汇总预览
      </h2>
      <p class="mt-1 text-sm text-slate-600">
        对齐 product-spec 最小交付：主身份模型 + 人格宪法 + 7-Day Launch Kit + 风险边界提醒。
      </p>
    </template>

    <UAlert
      v-if="!hasCoreArtifacts"
      color="warning"
      variant="soft"
      title="交付尚未完成"
      description="请先完成前置步骤，系统会自动汇总核心产物。"
      class="mb-4"
    />

    <div class="mb-4 flex flex-wrap gap-3">
      <UButton class="touch-target" :disabled="!hasCoreArtifacts" @click="exportJson">
        导出交付汇总 JSON
      </UButton>
      <UButton color="neutral" variant="outline" class="touch-target" @click="startOver">
        重新开始流程
      </UButton>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <UCard class="surface-card">
        <template #header>
          <h3 class="text-base font-semibold text-slate-900">
            主/备身份
          </h3>
        </template>
        <div class="space-y-2 text-sm text-slate-700">
          <p><span class="font-semibold">主身份：</span>{{ selectedPrimaryModel?.title || '未完成' }}</p>
          <p><span class="font-semibold">备身份：</span>{{ selectedBackupModel?.title || '未完成' }}</p>
          <p>
            <span class="font-semibold">差异化定位：</span>
            {{ selectedPrimaryModel?.differentiation || '未完成' }}
          </p>
        </div>
      </UCard>

      <UCard class="surface-card">
        <template #header>
          <h3 class="text-base font-semibold text-slate-900">
            人格宪法与一致性结果
          </h3>
        </template>
        <div class="space-y-2 text-sm text-slate-700">
          <p>
            <span class="font-semibold">不可动摇立场：</span>
            {{ state.persona?.immutablePositions.length || 0 }} 条
          </p>
          <p>
            <span class="font-semibold">一致性分数：</span>
            {{ state.consistencyCheck?.score ?? '未检查' }}
          </p>
          <p>
            <span class="font-semibold">风险提醒：</span>
            {{ state.consistencyCheck?.riskWarning || '未触发' }}
          </p>
        </div>
      </UCard>
    </div>

    <UCard class="surface-card mt-4">
      <template #header>
        <h3 class="text-base font-semibold text-slate-900">
          事件埋点
        </h3>
      </template>
      <div class="overflow-auto">
        <table class="w-full min-w-[560px] text-left text-sm">
          <thead>
            <tr class="border-b border-slate-200 text-slate-600">
              <th class="py-2">事件名</th>
              <th class="py-2">阶段</th>
              <th class="py-2">时间</th>
              <th class="py-2">身份 ID</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="event in state.events"
              :key="`${event.eventName}_${event.timestamp}`"
              class="border-b border-slate-100 text-slate-700"
            >
              <td class="py-2">{{ event.eventName }}</td>
              <td class="py-2">{{ event.stage }}</td>
              <td class="py-2">{{ event.timestamp }}</td>
              <td class="py-2">{{ event.identityId || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </UCard>
  </UCard>
</template>
