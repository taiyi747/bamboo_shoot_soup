export const useLoadingFeedback = (hints: string[], intervalMs = 1800) => {
  const currentIndex = ref(0)
  let timer: ReturnType<typeof setInterval> | undefined

  const currentHint = computed<string>(() => {
    if (hints.length === 0) {
      return '正在处理中...'
    }
    return hints[currentIndex.value] ?? hints[0] ?? '正在处理中...'
  })

  const stop = () => {
    if (!timer) {
      return
    }
    clearInterval(timer)
    timer = undefined
  }

  const start = () => {
    if (timer || hints.length <= 1) {
      return
    }
    timer = setInterval(() => {
      currentIndex.value = (currentIndex.value + 1) % hints.length
    }, intervalMs)
  }

  const reset = () => {
    stop()
    currentIndex.value = 0
  }

  onBeforeUnmount(() => {
    stop()
  })

  return {
    currentHint,
    start,
    stop,
    reset,
  }
}
