<template>
  <div class="h-full flex flex-col bg-gray-50">
    <!-- Header with Start Button -->
    <div class="px-6 py-4 border-b border-gray-200 bg-white">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <span class="material-symbols-outlined text-blue-600 text-xl">group_work</span>
          </div>
          <div>
            <h3 class="font-semibold text-gray-800">Organiser Agent</h3>
            <p class="text-sm text-gray-600">
              {{ getStatusMessage() }}
            </p>
          </div>
        </div>
        <button 
          @click="triggerOrganiser" 
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading || isRunning"
        >
          {{ getButtonText() }}
        </button>
      </div>
    </div>

    <!-- Messages Container -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6 space-y-4">
      <div v-if="!messages.length && !loading && !isRunning" class="text-center py-12">
        <div class="h-16 w-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span class="material-symbols-outlined text-gray-400 text-2xl">chat</span>
        </div>
        <p class="text-gray-500">No organiser activity yet. Click "Start Organiser" to begin.</p>
      </div>

      <div v-for="(message, index) in displayMessages" :key="index" 
           class="bg-white rounded-lg border shadow-sm overflow-hidden">
        
        <!-- Assistant Message -->
        <div v-if="message.role === 'assistant'" class="p-4">
          <div class="flex items-start gap-3">
            <div class="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
              <span class="material-symbols-outlined text-blue-600 text-sm">smart_toy</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-gray-800 mb-2">Agent Analysis</div>
              <div v-if="isJsonContent(message.content)" class="bg-gray-50 rounded p-3 border">
                <pre class="text-xs text-gray-700 whitespace-pre-wrap font-mono">{{ formatJson(message.content) }}</pre>
              </div>
              <div v-else class="prose prose-sm max-w-none text-gray-700" v-html="renderMarkdown(message.content)"></div>
              
              <!-- Tool Calls -->
              <div v-if="message.tool_calls" class="mt-3 space-y-2">
                <div v-for="toolCall in message.tool_calls" :key="toolCall.id" 
                     class="bg-blue-50 rounded-lg p-3 border border-blue-200">
                  <div class="flex items-center gap-2 text-sm">
                    <span class="material-symbols-outlined text-blue-600 text-base">search</span>
                    <span class="font-medium text-blue-800">Searching the web for more information...</span>
                  </div>
                  <div class="mt-1 text-xs text-blue-600">
                    Tool: {{ toolCall.function.name }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tool Response -->
        <div v-if="message.role === 'tool'" class="px-4 py-3 bg-gray-50 border-t">
          <div class="flex items-start gap-3">
            <div class="h-6 w-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              <span class="material-symbols-outlined text-green-600 text-xs">check_circle</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-xs font-medium text-gray-600 mb-1">Search completed</div>
              <div class="text-xs text-gray-500">Tool: {{ message.name }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading indicator for new messages -->
      <div v-if="isRunning && messages.length > 0" class="bg-white rounded-lg border shadow-sm p-4 animate-pulse">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
            <span class="material-symbols-outlined text-blue-600 text-sm animate-spin">refresh</span>
          </div>
          <div class="text-sm text-gray-600">Agent is thinking...</div>
        </div>
      </div>
      <!-- Database update confirmation -->
      <div v-if="showDatabaseUpdate" class="bg-green-50 rounded-lg border border-green-200 shadow-sm p-4">
        <div class="flex items-start gap-3">
          <div class="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
            <span class="material-symbols-outlined text-green-600 text-sm">check_circle</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-green-800 mb-1">Analysis Complete</div>
            <div class="text-sm text-green-700">Database updated with analysis results.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const route = useRoute()
const apiBase = inject('apiBase')
const token = localStorage.getItem('token')

const loading = ref(false)
const isRunning = ref(false)
const messages = ref([])
const analyzeState = ref(0)
const pollInterval = ref(null)
const messagesContainer = ref(null)
const showDatabaseUpdate = ref(false)

const displayMessages = computed(() => {
  return messages.value.filter(msg => 
    msg.role === 'assistant' || msg.role === 'tool'
  )
})

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const hasJsonResponse = computed(() => {
  const lastMessage = messages.value[messages.value.length - 1]
  return lastMessage && 
         lastMessage.role === 'assistant' && 
         isJsonContent(lastMessage.content) &&
         analyzeState.value === 6
})

const getStatusMessage = () => {
  if (loading.value) return 'Starting organiser...'
  if (isRunning.value) return 'Agent is actively analyzing...'
  if (analyzeState.value === 6) return 'Analysis complete'
  if (messages.value.length > 0) return 'Ready to restart analysis'
  return 'Ready to analyze this malware sample'
}

const getButtonText = () => {
  if (loading.value) return 'Starting...'
  if (isRunning.value) return 'Running...'
  if (analyzeState.value === 6) return 'Run Again'
  return 'Start Organiser'
}

const isJsonContent = (content) => {
  if (!content || typeof content !== 'string') return false
  const trimmed = content.trim()
  return (trimmed.startsWith('{') && trimmed.endsWith('}')) || 
         (trimmed.startsWith('[') && trimmed.endsWith(']'))
}

const formatJson = (content) => {
  try {
    const parsed = JSON.parse(content)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return content
  }
}

const renderMarkdown = (content) => {
  try {
    const html = marked.parse(content || '')
    return DOMPurify.sanitize(html)
  } catch {
    return content || ''
  }
}

const triggerOrganiser = async () => {
  loading.value = true
  try {
    const response = await fetch(`${apiBase}/organise/${route.params.md5}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      isRunning.value = true
      startPolling()
    } else {
      console.error('Failed to start organiser')
    }
  } catch (error) {
    console.error('Error starting organiser:', error)
  } finally {
    loading.value = false
  }
}

const fetchOrganiserStatus = async () => {
  try {
    const response = await fetch(`${apiBase}/organise/${route.params.md5}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      const previousMessageCount = messages.value.length
      
      analyzeState.value = data.analyze_state
      
      if (data.organiser_data && Array.isArray(data.organiser_data)) {
        messages.value = data.organiser_data
      }
      
      // Check if still running (state 5 = organizing)
      if (data.analyze_state === 5) {
        isRunning.value = true
        showDatabaseUpdate.value = false
        if (!pollInterval.value) {
          startPolling()
        }
      } else {
        isRunning.value = false
        if (data.analyze_state === 6) {
          showDatabaseUpdate.value = hasJsonResponse.value
        }
        stopPolling()
      }
      
      // Scroll to bottom if new messages arrived
      if (messages.value.length > previousMessageCount) {
        scrollToBottom()
      }
    }
  } catch (error) {
    console.error('Error fetching organiser status:', error)
  }
}

const startPolling = () => {
  if (pollInterval.value) clearInterval(pollInterval.value)
  pollInterval.value = setInterval(fetchOrganiserStatus, 3000)
}

const stopPolling = () => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
    pollInterval.value = null
  }
}

onMounted(() => {
  // Load initial status
  fetchOrganiserStatus()
})

// Watch for changes in messages to auto-scroll
watch(() => messages.value.length, () => {
  scrollToBottom()
}, { flush: 'post' })

// Watch for completion to show database update message
watch(() => hasJsonResponse.value, (newValue) => {
  if (newValue) {
    showDatabaseUpdate.value = true
    scrollToBottom()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.prose {
  color: #374151;
  line-height: 1.6;
  font-size: 0.875rem;
}

.prose h1, .prose h2, .prose h3, .prose h4, .prose h5, .prose h6 {
  color: #1f2937;
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.prose h1 { font-size: 1.25rem; }
.prose h2 { font-size: 1.125rem; }
.prose h3 { font-size: 1rem; }

.prose p {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
}

.prose ul, .prose ol {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  padding-left: 1.25rem;
}

.prose li {
  margin-top: 0.25rem;
  margin-bottom: 0.25rem;
}

.prose code {
  background-color: #f3f4f6;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-family: ui-monospace, monospace;
}

.prose pre {
  background-color: #f9fafb;
  padding: 0.75rem;
  border-radius: 0.375rem;
  overflow-x: auto;
  font-size: 0.75rem;
  margin: 0.5rem 0;
}

.prose blockquote {
  border-left: 3px solid #e5e7eb;
  padding-left: 0.75rem;
  font-style: italic;
  color: #6b7280;
  margin: 0.5rem 0;
}

.prose strong {
  font-weight: 600;
  color: #1f2937;
}
</style>

<style scoped>
/* Component-specific styles */
</style>