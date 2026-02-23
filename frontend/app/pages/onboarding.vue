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
  <UCard class="surface-card">
    <template #header>
      <h2 class="text-xl font-semibold text-slate-900">
        身份诊断
      </h2>
      <p class="mt-1 text-sm text-slate-600">
        为职场创作者采集六类维度：技能栈、兴趣能量、认知风格、价值边界、风险承受度、时间投入。
      </p>
    </template>

    <UAlert
      v-if="errorMessage"
      color="error"
      variant="soft"
      title="提交失败"
      :description="errorMessage"
      class="mb-4"
    />

    <UForm :schema="schema" :state="formState" class="space-y-4" @submit="onSubmit">
      <UFormField label="技能栈（逗号或换行分隔）" name="skills" required>
        <UTextarea v-model="formState.skills" :rows="2" class="touch-target" />
      </UFormField>

      <UFormField label="兴趣与能量曲线（逗号或换行分隔）" name="interests" required>
        <UTextarea v-model="formState.interests" :rows="2" class="touch-target" />
      </UFormField>

      <UFormField label="认知风格" name="cognitiveStyle" required>
        <UInput v-model="formState.cognitiveStyle" class="touch-target" />
      </UFormField>

      <UFormField label="价值观与边界（逗号或换行分隔）" name="valueBoundaries" required>
        <UTextarea v-model="formState.valueBoundaries" :rows="2" class="touch-target" />
      </UFormField>

      <div class="grid gap-4 sm:grid-cols-2">
        <UFormField label="风险承受度" name="riskTolerance" required>
          <USelect
            v-model="formState.riskTolerance"
            class="touch-target"
            :items="[
              { label: '低风险', value: 'low' },
              { label: '中风险', value: 'medium' },
              { label: '高风险', value: 'high' }
            ]"
          />
        </UFormField>

        <UFormField label="每周可投入小时" name="weeklyHours" required>
          <UInput v-model="formState.weeklyHours" type="number" class="touch-target" />
        </UFormField>
      </div>

      <UFormField label="阶段目标（逗号或换行分隔）" name="goals" required>
        <UTextarea v-model="formState.goals" :rows="2" class="touch-target" />
      </UFormField>

      <div class="flex flex-wrap gap-3">
        <UButton type="submit" :loading="loading" class="touch-target">
          生成能力画像并进入身份模型
        </UButton>
      </div>
    </UForm>
  </UCard>
</template>
