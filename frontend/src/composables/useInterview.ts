import { computed, ref } from 'vue'
import { listTopics } from '@/api/topics'
import type { InterviewTopic } from '@/types/interview'

const topics = ref<InterviewTopic[]>([])
const selectedTopicId = ref('')
const topicQuery = ref('')
const topicsLoading = ref(false)

export function useInterview() {
  const selectedTopic = computed(
    () => topics.value.find((topic) => topic.id === selectedTopicId.value) ?? topics.value[0] ?? null,
  )

  const filteredTopics = computed(() => {
    const q = topicQuery.value.trim().toLowerCase()
    if (!q) return topics.value
    return topics.value.filter((topic) => topic.label.toLowerCase().includes(q))
  })

  function selectTopic(id: string) {
    if (topics.value.some((topic) => topic.id === id)) {
      selectedTopicId.value = id
    }
  }

  function incrementQuestionCount(id: string) {
    const topic = topics.value.find((item) => item.id === id)
    if (!topic) return
    topic.question_count = (topic.question_count ?? 0) + 1
  }

  async function loadTopics(): Promise<InterviewTopic[]> {
    topicsLoading.value = true
    try {
      topics.value = await listTopics()
      if (selectedTopicId.value && !topics.value.some((topic) => topic.id === selectedTopicId.value)) {
        selectedTopicId.value = topics.value[0]?.id ?? ''
      } else if (!selectedTopicId.value && topics.value[0]) {
        selectedTopicId.value = topics.value[0].id
      }
      return topics.value
    } finally {
      topicsLoading.value = false
    }
  }

  return {
    interviewTopics: topics,
    selectedTopicId,
    selectedTopic,
    topicQuery,
    filteredTopics,
    topicsLoading,
    selectTopic,
    incrementQuestionCount,
    loadTopics,
  }
}
