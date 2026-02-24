<script setup lang="ts">
import { useApiClient } from '../services/api/client'
import { generationFeedbackCopy } from '../constants/generation-feedback'

const api = useApiClient()
const { track } = useAnalytics()
const { state, selectedPrimaryModel } = useMvpFlow()

const loading = ref(false)
const errorMessage = ref('')
const feedbackMeta = { ui_feedback_variant: 'card_skeleton' }
const feedbackCopy = generationFeedbackCopy.launchKit
const {
  currentHint: currentLoadingHint,
  start: startLoadingFeedback,
  stop: stopLoadingFeedback,
  reset: resetLoadingFeedback,
} = useLoadingFeedback(feedbackCopy.hints)

const generateLaunchKit = async () => {
  if (loading.value) {
    return
  }

  if (!selectedPrimaryModel.value || !state.value.persona) {
    errorMessage.value = '请先完成主身份和人格宪法。'
    return
  }

  const startedAt = Date.now()
  loading.value = true
  errorMessage.value = ''
  resetLoadingFeedback()
  startLoadingFeedback()
  try {
    const result = await api.generateLaunchKit({
      identityModel: selectedPrimaryModel.value,
      constitution: state.value.persona,
    })
    state.value.launchKit = result.launchKit
    await track('launch_kit_generated', selectedPrimaryModel.value.id, {
      ...feedbackMeta,
      loading_duration_ms: Date.now() - startedAt,
    })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '启动包生成失败。'
  } finally {
    loading.value = false
    stopLoadingFeedback()
    resetLoadingFeedback()
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto w-full">
    <UCard class="surface-card ring-1 ring-slate-200 dark:ring-slate-800">
      <template #header>
        <div class="flex items-center gap-4">
          <div class="p-3 bg-indigo-50 dark:bg-indigo-950/50 rounded-2xl">
            <UIcon name="i-lucide-rocket" class="w-8 h-8 text-indigo-500 dark:text-indigo-400" />
          </div>
          <div class="flex-1">
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">
              7-Day Launch Kit
            </h2>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              结合主身份与人格宪法，自动生成 7 天初始发文主题、草稿骨架、可持续栏目与增长实验建议。
            </p>
          </div>
          
          <div v-if="state.launchKit" class="hidden sm:flex items-center gap-3">
            <UButton 
              class="touch-target font-medium shadow-sm" 
              color="neutral" 
              variant="outline" 
              icon="i-lucide-refresh-cw"
              :loading="loading" 
              @click="generateLaunchKit"
            >
              重新生成
            </UButton>
            <NuxtLink to="/consistency-check">
              <UButton 
                color="primary" 
                class="touch-target font-semibold shadow-md" 
                trailing-icon="i-lucide-arrow-right"
                :disabled="loading"
              >
                进行一致性检查
              </UButton>
            </NuxtLink>
          </div>
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

      <GenerationFeedbackCard
        v-if="loading"
        :title="feedbackCopy.title"
        :description="feedbackCopy.description"
        :hint="currentLoadingHint"
        :icon="feedbackCopy.icon"
        :color="feedbackCopy.color"
      />

       <div v-if="!state.launchKit && !loading" class="flex flex-col items-center justify-center py-16 px-4 text-center border border-dashed border-slate-300 dark:border-slate-800 rounded-3xl">
         <div class="w-20 h-20 bg-indigo-50 dark:bg-indigo-950/30 rounded-full flex items-center justify-center mb-6">
           <UIcon name="i-lucide-rocket" class="w-10 h-10 text-indigo-500" />
         </div>
         <h3 class="text-xl font-semibold mb-2">准备起飞</h3>
         <p class="text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-8">
           所有身份要素已就绪。点击下方按钮，Agent 将为你生成冷启动的七天发文包与实验策略。
         </p>
         <UButton 
            size="xl" 
            :loading="loading" 
            class="touch-target shadow-lg px-8 font-semibold" 
            color="primary"
            icon="i-lucide-sparkles" 
            @click="generateLaunchKit"
          >
            一键生成 7 天启动包
          </UButton>
      </div>

      <div v-else-if="state.launchKit" class="space-y-8">
        <div>
          <div class="flex items-center gap-2 mb-4">
             <UIcon name="i-lucide-calendar-days" class="w-5 h-5 text-slate-700 dark:text-slate-300" />
             <h3 class="text-lg font-bold text-slate-900 dark:text-white">首周内容排期 (Day 1-7)</h3>
          </div>
          <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <UCard
              v-for="day in state.launchKit.days"
              :key="day.day"
              class="surface-card ring-1 ring-slate-100 dark:ring-slate-800/60 hover:shadow-md transition-shadow relative overflow-hidden group"
            >
              <div class="absolute top-0 right-0 w-24 h-24 bg-indigo-50 dark:bg-indigo-900/10 rounded-bl-full -z-10 group-hover:bg-indigo-100 dark:group-hover:bg-indigo-900/20 transition-colors"></div>
              <template #header>
                <div class="flex items-center justify-between">
                   <h4 class="text-2xl font-black text-indigo-950/20 dark:text-indigo-100/10 tracking-widest">
                    D{{ day.day }}
                  </h4>
                   <UBadge color="primary" variant="soft" class="font-semibold uppercase tracking-wider">Day {{ day.day }}</UBadge>
                </div>
              </template>
              <div class="space-y-4 text-sm text-slate-600 dark:text-slate-300">
                <div>
                   <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">核心主题</p>
                   <p class="font-semibold text-slate-800 dark:text-slate-200 text-base leading-tight">{{ day.theme }}</p>
                </div>
                
                <div class="bg-slate-50 dark:bg-slate-900/50 p-3 rounded-lg border border-slate-100 dark:border-slate-800">
                   <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">草稿大纲</p>
                   <p class="leading-relaxed">{{ day.draftOutline }}</p>
                </div>
                <div>
                  <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">开头破冰示例</p>
                  <div class="flex gap-2 text-indigo-700 dark:text-indigo-400 italic">
                   <UIcon name="i-lucide-quote" class="w-4 h-4 flex-shrink-0 mt-0.5 opacity-50" />
                   <p>{{ day.opening }}</p>
                  </div>
                </div>
              </div>
            </UCard>
          </div>
        </div>

        <div class="grid gap-6 md:grid-cols-2 pt-6 border-t border-slate-100 dark:border-slate-800">
           <UCard class="surface-card border border-emerald-100 dark:border-emerald-900/30 bg-emerald-50/30 dark:bg-emerald-950/10">
            <template #header>
               <div class="flex items-center gap-2">
                  <div class="p-2 bg-emerald-100 dark:bg-emerald-900/50 rounded-lg">
                     <UIcon name="i-lucide-layout-template" class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <h3 class="text-lg font-bold text-slate-900 dark:text-white">三个可持续栏目</h3>
               </div>
            </template>
            <ul class="space-y-3">
               <li v-for="(column, index) in state.launchKit.sustainableColumns" :key="column" class="flex items-start gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl shadow-sm ring-1 ring-emerald-500/10">
                  <div class="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-xs font-bold">
                     {{ index + 1 }}
                  </div>
                  <span class="text-sm font-medium text-slate-700 dark:text-slate-300 pt-0.5">{{ column }}</span>
               </li>
            </ul>
           </UCard>

           <UCard class="surface-card border border-amber-100 dark:border-amber-900/30 bg-amber-50/30 dark:bg-amber-950/10">
            <template #header>
              <div class="flex items-center gap-2">
                  <div class="p-2 bg-amber-100 dark:bg-amber-900/50 rounded-lg">
                     <UIcon name="i-lucide-microscope" class="w-5 h-5 text-amber-600 dark:text-amber-500" />
                  </div>
                  <h3 class="text-lg font-bold text-slate-900 dark:text-white">早期增长实验建议</h3>
               </div>
            </template>
            <div class="space-y-4 text-sm">
               <div class="bg-white dark:bg-slate-900 p-4 rounded-xl shadow-sm ring-1 ring-amber-500/10">
                 <p class="text-xs font-bold text-amber-600/70 dark:text-amber-500/70 uppercase tracking-wider mb-1">核心假设</p>
                 <p class="font-semibold text-slate-800 dark:text-slate-200">{{ state.launchKit.growthExperiment.hypothesis }}</p>
               </div>
               
               <div class="grid grid-cols-2 gap-3">
                 <div class="bg-white dark:bg-slate-900 p-3 rounded-lg shadow-sm ring-1 ring-amber-500/10">
                   <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">测试变量</p>
                   <p class="font-medium text-slate-700 dark:text-slate-300">{{ state.launchKit.growthExperiment.variables.join(' / ') }}</p>
                 </div>
                 <div class="bg-white dark:bg-slate-900 p-3 rounded-lg shadow-sm ring-1 ring-amber-500/10">
                   <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">执行周期</p>
                   <p class="font-medium text-slate-700 dark:text-slate-300">{{ state.launchKit.growthExperiment.executionCycle }}</p>
                 </div>
                   <div class="col-span-2 bg-white dark:bg-slate-900 p-3 rounded-lg shadow-sm ring-1 ring-amber-500/10">
                   <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">判定成功的指标</p>
                   <p class="font-medium text-amber-700 dark:text-amber-500">{{ state.launchKit.growthExperiment.successMetric }}</p>
                 </div>
               </div>
            </div>
           </UCard>
        </div>
      </div>
      
       <div v-if="state.launchKit || loading" class="mt-8 sm:hidden flex flex-col gap-3 pt-6 border-t border-slate-200 dark:border-slate-800">
           <UButton 
              class="touch-target justify-center font-medium shadow-sm" 
              color="neutral" 
              variant="outline" 
              icon="i-lucide-refresh-cw"
              size="lg"
              :loading="loading" 
              @click="generateLaunchKit"
            >
              重新生成
            </UButton>
            <NuxtLink to="/consistency-check" class="w-full block">
              <UButton 
                color="primary" 
                class="touch-target justify-center font-semibold shadow-md w-full" 
                size="lg"
                trailing-icon="i-lucide-arrow-right"
                :disabled="loading"
              >
                继续
              </UButton>
            </NuxtLink>
      </div>
    </UCard>
  </div>
</template>
