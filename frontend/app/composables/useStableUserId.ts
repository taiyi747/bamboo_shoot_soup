const STORAGE_KEY = 'bss-mvp-user-id'

const buildUserId = () => {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID()
  }
  return `user_${Math.random().toString(36).slice(2, 10)}`
}

export const useStableUserId = () => {
  const userId = useState<string>('mvp-user-id', () => '')

  if (!userId.value) {
    userId.value = buildUserId()
  }

  if (import.meta.client) {
    const localValue = localStorage.getItem(STORAGE_KEY)
    if (localValue && localValue !== userId.value) {
      userId.value = localValue
    } else if (!localValue) {
      localStorage.setItem(STORAGE_KEY, userId.value)
    }
  }

  return userId
}
