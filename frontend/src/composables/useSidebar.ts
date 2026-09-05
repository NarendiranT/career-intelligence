import { ref, watch } from 'vue'

const LEFT_KEY = 'ci.leftSidebarCollapsed'
const RIGHT_KEY = 'ci.rightSidebarCollapsed'

const leftCollapsed = ref(false)
const rightCollapsed = ref(false)
let hydrated = false

function readFlag(key: string) {
  try {
    return window.localStorage.getItem(key) === '1'
  } catch {
    return false
  }
}

function persist(key: string, value: boolean) {
  try {
    window.localStorage.setItem(key, value ? '1' : '0')
  } catch {
    /* ignore */
  }
}

function hydrate() {
  if (hydrated || typeof window === 'undefined') return
  hydrated = true
  leftCollapsed.value = readFlag(LEFT_KEY)
  rightCollapsed.value = readFlag(RIGHT_KEY)
  watch(leftCollapsed, (value) => persist(LEFT_KEY, value))
  watch(rightCollapsed, (value) => persist(RIGHT_KEY, value))
}

export function useSidebar() {
  hydrate()

  function toggleLeft() {
    leftCollapsed.value = !leftCollapsed.value
  }

  function toggleRight() {
    rightCollapsed.value = !rightCollapsed.value
  }

  return {
    leftCollapsed,
    rightCollapsed,
    toggleLeft,
    toggleRight,
  }
}
