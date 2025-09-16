<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Top Bar -->
    <header class="w-full fixed top-0 left-0 z-20 bg-white border-b border-gray-200">
      <div class="w-full px-6 flex justify-between items-center h-16">
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 bg-blue-600 rounded-lg flex items-center justify-center">
            <span class="material-symbols-outlined text-white text-2xl">storage</span>
          </div>
          <h1 class="text-xl font-semibold text-gray-900">StatDig</h1>
        </div>
        <nav class="flex items-center gap-6">
          <router-link to="/dashboard" class="flex items-center gap-1 text-gray-700 hover:text-blue-600 font-medium">
            <span class="material-symbols-outlined text-base">home</span> Home
          </router-link>
          <router-link to="/supersearch" class="flex items-center gap-1 bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-2 rounded-lg shadow hover:from-blue-600 hover:to-purple-600 transition-colors font-semibold">
            <span class="material-symbols-outlined text-base">search</span> SuperSearch
          </router-link>
          <button @click="logout" class="flex items-center gap-1 text-gray-600 hover:text-red-600 font-medium">
            <span class="material-symbols-outlined text-base">logout</span> Logout
          </button>
        </nav>
      </div>
    </header>
    <div class="flex-1 flex w-full pt-16 bg-gray-50">
      <div class="w-full flex flex-row h-[calc(100vh-4rem)] bg-white shadow-lg border-x border-gray-200 overflow-hidden">
        <!-- Leftmost Pane: All Functions -->
        <aside class="w-80 min-w-[16rem] h-full flex flex-col border-r border-gray-300 bg-gray-50">
          <div class="flex flex-col h-full overflow-hidden">
            <div class="px-6 py-3 border-b border-gray-300 bg-gray-200 shadow-sm">
              <h2 class="text-sm font-semibold text-gray-800 flex items-center gap-2">
                <span class="material-symbols-outlined text-purple-600">functions</span>
                All Functions
              </h2>
            </div>
            <div class="flex-1 overflow-y-auto py-2 px-3 bg-white">
              <ul class="space-y-1">
                <li v-for="fn in functions" :key="fn.name">
                  <button @click="selectFunction(fn)" class="w-full text-left px-3 py-2 rounded hover:bg-blue-50 text-sm truncate flex items-center gap-2 transition-colors"
                          :class="{ 'bg-blue-50 border-l-2 border-blue-500': selectedFunction?.name === fn.name }">
                    <span v-if="isInTree(fn.name)" class="text-yellow-500 text-xs">★</span>
                    <span class="flex-1 truncate">{{ fn.name }}</span>
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </aside>
        <!-- Main Content Area -->
        <main class="flex-1 flex flex-row min-w-0">
          <!-- Left: Report Markdown -->
          <section class="w-1/2 min-w-[22rem] max-w-[40rem] h-full flex flex-col bg-white border-r border-gray-200">
            <!-- Report Header -->
            <div class="px-6 py-3 border-b border-gray-300 bg-blue-50 shadow-sm">
              <h2 class="text-sm font-semibold text-gray-800 flex items-center gap-2">
                <span class="material-symbols-outlined text-blue-800">assessment</span>
                Analysis Report
              </h2>
            </div>
            <!-- Report Content -->
            <div class="flex-1 overflow-y-auto">
              <!-- Binary Summary Section -->
              <div class="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h3 class="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <span class="material-symbols-outlined text-blue-600">info</span>
                  Binary Information
                </h3>
                <div v-if="binaryDetails" class="grid grid-cols-2 gap-3 text-xs">
                  <div class="bg-white p-3 rounded-lg border shadow-sm">
                    <div class="font-semibold text-gray-600 mb-1">Filename</div>
                    <div class="text-gray-900 truncate">{{ binaryDetails.original_filename }}</div>
                  </div>
                  <div class="bg-white p-3 rounded-lg border shadow-sm">
                    <div class="font-semibold text-gray-600 mb-1">File Type</div>
                    <div class="text-gray-900">{{ binaryDetails.filetype }}</div>
                  </div>
                  <div class="bg-white p-3 rounded-lg border shadow-sm">
                    <div class="font-semibold text-gray-600 mb-1">Size</div>
                    <div class="text-gray-900">{{ formatFileSize(binaryDetails.file_size) }}</div>
                  </div>
                  <div class="bg-white p-3 rounded-lg border shadow-sm">
                    <div class="font-semibold text-gray-600 mb-1">Status</div>
                    <div :class="{
                      'text-red-600 font-bold': binaryDetails.malicious === 'True',
                      'text-green-600 font-bold': binaryDetails.malicious === 'False',
                      'text-yellow-600 font-bold': binaryDetails.malicious === 'Uncertain'
                    }">
                      <span v-if="binaryDetails.malicious === 'True'">Malicious</span>
                      <span v-else-if="binaryDetails.malicious === 'False'">Benign</span>
                      <span v-else-if="binaryDetails.malicious === 'Uncertain'">Uncertain</span>
                      <span v-else class="text-gray-400 italic">Pending Analysis</span>
                    </div>
                  </div>
                  <div v-if="binaryDetails.file_description && binaryDetails.file_description !== 'unknown'" class="bg-white p-3 rounded-lg border shadow-sm col-span-2">
                    <div class="font-semibold text-gray-600 mb-1">Description</div>
                    <div class="text-gray-900 text-sm">{{ binaryDetails.file_description }}</div>
                  </div>
                  <div v-if="binaryDetails.overview && !isUnIndexed(binaryDetails.overview)" class="bg-white p-3 rounded-lg border shadow-sm col-span-2">
                    <div class="font-semibold text-gray-600 mb-1">Overview</div>
                    <div class="text-gray-900 text-sm">{{ binaryDetails.overview }}</div>
                  </div>
                </div>
              </div>
              
              <!-- Function Tree Section -->
              <div v-if="sigfnTree" class="px-6 py-4 border-b border-gray-200">
                <h3 class="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <span class="material-symbols-outlined text-blue-600">account_tree</span>
                  Function Call Tree
                </h3>
                <div class="bg-gray-50 rounded-lg border p-4 shadow-sm">
                  <FunctionTree :sigfnTree="sigfnTree" @select="selectFunction" />
                </div>
              </div>
              
              <!-- Analysis Content -->
              <div class="px-6 py-4">
                <div class="prose max-w-none" v-html="processedAnalysis"></div>
              </div>
            </div>
          </section>
          <!-- Right: Tabbed Interface -->
          <section class="w-1/2 min-w-[22rem] flex flex-col h-full bg-gray-50">
            <!-- Tab Headers -->
            <div class="border-b border-gray-300 bg-gray-200 shadow-sm">
              <div class="flex space-x-1">
                <button 
                  @click="activeTab = 'functions'"
                  :class="['px-6 py-3 text-sm font-semibold transition-colors flex-1 flex items-center justify-center gap-2', 
                    activeTab === 'functions' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50']"
                >
                  <span class="material-symbols-outlined text-base">psychology</span>
                  <span>Function Details</span>
                </button>
                <button 
                  @click="activeTab = 'organiser'"
                  :class="['px-6 py-3 text-sm font-semibold transition-colors flex-1 flex items-center justify-center gap-2', 
                    activeTab === 'organiser' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50']"
                >
                  <span class="material-symbols-outlined text-base">group_work</span>
                  <span>Organiser Agent</span>
                </button>
                <button 
                  @click="activeTab = 'responder'"
                  :class="['px-6 py-3 text-sm font-semibold transition-colors flex-1 flex items-center justify-center gap-2', 
                    activeTab === 'responder' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50']"
                >
                  <span class="material-symbols-outlined text-base">chat</span>
                  <span>Responder</span>
                </button>
              </div>
            </div>            <!-- Tab Content - intentional overflow y scroll -->
            <div class="flex-1 flex flex-col overflow-y-scroll">
              <!-- Function Details Tab -->
              <div v-show="activeTab === 'functions'" class="flex-1 flex flex-col">
                <div class="px-6 py-3 border-b border-gray-200 bg-gray-100 flex items-center justify-between">
                  <span class="text-sm font-semibold text-gray-800">Selected Function</span>
                  <button @click="detailsOpen = !detailsOpen" class="text-xs text-blue-600 hover:underline">
                    <span class="material-symbols-outlined text-base align-middle">{{ detailsOpen ? 'expand_less' : 'expand_more' }}</span>
                    {{ detailsOpen ? 'Collapse' : 'Expand' }}
                  </button>
                </div>
                <transition name="fade">
                  <div v-show="detailsOpen" class="px-6 py-4 border-b border-gray-100 bg-white">
                    <div v-if="selectedFunction">
                      <div class="mb-2">
                        <span class="font-semibold">Name:</span> {{ selectedFunction.name }}
                      </div>
                      <div class="mb-2 break-words">
                        <span class="font-semibold">Signature:</span> <span class="font-mono text-xs">{{ selectedFunction.signature }}</span>
                      </div>
                      <div class="mb-2">
                        <span class="font-semibold block mb-1">Description:</span>
                        <p v-if="selectedFunction.description && !isUnIndexed(selectedFunction.description)" class="text-sm text-gray-700 break-words">{{ selectedFunction.description }}</p>
                        <p v-else class="italic text-gray-400">None</p>
                      </div>
                    </div>
                    <div v-else class="text-gray-400">Select a function to view details.</div>
                  </div>
                </transition>
                <div class="flex-1 overflow-hidden bg-gray-50">
                  <div id="codemirror-container" class="h-full border border-gray-200 bg-white"></div>
                </div>
              </div>
              
              <!-- Organiser Agent Tab -->
              <div v-show="activeTab === 'organiser'" class="flex-1">
                <OrganiserAgent />
              </div>
              
              <!-- Responder Tab -->
              <div v-show="activeTab === 'responder'" class="flex-1">
                <ResponderAgent />
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import FunctionTree from './FunctionTree.vue'
import OrganiserAgent from './OrganiserAgent.vue'
import ResponderAgent from './ResponderAgent.vue'

const route = useRoute()
const router = useRouter()
const apiBase = inject('apiBase')
const token = localStorage.getItem('token')

const md5 = route.params.md5
const analysis = ref('')
const rawAnalysis = ref('')
const sigfnTree = ref('')
const functions = ref([])
const selectedFunction = ref(null)
const detailsOpen = ref(true)
const activeTab = ref('functions')
const binaryDetails = ref(null)

const extractSigfnTree = (analysisText) => {
  if (!analysisText) return ''
  
  // Look for ```sigfn_tree blocks in the analysis
  const sigfnTreeMatch = analysisText.match(/```sigfn_tree\s*\n([\s\S]*?)\n```/i)
  if (sigfnTreeMatch) {
    return sigfnTreeMatch[1].trim()
  }
  
  return ''
}

const processedAnalysis = computed(() => {
  if (!rawAnalysis.value) return ''
  try {
    // Remove sigfn_tree code blocks from the analysis before rendering
    const withoutSigfnTree = rawAnalysis.value.replace(/```sigfn_tree\s*\n[\s\S]*?\n```/gi, '')
    const html = marked.parse(withoutSigfnTree)
    return DOMPurify.sanitize(html)
  } catch (err) {
    return `<pre>${rawAnalysis.value}</pre>`
  }
})

const renderedAnalysis = computed(() => {
  if (!rawAnalysis.value) return ''
  try {
    const html = marked.parse(rawAnalysis.value)
    return DOMPurify.sanitize(html)
  } catch (err) {
    return `<pre>${rawAnalysis.value}</pre>`
  }
})

const isInTree = (functionName) => {
  if (!sigfnTree.value) return false
  return sigfnTree.value.includes(functionName)
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const isUnIndexed = (desc) => desc && desc.startsWith('UN_IDX_')

const selectFunction = (fn) => {
  console.log('selectFunction called with:', fn)
  console.log('Type of fn:', typeof fn)
  console.log('fn.name:', fn?.name)
  console.log('Available functions:', functions.value.map(f => f.name))
  
  // If it's just a node with a name (from tree), find the full function object
  if (typeof fn === 'object' && fn.name && !fn.c_code) {
    const fullFunction = functions.value.find(f => f.name === fn.name)
    console.log('Found full function:', fullFunction)
    selectedFunction.value = fullFunction || fn
  } else {
    selectedFunction.value = fn
  }
  
  setTimeout(() => {
    const code = selectedFunction.value?.c_code || '// No code available'
    console.log('Code to show:', code.substring(0, 100))
    showCodeMirror(code)
  }, 0)
}

const showCodeMirror = (code) => {
  if (!window.CodeMirror) return
  const container = document.getElementById('codemirror-container')
  container.innerHTML = ''
  window.CodeMirror(container, {
    value: code || '// Select a function to get started',
    mode: 'clike',
    lineNumbers: true,
    readOnly: true,
    theme: 'mdn-like',
    viewportMargin: Infinity
  })
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}

onMounted(async () => {
  // Load binary details first
  const sampleResp = await fetch(`${apiBase}/samples`, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  if (sampleResp.ok) {
    const sampleData = await sampleResp.json()
    binaryDetails.value = sampleData.samples.find(s => s.md5 === md5)
    // AUTOMATION: If malicious and organiser not run, start organiser agent
    /*if (binaryDetails.value && binaryDetails.value.malicious === 'True' && ![5,6].includes(binaryDetails.value.analyze_state)) {
      try {
        await fetch(`${apiBase}/organise/${md5}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
      } catch (e) {
        // ignore errors
      }
    }*/
  }
  // Load report and sigfn_tree
  const resp = await fetch(`${apiBase}/analyze/${md5}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  if (resp.ok) {
    const data = await resp.json()
    rawAnalysis.value = data.analysis
    // Extract sigfn_tree from the analysis text
    const extractedTree = extractSigfnTree(data.analysis)
    if (extractedTree) {
      sigfnTree.value = extractedTree
    } else if (data.sigfn_tree) {
      // Fallback to backend-provided sigfn_tree
      sigfnTree.value = data.sigfn_tree
    }
  }
  // Load all functions
  const fnResp = await fetch(`${apiBase}/functions/${md5}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  if (fnResp.ok) {
    const data = await fnResp.json()
    functions.value = data.functions
  }
  // codemirror is already loaded from CDN.
  showCodeMirror('// Select a function to get started')
})
</script>

<style>
/* Scoped styles */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Enhanced Markdown styling with sensible defaults */
.prose {
  color: #374151;
  line-height: 1.75;
  font-size: 1rem;
  max-width: 100%;
}

/* CodeMirror styling */
#codemirror-container .CodeMirror {
  height: 100%;
  border: none;
  font-family: 'Fira Code', 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.4;
}

#codemirror-container .CodeMirror-scroll {
  padding: 0;
}

#codemirror-container .CodeMirror-lines {
  padding: 8px 0;
}

#codemirror-container .CodeMirror-line {
  padding: 0 8px;
}

.prose h1 {
  font-size: 1.8rem;
  font-weight: 700;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
  color: #111827;
}

.prose h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: #1f2937;
}

.prose h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.75rem;
  color: #374151;
}

.prose p, .prose ul, .prose ol {
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
}

.prose ul, .prose ol {
  padding-left: 1.5rem;
}

.prose ul {
  list-style-type: disc;
}

.prose ol {
  list-style-type: decimal;
}

.prose li {
  margin-top: 0.25rem;
  margin-bottom: 0.25rem;
}

.prose a {
  color: #2563eb;
  text-decoration: underline;
  font-weight: 500;
}

.prose a:hover {
  color: #1d4ed8;
}

.prose blockquote {
  border-left: 4px solid #e5e7eb;
  padding-left: 1rem;
  color: #6b7280;
  font-style: italic;
  margin: 1rem 0;
}

.prose pre {
  background-color: #f3f4f6;
  padding: 1rem;
  border-radius: 0.375rem;
  overflow-x: auto;
  margin: 1rem 0;
  box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
  font-size: 0.875rem;
}

.prose code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.875em;
  background-color: #f3f4f6;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
}

.prose pre code {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
}

.prose table {
  width: 100%;
  margin: 1.5rem 0;
  border-collapse: collapse;
  overflow-x: auto;
  display: block;
}

.prose thead {
  background-color: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}

.prose th {
  font-weight: 600;
  padding: 0.75rem 1rem;
  text-align: left;
  color: #111827;
}

.prose td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.prose tbody tr:nth-child(even) {
  background-color: #f9fafb;
}

.prose hr {
  border: 0;
  border-top: 1px solid #e5e7eb;
  margin: 2rem 0;
}

.prose strong {
  font-weight: 600;
  color: #111827;
}

.prose em {
  font-style: italic;
}
</style>
