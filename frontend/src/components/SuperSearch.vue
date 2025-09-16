<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center">
            <div class="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
              <span class="material-symbols-outlined text-white text-lg">storage</span>
            </div>
            <h1 class="text-xl font-semibold text-gray-900">StatDig</h1>
            <span class="ml-3 text-gray-400">|</span>
            <h2 class="ml-3 text-lg font-medium text-gray-700">SuperSearch Copilot</h2>
          </div>
          <div class="flex items-center space-x-4">
            <router-link 
              to="/dashboard" 
              class="flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors"
            >
              <span class="material-symbols-outlined text-lg">home</span>
              <span class="text-base">Dashboard</span>
            </router-link>
            <div class="flex items-center space-x-2 text-base text-gray-600">
              <span class="material-symbols-outlined text-lg">person</span>
              <span>{{ user?.username }}</span>
            </div>
            <button
              @click="logout"
              class="flex items-center space-x-1 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <span class="material-symbols-outlined text-lg">logout</span>
              <span class="text-base">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <!-- Sticky Search Section -->
      <div class="mb-8 sticky top-0 z-20 bg-gray-50 pt-2 pb-4">
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span class="material-symbols-outlined mr-2">search</span>
            Intelligent Search
          </h2>
          <div class="flex gap-4 items-center relative">
            <div class="flex-1 relative">
              <input
                v-model="searchTerm"
                @keyup.enter="performSearch"
                type="text"
                placeholder="Search for malware behaviors, IOCs, function names, or techniques..."
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors pr-40 text-base"
              >
              <span v-if="lastSearchType" class="absolute right-4 top-1/2 -translate-y-1/2 px-3 py-1 rounded-full text-base font-medium select-none"
                :class="lastSearchType === 'semantic' ? 'bg-purple-100 text-purple-700' : 'bg-green-100 text-green-700'">
                {{ lastSearchType === 'semantic' ? 'Semantic' : 'Exact' }}
              </span>
            </div>
            <button
              @click="performSearch"
              :disabled="!searchTerm.trim() || searching"
              class="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2 text-base"
            >
              <span class="material-symbols-outlined" :class="{ 'animate-spin': searching }">
                {{ searching ? 'progress_activity' : 'search' }}
              </span>
              <span>{{ searching ? 'Searching...' : 'Search' }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Results Section -->
      <div v-if="hasResults || searching" class="space-y-6">
        <!-- AI Analysis Section -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900 flex items-center">
              <span class="material-symbols-outlined mr-2">psychology</span>
              SuperSearch Overview
            </h3>
            <button v-if="showExpandAll" @click="expandAll = !expandAll" class="px-3 py-1 rounded bg-blue-100 text-blue-700 hover:bg-blue-200 text-base font-medium">
              {{ expandAll ? 'Collapse all' : 'Expand all' }}
            </button>
          </div>
          <div>
            <transition name="fade-reveal">
              <div v-if="aiAnalysis" class="prose max-w-none text-gray-700 animate-fade-in">
                <div v-html="renderedAnalysis"></div>
              </div>
            </transition>
            <div v-if="!aiAnalysis && analysisJobId" class="flex items-center justify-center py-8">
              <div class="text-center">
                <span class="material-symbols-outlined animate-spin text-blue-600 text-3xl mb-3">progress_activity</span>
                <p class="text-gray-600 text-base">AI is analyzing your search results...</p>
                <p class="text-base text-gray-500 mt-1">This may take a few moments</p>
              </div>
            </div>
            <div v-if="!aiAnalysis && !analysisJobId" class="bg-gray-50 rounded-lg p-4 text-center text-gray-500 text-base">
              AI analysis will appear here after you perform a search
            </div>
          </div>
        </div>

        <!-- Search Results -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200">
          <div class="p-6 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900 flex items-center">
              <span class="material-symbols-outlined mr-2">list</span>
              Search Results
              <span v-if="searchResults.length > 0" class="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-base font-medium">
                {{ searchResults.length }}
              </span>
            </h3>
            <button v-if="showExpandAll" @click="expandAll = !expandAll" class="px-3 py-1 rounded bg-blue-100 text-blue-700 hover:bg-blue-200 text-base font-medium">
              {{ expandAll ? 'Collapse all' : 'Expand all' }}
            </button>
          </div>

          <div v-if="searching" class="p-8 text-center">
            <span class="material-symbols-outlined animate-spin text-gray-400 text-3xl">progress_activity</span>
            <p class="text-gray-500 mt-2 text-base">Searching...</p>
          </div>
          
          <div v-else-if="searchResults.length === 0 && hasSearched" class="p-8 text-center">
            <span class="material-symbols-outlined text-gray-400 text-4xl">search_off</span>
            <p class="text-gray-500 mt-2 text-base">No results found for "{{ lastSearchTerm }}"</p>
          </div>

          <div v-else-if="searchResults.length > 0" class="divide-y divide-gray-200">
            <div
              v-for="(result, index) in searchResults"
              :key="`${result.type}-${index}`"
              class="p-4 hover:bg-gray-50 transition-colors"
            >
              <!-- Sample Result -->
              <div v-if="result.type === 'sample'" class="flex items-start justify-between">
                <div class="flex items-start space-x-3 flex-1">
                  <div class="h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <span class="material-symbols-outlined text-green-600">description</span>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center space-x-2 mb-1">
                      <h4 class="text-base font-medium text-gray-900 truncate">{{ result.original_filename }}</h4>
                      <span class="text-base text-gray-500 font-mono">{{ result.md5.substring(0, 8) }}...</span>
                    </div>
                    <div class="flex flex-wrap items-center gap-2 text-base text-gray-500 mb-2">
                      <span>{{ result.filetype }}</span>
                      <span v-if="result.malicious" :class="{
                        'text-red-600 font-bold': result.malicious === 'True',
                        'text-green-600 font-bold': result.malicious === 'False',
                        'text-yellow-600 font-bold': result.malicious === 'Uncertain'
                      }">
                        {{ result.malicious === 'True' ? 'Malicious' : result.malicious === 'False' ? 'Benign' : 'Uncertain' }}
                      </span>
                      <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                        Score: {{ (result.score * 100).toFixed(1) }}%
                      </span>
                    </div>
                    <p v-if="result.overview && !isUnIndexed(result.overview)" class="text-base text-gray-700 mb-2">
                      <span v-if="!expandAll && !expandedSamples[result.md5] && result.overview.length > 180">
                        {{ result.overview.slice(0, 180) }}... 
                        <button @click="expandedSamples[result.md5] = true" class="text-blue-600 hover:underline ml-2">See more</button>
                      </span>
                      <span v-else>{{ result.overview }}</span>
                    </p>
                    <div v-if="result.tags" class="flex flex-wrap gap-1">
                      <span 
                        v-for="tag in result.tags.split(',')" 
                        :key="tag" 
                        class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-base"
                      >
                        {{ tag.trim() }}
                      </span>
                    </div>
                  </div>
                </div>
                <div class="flex items-center space-x-2 ml-4">
                  <button
                    @click="viewSampleReport(result.md5)"
                    class="px-3 py-1 text-base bg-blue-100 text-blue-700 hover:bg-blue-200 rounded-lg flex items-center space-x-1 transition-colors"
                  >
                    <span class="material-symbols-outlined text-base">visibility</span>
                    <span>View Report</span>
                  </button>
                </div>
              </div>

              <!-- Function Result -->
              <div v-else-if="result.type === 'function'" class="flex items-start justify-between">
                <div class="flex items-start space-x-3 flex-1">
                  <div class="h-10 w-10 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <span class="material-symbols-outlined text-purple-600">functions</span>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center space-x-2 mb-1">
                      <h4 class="text-base font-medium text-gray-900 truncate">{{ result.name }}</h4>
                      <span class="px-2 py-1 bg-purple-100 text-purple-700 rounded text-base">
                        Score: {{ (result.score * 100).toFixed(1) }}%
                      </span>
                    </div>
                    <p v-if="result.description && !isUnIndexed(result.description)" class="text-base text-gray-700 mb-2">
                      <span v-if="!expandAll && !expandedFunctions[result.name] && result.description.length > 180">
                        {{ result.description.slice(0, 180) }}... 
                        <button @click="expandedFunctions[result.name] = true" class="text-blue-600 hover:underline ml-2">See more</button>
                      </span>
                      <span v-else>{{ result.description }}</span>
                    </p>
                    <div class="text-base text-gray-500 mb-2">
                      Sample: {{ result.sample_md5.substring(0, 8) }}...
                    </div>
                  </div>
                </div>
                <div class="flex items-center space-x-2 ml-4">
                  <button
                    @click="viewFunctionCode(result)"
                    class="px-3 py-1 text-base bg-purple-100 text-purple-700 hover:bg-purple-200 rounded-lg flex items-center space-x-1 transition-colors"
                  >
                    <span class="material-symbols-outlined text-base">code</span>
                    <span>View Code</span>
                  </button>
                  <button
                    @click="viewSampleReport(result.sample_md5)"
                    class="px-3 py-1 text-base bg-gray-100 text-gray-700 hover:bg-gray-200 rounded-lg flex items-center space-x-1 transition-colors"
                  >
                    <span class="material-symbols-outlined text-base">launch</span>
                    <span>Sample</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Initial State -->
      <div v-if="!hasResults && !searching && !hasSearched" class="text-center py-16">
        <div class="h-24 w-24 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-6">
          <span class="material-symbols-outlined text-white text-4xl">search</span>
        </div>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">Intelligent Malware Search</h3>
        <p class="text-gray-600 max-w-2xl mx-auto text-base">
          Search for malware behaviors, techniques, IOCs, or specific identifiers. 
          Our AI will classify your search and find the most relevant samples and functions.
        </p>
      </div>
    </main>

    <!-- Code Modal -->
    <div v-if="showCodeModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        <div class="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h3 class="text-lg font-semibold text-gray-900">{{ selectedFunction?.name }}</h3>
            <p class="text-base text-gray-600 mt-1">Function Code</p>
          </div>
          <button
            @click="closeCodeModal"
            class="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <span class="material-symbols-outlined text-2xl">close</span>
          </button>
        </div>
        <div class="flex-1 overflow-hidden">
          <div id="code-modal-container" class="h-full"></div>
        </div>
        <div class="p-4 border-t border-gray-200 bg-gray-50 flex justify-end space-x-3">
          <button
            @click="viewSampleReport(selectedFunction?.sample_md5)"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <span class="material-symbols-outlined text-base">launch</span>
            <span>View Sample Report</span>
          </button>
          <button
            @click="closeCodeModal"
            class="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const router = useRouter()
const apiBase = inject('apiBase')

const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
const token = localStorage.getItem('token')

const searchTerm = ref('')
const lastSearchTerm = ref('')
const lastSearchType = ref('')
const searching = ref(false)
const hasSearched = ref(false)
const searchResults = ref([])
const analysisJobId = ref('')
const aiAnalysis = ref('')
const showCodeModal = ref(false)
const selectedFunction = ref(null)
const pollInterval = ref(null)
const expandedSamples = ref({})
const expandedFunctions = ref({})
const expandAll = ref(false)

const hasResults = computed(() => searchResults.value.length > 0 || aiAnalysis.value)
const showExpandAll = computed(() => searchResults.value.some(r => (r.type === 'sample' && r.overview && r.overview.length > 180) || (r.type === 'function' && r.description && r.description.length > 180)))

const renderedAnalysis = computed(() => {
  if (!aiAnalysis.value) return ''
  try {
    const html = marked.parse(aiAnalysis.value)
    return DOMPurify.sanitize(html)
  } catch (err) {
    return `<pre>${aiAnalysis.value}</pre>`
  }
})

const isUnIndexed = (text) => text && text.startsWith('UN_IDX_')

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}

const performSearch = async () => {
  if (!searchTerm.value.trim()) return
  
  searching.value = true
  hasSearched.value = true
  lastSearchTerm.value = searchTerm.value
  searchResults.value = []
  aiAnalysis.value = ''
  analysisJobId.value = ''
  expandedSamples.value = {}
  expandedFunctions.value = {}
  expandAll.value = false
  
  try {
    const response = await fetch(`${apiBase}/supersearch`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ search_term: searchTerm.value })
    })
    
    if (response.ok) {
      const data = await response.json()
      searchResults.value = data.results
      lastSearchType.value = data.type
      analysisJobId.value = data.job_id
      
      // Start polling for AI analysis
      if (data.job_id) {
        startPollingAnalysis(data.job_id)
      }
    } else {
      console.error('Search failed')
    }
  } catch (error) {
    console.error('Search error:', error)
  } finally {
    searching.value = false
  }
}

const startPollingAnalysis = (jobId) => {
  const pollForAnalysis = async () => {
    try {
      const response = await fetch(`${apiBase}/supersearch/${jobId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      console.log(response);
      if (response.status === 202) {
        // Status 202 means still processing, continue polling
        console.log('Analysis still being generated, continuing to poll...')
      } else if  (response.ok) {
        const data = await response.json()
        aiAnalysis.value = data.summary
        stopPolling()
      } else if (response.status === 404) {
        // Job not found or error, but continue polling for a bit
        console.log('Job not found yet, continuing to poll...')
      } else {
        // Other error, stop polling
        console.error('Polling error:', response.status)
        stopPolling()
      }
    } catch (error) {
      // Network error, continue polling
      console.log('Network error during polling, continuing...', error)
    }
  }
  // Poll immediately and then every 2 seconds
  pollForAnalysis()
  pollInterval.value = setInterval(pollForAnalysis, 2000)
}

const stopPolling = () => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
    pollInterval.value = null
  }
}

const viewSampleReport = (md5) => {
  router.push(`/report/${md5}`)
}

const viewFunctionCode = async (functionResult) => {
  selectedFunction.value = functionResult
  showCodeModal.value = true
  
  await nextTick()
  showCodeInModal(functionResult.c_code || '// No code available')
}

const showCodeInModal = (code) => {
  if (!window.CodeMirror) return
  const container = document.getElementById('code-modal-container')
  if (!container) return
  container.innerHTML = ''
  window.CodeMirror(container, {
    value: code,
    mode: 'clike',
    lineNumbers: true,
    readOnly: true,
    theme: 'mdn-like',
    viewportMargin: Infinity
  })
}

const closeCodeModal = () => {
  showCodeModal.value = false
  selectedFunction.value = null
}

// Expand all/collapse all logic
watch(expandAll, (val) => {
  if (val) {
    // Expand all
    searchResults.value.forEach(r => {
      if (r.type === 'sample' && r.overview && r.overview.length > 180) expandedSamples.value[r.md5] = true
      if (r.type === 'function' && r.description && r.description.length > 180) expandedFunctions.value[r.name] = true
    })
  } else {
    expandedSamples.value = {}
    expandedFunctions.value = {}
  }
})

onMounted(() => {
  if (!token || !user.value) {
    router.push('/login')
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style>
.fade-reveal-enter-active {
  animation: fadeInReveal 0.7s cubic-bezier(0.4,0,0.2,1);
}
@keyframes fadeInReveal {
  0% { opacity: 0; transform: translateY(30px); }
  100% { opacity: 1; transform: translateY(0); }
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.prose {
  color: #374151;
  line-height: 1.75;
  font-size: 1rem;
  max-width: 100%;
}
</style>