<script setup lang="ts">
import { z } from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import { useApiClient } from '../services/api/client'
import type { OnboardingInput } from '../types/flow'

const api = useApiClient()
const { track } = useAnalytics()
const { state, reset } = useMvpFlow()

const schema = z.object({
  skills: z.string().min(3, '请至少填写 1 项技能'),
  interests: z.string().min(3, '请至少填写 1 项可持续兴趣'),
  cognitiveStyle: z.string().min(4, '请描述你的认知风格'),
  valueBoundaries: z.string().min(4, '请填写你的价值边界'),
  riskTolerance: z.enum(['low', 'medium', 'high']),
  weeklyHours: z.coerce.number().int().min(2).max(40),
  goals: z.string().min(3, '请填写阶段目标'),
})

type Schema = z.output<typeof schema>

const formState = reactive<Schema>({
  skills: '行业分析, 项目管理, 写作表达',
  interests: '职场策略, 方法沉淀, 案例复盘',
  cognitiveStyle: '结构化拆解 + 可执行清单',
  valueBoundaries: '不制造焦虑，不承诺短期暴富，不做无证据断言',
  riskTolerance: 'medium',
  weeklyHours: 8,
  goals: '建立稳定内容输出并验证咨询线索',
})

const loading = ref(false)
const errorMessage = ref('')

const splitList = (value: string) =>
  value
    .split(/[\n,，]/g)
    .map(item => item.trim())
    .filter(Boolean)

const toInput = (data: Schema): OnboardingInput => ({
  skills: splitList(data.skills),
  interests: splitList(data.interests),
  cognitiveStyle: data.cognitiveStyle.trim(),
  valueBoundaries: splitList(data.valueBoundaries),
  riskTolerance: data.riskTolerance,
  weeklyHours: data.weeklyHours,
  goals: splitList(data.goals),
})

const onSubmit = async (event: FormSubmitEvent<Schema>) => {
  loading.value = true
  errorMessage.value = ''

  try {
    const input = toInput(event.data)
    reset()
    state.value.onboardingInput = input

    await track('onboarding_started')
    const session = await api.createOnboardingSession({
      targetPersona: 'career_creator',
      goals: input.goals,
    })
    const profile = await api.completeOnboarding({
      sessionId: session.sessionId,
      input,
    })

    state.value.sessionId = session.sessionId
    state.value.profile = profile.profile

    await track('onboarding_completed')
    await navigateTo('/identity-models')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '诊断生成失败，请重试。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto w-full">
    <UCard class="surface-card ring-1 ring-slate-200 dark:ring-slate-800">
      <template #header>
        <div class="flex items-center gap-4">
          <div class="p-3 bg-primary-50 dark:bg-primary-950 rounded-2xl">
            <UIcon name="i-lucide-clipboard-check" class="w-8 h-8 text-primary-500" />
          </div>
          <div>
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">
              身份诊断
            </h2>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              我们将通过六个维度全面剖析你的能力画像，帮助定位最适合你的创作者身份模型。
            </p>
          </div>
        </div>
      </template>

      <UAlert
        v-if="errorMessage"
        color="error"
        variant="soft"
        title="提交失败"
        :description="errorMessage"
        icon="i-lucide-alert-triangle"
        class="mb-6"
      />

      <UForm :schema="schema" :state="formState" class="space-y-6" @submit="onSubmit">
        <div class="space-y-4 md:grid md:grid-cols-2 md:gap-6 md:space-y-0">
          <UFormField label="核心技能栈 (Skill Stack)" name="skills" required>
            <template #description>
              <span class="text-xs text-slate-400">你最擅长的专业技能，逗号或换行分隔</span>
            </template>
            <UTextarea v-model="formState.skills" :rows="3" class="w-full touch-target transition-shadow focus:ring-primary-500" />
          </UFormField>

          <UFormField label="兴趣与能量区 (Energy Zone)" name="interests" required>
            <template #description>
              <span class="text-xs text-slate-400">做起来不觉得累、能持续产出的领域</span>
            </template>
            <UTextarea v-model="formState.interests" :rows="3" class="w-full touch-target transition-shadow focus:ring-primary-500" />
          </UFormField>
        </div>

        <UFormField label="认知风格 (Cognitive Style)" name="cognitiveStyle" required class="w-full">
          <template #description>
            <span class="text-xs text-slate-400">例如：结构化拆解、感性共情、数据驱动</span>
          </template>
          <UInput v-model="formState.cognitiveStyle" class="touch-target w-full" />
        </UFormField>

        <UFormField label="价值观与红线 (Value Boundaries)" name="valueBoundaries" required class="w-full">
          <template #description>
            <span class="text-xs text-slate-400">你坚持什么？坚决不做什么？</span>
          </template>
          <UTextarea v-model="formState.valueBoundaries" :rows="2" class="w-full touch-target" />
        </UFormField>

        <div class="grid gap-6 sm:grid-cols-2 bg-slate-50 dark:bg-slate-900/50 p-5 rounded-xl border border-slate-100 dark:border-slate-800">
          <UFormField label="对争议的风险承受度" name="riskTolerance" required>
            <USelect
              v-model="formState.riskTolerance"
              class="touch-target w-full"
              :items="[
                { label: '低风险 (维稳优先)', value: 'low' },
                { label: '中风险 (接受适度辩论)', value: 'medium' },
                { label: '高风险 (拥抱争议与流量)', value: 'high' }
              ]"
            />
          </UFormField>

          <UFormField label="每周可投入时间 (小时)" name="weeklyHours" required>
            <UInput v-model="formState.weeklyHours" type="number" class="touch-target w-full" />
          </UFormField>
        </div>

        <UFormField label="现阶段核心目标 (Current Goals)" name="goals" required class="w-full">
          <template #description>
            <span class="text-xs text-slate-400">例如：涨粉、变现验证、建立个人IP库</span>
          </template>
          <UTextarea v-model="formState.goals" :rows="2" class="w-full touch-target" />
        </UFormField>

        <div class="pt-4 flex justify-end">
          <UButton 
            type="submit" 
            :loading="loading" 
            class="touch-target flex-1 sm:flex-none justify-center px-8 shadow-md hover:shadow-lg transition-all font-semibold"
            size="lg"
            color="primary"
            trailing-icon="i-lucide-arrow-right"
          >
            生成能力画像并进入身份模型
          </UButton>
        </div>
      </UForm>
    </UCard>
  </div>
</template>
