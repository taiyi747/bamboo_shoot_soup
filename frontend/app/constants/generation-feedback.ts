export interface GenerationFeedbackCopy {
  title: string
  description: string
  hints: string[]
  icon: string
  color: 'primary' | 'info' | 'neutral'
}

export const generationFeedbackCopy: Record<
  'onboarding' | 'identityModels' | 'personaConstitution' | 'launchKit' | 'consistencyCheck',
  GenerationFeedbackCopy
> = {
  onboarding: {
    title: '正在生成能力画像',
    description: 'Agent 正在汇总你的输入并构建可执行画像。',
    hints: ['正在整理技能与兴趣信号...', '正在对齐风险偏好与时间投入...', '正在输出结构化能力画像...'],
    icon: 'i-lucide-clipboard-check',
    color: 'primary',
  },
  identityModels: {
    title: '正在生成身份模型',
    description: 'Agent 正在推演候选身份并检查差异化字段完整性。',
    hints: ['正在生成候选身份卡...', '正在对比内容支柱与语气风格...', '正在准备可选择的主/备身份...'],
    icon: 'i-lucide-users',
    color: 'primary',
  },
  personaConstitution: {
    title: '正在生成人格宪法',
    description: 'Agent 正在构建口吻词典、立场边界与叙事主线。',
    hints: ['正在提取稳定语气规则...', '正在写入观点护城河...', '正在形成成长叙事模板...'],
    icon: 'i-lucide-scroll',
    color: 'primary',
  },
  launchKit: {
    title: '正在生成 7-Day Launch Kit',
    description: 'Agent 正在生成 7 天主题、大纲与增长实验建议。',
    hints: ['正在生成 7 天发文主题...', '正在编排每日草稿大纲...', '正在输出可持续栏目与实验建议...'],
    icon: 'i-lucide-rocket',
    color: 'primary',
  },
  consistencyCheck: {
    title: '正在执行一致性检查',
    description: 'Agent 正在对照人格宪法识别偏离项并给出改写建议。',
    hints: ['正在扫描语气与立场偏离...', '正在定位潜在风险边界...', '正在整理可执行修改建议...'],
    icon: 'i-lucide-check-circle',
    color: 'info',
  },
}
