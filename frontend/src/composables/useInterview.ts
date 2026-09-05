import { computed, ref } from 'vue'
import { interviewTopics } from '@/types/interview'

const selectedTopicId = ref('python')
const topicQuery = ref('')

export function useInterview() {
  const selectedTopic = computed(
    () => interviewTopics.find((topic) => topic.id === selectedTopicId.value) ?? interviewTopics[0],
  )

  const filteredTopics = computed(() => {
    const q = topicQuery.value.trim().toLowerCase()
    if (!q) return interviewTopics
    return interviewTopics.filter((topic) => topic.label.toLowerCase().includes(q))
  })

  function selectTopic(id: string) {
    if (interviewTopics.some((topic) => topic.id === id)) {
      selectedTopicId.value = id
    }
  }

  return {
    interviewTopics,
    selectedTopicId,
    selectedTopic,
    topicQuery,
    filteredTopics,
    selectTopic,
  }
}
