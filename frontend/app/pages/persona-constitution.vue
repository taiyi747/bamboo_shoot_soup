<script setup lang="ts">
import { useApiClient } from '../services/api/client'
import type { PersonaConstitution } from '../types/mvp'

const api = useApiClient()
const { state, selectedPrimaryModel } = useMvpFlow()

const loading = ref(false)
const errorMessage = ref('')

const form = reactive({
  commonWords: '',
  forbiddenWords: '',
  sentencePreferences: '',
  immutablePositions: '',
  narrativeMainline: '',
  growthArc: '',
})

const fillForm = (constitution: PersonaConstitution) => {
  form.commonWords = constitution.commonWords.join('\n')
  form.forbiddenWords = constitution.forbiddenWords.join('\n')
  form.sentencePreferences = constitution.sentencePreferences.join('\n')
  form.immutablePositions = constitution.immutablePositions.join('\n')
  form.narrativeMainline = constitution.narrativeMainline
  form.growthArc = constitution.growthArc.map(item => `${item.stage}：${item.storyTemplate}`).join('\n')
}

const splitLines = (value: string) =>
  value
    .split('\n')
    .map(item => item.trim())
    .filter(Boolean)

const saveDraft = () => {
  state.value.persona = {
    commonWords: splitLines(form.commonWords),
    forbiddenWords: splitLines(form.forbiddenWords),
    sentencePreferences: splitLines(form.sentencePreferences),
    immutablePositions: splitLines(form.immutablePositions),
    narrativeMainline: form.narrativeMainline.trim(),
    growthArc: splitLines(form.growthArc).map(line => {
      const [stage, ...rest] = line.split('：')
      return {
        stage: stage || '阶段',
        storyTemplate: rest.join('：') || line,
      }
    }),
  }
}

const generateConstitution = async () => {
  if (!selectedPrimaryModel.value) {
    errorMessage.value = '请先在上一页选择主身份。'
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    const result = await api.generatePersonaConstitution({
      identityModel: selectedPrimaryModel.value,
    })
    state.value.persona = result.constitution
    fillForm(result.constitution)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '人格宪法生成失败。'
  } finally {
    loading.value = false
  }
}

const nextStep = async () => {
  saveDraft()
  await navigateTo('/launch-kit')
}

if (state.value.persona) {
  fillForm(state.value.persona)
}
</script>

<template>
  <UCard class="surface-card">
    <template #header>
      <h2 class="text-xl font-semibold text-slate-900">
        M2 人格宪法
      </h2>
      <p class="mt-1 text-sm text-slate-600">
        编辑并固化口吻词典、观点护城河、叙事主线与成长 Arc。
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
      <UButton class="touch-target" :loading="loading" @click="generateConstitution">
        生成人格宪法
      </UButton>
      <UButton color="neutral" variant="outline" class="touch-target" @click="nextStep">
        保存并进入 7 天启动包
      </UButton>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <UFormField label="口吻词典：常用词（每行一个）">
        <UTextarea v-model="form.commonWords" :rows="5" class="touch-target" />
      </UFormField>
      <UFormField label="口吻词典：禁用词（每行一个）">
        <UTextarea v-model="form.forbiddenWords" :rows="5" class="touch-target" />
      </UFormField>
      <UFormField label="句式偏好（每行一个）">
        <UTextarea v-model="form.sentencePreferences" :rows="5" class="touch-target" />
      </UFormField>
      <UFormField label="观点护城河（每行一个）">
        <UTextarea v-model="form.immutablePositions" :rows="5" class="touch-target" />
      </UFormField>
    </div>

    <div class="mt-4 grid gap-4">
      <UFormField label="叙事主线">
        <UTextarea v-model="form.narrativeMainline" :rows="3" class="touch-target" />
      </UFormField>
      <UFormField label="成长 Arc（格式：阶段：模板，每行一个）">
        <UTextarea v-model="form.growthArc" :rows="4" class="touch-target" />
      </UFormField>
    </div>
  </UCard>
</template>
