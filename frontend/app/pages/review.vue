<script setup lang="ts">
import { exportDeliveryJsonPackage, type DeliveryPackagePayload } from '../services/export/delivery'

const toast = useToast()
const { state, selectedPrimaryModel, selectedBackupModel, reset } = useMvpFlow()

const hasCoreArtifacts = computed(
  () => Boolean(selectedPrimaryModel.value && state.value.persona && state.value.launchKit && state.value.consistencyCheck)
)

const exportJson = async () => {
  if (!hasCoreArtifacts.value) {
    toast.add({
      title: '导出失败',
      description: '请先完成主流程后再导出。',
      color: 'error',
    })
    return
  }

  const payload: DeliveryPackagePayload = {
    profile: state.value.profile,
    primaryIdentity: selectedPrimaryModel.value,
    backupIdentity: selectedBackupModel.value,
    constitution: state.value.persona,
    launchKit: state.value.launchKit,
    consistencyCheck: state.value.consistencyCheck,
    events: state.value.events,
  }

  try {
    const result = await exportDeliveryJsonPackage(payload)

    if (result.status === 'cancelled') {
      toast.add({
        title: '已取消导出',
        description: '你已取消保存 JSON 交付包。',
        color: 'neutral',
      })
      return
    }

    toast.add({
      title: '导出完成',
      description:
        result.channel === 'tauri'
          ? '交付汇总 JSON 已保存到你选择的位置。'
          : '交付汇总 JSON 已生成并下载。',
      color: 'success',
    })
  } catch (error) {
    toast.add({
      title: '导出失败',
      description: error instanceof Error ? error.message : '导出 JSON 交付包失败，请稍后重试。',
      color: 'error',
    })
  }
}

const startOver = async () => {
  reset()
  await navigateTo('/onboarding')
}
</script>

<template>
  <div class="max-w-5xl mx-auto w-full">
    <UCard class="surface-card ring-1 ring-slate-200 dark:ring-slate-800">
      <template #header>
        <div class="flex items-center gap-4">
          <div class="p-3 bg-fuchsia-50 dark:bg-fuchsia-950/50 rounded-2xl">
            <UIcon name="i-lucide-package-check" class="w-8 h-8 text-fuchsia-500" />
          </div>
          <div class="flex-1">
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">
              最终交付物汇总 (Delivery Review)
            </h2>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              MVP 最小功能核心闭环：包含你的主身份模型、人格宪法约束、7日启动模板及内容一次性检查依据。
            </p>
          </div>
        </div>
      </template>

      <UAlert
        v-if="!hasCoreArtifacts"
        color="warning"
        variant="soft"
        title="环节未闭环"
        description="请先完成从 onboarding 到 launch kit 的所有前置步骤，方可通过一致性检查后导出完整交付物。"
        icon="i-lucide-shield-alert"
        class="mb-6"
      />

      <div class="grid gap-6 lg:grid-cols-2">
        <UCard class="surface-card border border-emerald-100 dark:border-emerald-900/30 bg-emerald-50/10 dark:bg-emerald-950/5">
          <template #header>
             <div class="flex items-center gap-2">
               <UIcon name="i-lucide-users" class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
               <h3 class="text-lg font-bold text-slate-900 dark:text-white">
                设定的身份模型
               </h3>
             </div>
          </template>
          <div class="space-y-4 text-sm text-slate-700 dark:text-slate-300">
            <div class="flex flex-col">
               <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">主身份 (Primary)</span>
               <span class="font-semibold text-lg text-emerald-800 dark:text-emerald-200">{{ selectedPrimaryModel?.title || '未配置' }}</span>
            </div>
             <div class="flex flex-col">
               <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">备选身份 (Backup)</span>
               <span class="font-medium">{{ selectedBackupModel?.title || '未配置' }}</span>
            </div>
            <div class="p-3 bg-white dark:bg-slate-900 rounded-lg ring-1 ring-slate-100 dark:ring-slate-800">
              <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1 block">核心差异化定位</span>
              <span class="leading-relaxed">{{ selectedPrimaryModel?.differentiation || '缺少差异化定位数据' }}</span>
            </div>
          </div>
        </UCard>

        <UCard class="surface-card border border-sky-100 dark:border-sky-900/30 bg-sky-50/10 dark:bg-sky-950/5">
          <template #header>
            <div class="flex items-center gap-2">
               <UIcon name="i-lucide-shield-check" class="w-5 h-5 text-sky-600 dark:text-sky-400" />
               <h3 class="text-lg font-bold text-slate-900 dark:text-white">
                宪法墙与体检分
               </h3>
             </div>
          </template>
          <div class="space-y-4 text-sm text-slate-700 dark:text-slate-300">
             <div class="grid grid-cols-2 gap-4">
                <div class="flex flex-col">
                   <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">不可动摇立场</span>
                   <span class="font-bold text-2xl text-slate-800 dark:text-slate-200">{{ state.persona?.immutablePositions.length || 0 }} <span class="text-sm font-normal text-slate-500">条</span></span>
                </div>
                 <div class="flex flex-col">
                   <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">草稿一致性分</span>
                   <span class="font-bold text-2xl text-sky-600 dark:text-sky-400">{{ state.consistencyCheck?.score ?? '-' }} <span class="text-sm font-normal text-slate-500">分</span></span>
                </div>
             </div>
            
            <div class="p-3 bg-white dark:bg-slate-900 rounded-lg ring-1 ring-slate-100 dark:ring-slate-800 whitespace-pre-wrap">
              <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1 block">近期风险高亮提醒</span>
              <span :class="state.consistencyCheck?.riskWarning ? 'text-rose-600 dark:text-rose-400 font-medium' : 'text-slate-500 italic'">
                {{ state.consistencyCheck?.riskWarning || '良好，暂未发现破除底线的风险。' }}
              </span>
            </div>
          </div>
        </UCard>
      </div>

       <div class="mt-8 flex flex-col sm:flex-row gap-4 pt-6 border-t border-slate-200 dark:border-slate-800">
           <UButton 
            class="touch-target flex-1 justify-center px-8 font-semibold shadow-md" 
            size="lg"
            icon="i-lucide-download"
            color="secondary"
            :disabled="!hasCoreArtifacts" 
            @click="exportJson"
          >
            导出 JSON 交付包
          </UButton>
           <UButton 
            color="neutral" 
            variant="outline" 
            class="touch-target flex-1 justify-center px-8 font-semibold" 
            size="lg"
            icon="i-lucide-rotate-ccw"
            @click="startOver"
          >
            开启新身份探索
          </UButton>
      </div>

      <UCard class="surface-card mt-8 border-none ring-1 ring-slate-200 dark:ring-slate-800 shadow-none">
        <template #header>
           <div class="flex items-center justify-between">
              <h3 class="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                Telemetry 转化节点记录
              </h3>
               <UBadge color="neutral" variant="soft">{{ state.events.length }} 节点</UBadge>
           </div>
        </template>
        <div class="overflow-auto max-h-60 rounded-xl">
          <table class="w-full min-w-[560px] text-left text-sm">
            <thead class="sticky top-0 bg-slate-50 dark:bg-slate-900">
              <tr class="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                <th class="py-3 px-4 font-semibold uppercase text-xs tracking-wider">Event Name</th>
                <th class="py-3 px-4 font-semibold uppercase text-xs tracking-wider">Timestamp</th>
                <th class="py-3 px-4 font-semibold uppercase text-xs tracking-wider">Identity ID</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="event in state.events"
                :key="event.eventName + '_' + event.timestamp"
                class="border-b border-slate-100 dark:border-slate-800/60 text-slate-700 dark:text-slate-300 hover:bg-slate-50/50 dark:hover:bg-slate-900/50 transition-colors"
              >
                <td class="py-3 px-4 font-mono text-xs font-semibold text-fuchsia-600 dark:text-fuchsia-400">{{ event.eventName }}</td>
                <td class="py-3 px-4 font-mono text-xs opacity-70">{{ new Date(event.timestamp).toLocaleString() }}</td>
                <td class="py-3 px-4 font-mono text-xs opacity-70">{{ event.identityId || 'N/A' }}</td>
              </tr>
              <tr v-if="state.events.length === 0">
                <td colspan="3" class="py-8 text-center text-slate-500 italic">暂无追踪事件，需运行后端与埋点记录器以观察变化。</td>
              </tr>
            </tbody>
          </table>
        </div>
      </UCard>
    </UCard>
  </div>
</template>

