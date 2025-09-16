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
          </div>
          <div class="flex items-center space-x-4">
            <router-link 
              to="/supersearch" 
              class="flex items-center space-x-1 bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-2 rounded-lg shadow hover:from-blue-600 hover:to-purple-600 transition-colors font-semibold"
            >
              <span class="material-symbols-outlined text-lg">search</span>
              <span class="text-base">SuperSearch</span>
            </router-link>
            <div class="flex items-center space-x-2 text-sm text-gray-600">
              <span class="material-symbols-outlined text-lg">person</span>
              <span>{{ user?.username }}</span>
              <span v-if="user?.role === 'admin'" class="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                Admin
              </span>
            </div>
            <button
              @click="logout"
              class="flex items-center space-x-1 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <span class="material-symbols-outlined text-lg">logout</span>
              <span class="text-sm">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>
    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <!-- SuperSearch Bar -->
      <div class="mb-8">
        <div class="flex items-center justify-center mb-4">
          <button @click="goToSuperSearch" class="w-full max-w-2xl flex items-center px-6 py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl shadow-lg hover:from-blue-600 hover:to-purple-600 transition-colors text-lg font-semibold gap-3">
            <span class="material-symbols-outlined text-2xl">search</span>
            <span>Try Intelligent SuperSearch</span>
          </button>
        </div>
      </div>
      <!-- Upload Section -->
      <div class="mb-8">
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span class="material-symbols-outlined mr-2">cloud_upload</span>
            Upload Files
          </h2>
          <div
            @drop="handleDrop"
            @dragover.prevent
            @dragenter.prevent
            class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors"
            :class="{ 'border-blue-400 bg-blue-50': dragActive }"
          >
            <div class="space-y-4">
              <div class="mx-auto h-16 w-16 bg-gray-100 rounded-full flex items-center justify-center">
                <span class="material-symbols-outlined text-gray-400 text-2xl">upload_file</span>
              </div>
              <div>
                <p class="text-lg font-medium text-gray-900">Drop files here or click to browse</p>
                <p class="text-sm text-gray-500 mt-1">Maximum file size: 50MB</p>
              </div>
              <input
                ref="fileInput"
                type="file"
                multiple
                @change="handleFileSelect"
                class="hidden"
              >
              <button
                @click="$refs.fileInput.click()"
                class="inline-flex items-center px-4 py-2 border border-blue-300 rounded-lg text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
              >
                <span class="material-symbols-outlined mr-2">folder_open</span>
                Select Files
              </button>
            </div>
          </div>
          <!-- Upload Queue -->
          <div v-if="uploadQueue.length > 0" class="mt-6 space-y-3">
            <h3 class="text-sm font-medium text-gray-900">Upload Queue</h3>
            <div
              v-for="upload in uploadQueue"
              :key="upload.id"
              class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div class="flex items-center space-x-3">
                <span class="material-symbols-outlined text-gray-400">description</span>
                <div>
                  <p class="text-sm font-medium text-gray-900">{{ upload.file.name }}</p>
                  <p class="text-xs text-gray-500">{{ formatFileSize(upload.file.size) }}</p>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <div v-if="upload.status === 'uploading'" class="flex items-center space-x-2">
                  <div class="w-4 h-4">
                    <span class="material-symbols-outlined animate-spin text-blue-600 text-lg">progress_activity</span>
                  </div>
                  <span class="text-xs text-gray-600">Uploading...</span>
                </div>
                <div v-else-if="upload.status === 'success'" class="flex items-center space-x-2">
                  <span class="material-symbols-outlined text-green-600 text-lg">check_circle</span>
                  <span class="text-xs text-green-600">Complete</span>
                </div>
                <div v-else-if="upload.status === 'error'" class="flex items-center space-x-2">
                  <span class="material-symbols-outlined text-red-600 text-lg">error</span>
                  <span class="text-xs text-red-600">Failed</span>
                </div>
                <button
                  v-if="upload.status === 'pending'"
                  @click="removeFromQueue(upload.id)"
                  class="text-gray-400 hover:text-red-600 transition-colors"
                >
                  <span class="material-symbols-outlined text-lg">close</span>
                </button>
              </div>
            </div>
            <button
              v-if="uploadQueue.some(u => u.status === 'pending')"
              @click="uploadFiles"
              :disabled="uploading"
              class="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center justify-center"
            >
              <span class="material-symbols-outlined mr-2">cloud_upload</span>
              Upload All Files
            </button>
          </div>
        </div>
      </div>
      <!-- Files List -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200">
        <div class="p-6 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 flex items-center">
              <span class="material-symbols-outlined mr-2">folder</span>
              Files ({{ samples.length }})
            </h2>
            <button
              @click="loadSamples"
              :disabled="loadingSamples"
              class="flex items-center space-x-1 text-blue-600 hover:text-blue-700 transition-colors"
            >
              <span class="material-symbols-outlined text-lg" :class="{ 'animate-spin': loadingSamples }">
                refresh
              </span>
              <span class="text-sm">Refresh</span>
            </button>
          </div>
        </div>
        <div v-if="loadingSamples" class="p-8 text-center">
          <span class="material-symbols-outlined animate-spin text-gray-400 text-3xl">progress_activity</span>
          <p class="text-gray-500 mt-2">Loading files...</p>
        </div>
        <div v-else-if="samples.length === 0" class="p-8 text-center">
          <span class="material-symbols-outlined text-gray-400 text-4xl">folder_open</span>
          <p class="text-gray-500 mt-2">No files uploaded yet</p>
        </div>
        <div v-else class="divide-y divide-gray-200">
          <div
            v-for="sample in samples"
            :key="sample.md5"
            class="p-4 hover:bg-gray-50 transition-colors"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span class="material-symbols-outlined text-blue-600">description</span>
                </div>
                <div>
                  <p class="text font-medium text-gray-900">{{ sample.original_filename }}</p>
                  <div class="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                    <span>{{ formatFileSize(sample.file_size) }}</span>
                    <span>{{ sample.filetype }}</span>
                    <span>{{ formatDate(sample.created_at) }}</span>
                    <span>by {{ sample.uploaded_by_username }}</span>
                    <span v-if="sample.is_public" class="text-blue-600 font-medium">Public</span>
                    <span v-else class="text-gray-400">Private</span>
                    <span v-if="sample.malicious" :class="{
                      'text-red-600 font-bold': sample.malicious === 'True',
                      'text-green-600 font-bold': sample.malicious === 'False',
                      'text-yellow-600 font-bold': sample.malicious === 'Uncertain'
                    }">
                      <span v-if="sample.malicious === 'True'">Malicious</span>
                      <span v-else-if="sample.malicious === 'False'">Benign</span>
                      <span v-else>Uncertain</span>
                    </span>
                  </div>
                  <div v-if="sample.tags" class="flex flex-wrap gap-2 mt-1">
                    <span v-for="tag in sample.tags.split(',')" :key="tag" class="bg-gray-200 text-gray-700 px-2 py-0.5 rounded text-xs">{{ tag }}</span>
                  </div>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <span class="text-sm text-gray-400 font-mono">{{ sample.md5.substring(0, 8) }}...</span>
                <!-- Extraction/Analysis State Machine -->
                <template v-if="sample.analyze_state === 0">
                  <button
                    @click="extractFunctions(sample)"
                    class="px-3 py-1 text-sm bg-blue-100 text-blue-700 hover:bg-blue-200 rounded-lg flex items-center space-x-1 transition-colors"
                  >
                    <span class="material-symbols-outlined text-sm">psychology</span>
                    <span>Full Analysis</span>
                  </button>
                </template>
                <template v-else-if="sample.analyze_state === 1">
                  <div class="flex items-center space-x-1">
                    <span class="material-symbols-outlined animate-spin text-blue-600 text-lg">progress_activity</span>
                    <span class="text-sm text-blue-600">Extracting...</span>
                  </div>
                </template>
                <template v-else-if="sample.analyze_state === 2">
                  <div class="flex items-center space-x-1">
                    <span class="material-symbols-outlined animate-spin text-purple-600 text-lg">progress_activity</span>
                    <span class="text-sm text-purple-600">Analysing...</span>
                  </div>
                </template>
                <template v-else-if="sample.analyze_state === 3">
                  <div class="flex items-center space-x-1">
                    <span class="material-symbols-outlined animate-spin text-purple-600 text-lg">progress_activity</span>
                    <span class="text-sm text-purple-600">Analysing...</span>
                  </div>
                </template>
                <template v-else-if="sample.analyze_state === 4">
                  <button
                    @click="viewAnalysis(sample)"
                    class="px-3 py-1 text-sm bg-green-100 text-green-700 hover:bg-green-200 rounded-lg flex items-center space-x-1 transition-colors"
                  >
                    <span class="material-symbols-outlined text-sm">visibility</span>
                    <span>View Report</span>
                  </button>
                </template>
                <template v-else-if="sample.analyze_state === 5">
                  <div class="flex items-center space-x-1">
                    <span class="material-symbols-outlined animate-spin text-orange-600 text-lg">progress_activity</span>
                    <span class="text-sm text-orange-600">Organizing...</span>
                  </div>
                </template>
                <template v-else-if="sample.analyze_state === 6">
                  <button
                    @click="viewAnalysis(sample)"
                    class="px-3 py-1 text-sm bg-green-100 text-green-700 hover:bg-green-200 rounded-lg flex items-center space-x-1 transition-colors"
                  >
                    <span class="material-symbols-outlined text-sm">visibility</span>
                    <span>View Report</span>
                  </button>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
    <!-- Analysis Report Modal -->
    <div v-if="showAnalysisModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="max-w-6xl w-full max-h-[90vh] overflow-hidden">
        <AnalysisReport 
          :sample="selectedSample" 
          @close="closeAnalysisModal"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const apiBase = inject('apiBase')

const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
const token = localStorage.getItem('token')

const samples = ref([])
const loadingSamples = ref(false)
const uploadQueue = ref([])
const uploading = ref(false)
const dragActive = ref(false)
const extractStatus = ref({}) // Track extraction status for each sample
const analysisStatus = ref({}) // Track analysis status for each sample
const showAnalysisModal = ref(false)
const selectedSample = ref(null)

if (!token || !user.value) {
  router.push('/login')
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleDrop = (e) => {
  e.preventDefault()
  dragActive.value = false
  const files = Array.from(e.dataTransfer.files)
  addFilesToQueue(files)
}

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  addFilesToQueue(files)
  e.target.value = ''
}

const addFilesToQueue = (files) => {
  files.forEach(file => {
    if (file.size > 50 * 1024 * 1024) {
      alert(`File ${file.name} exceeds 50MB limit`)
      return
    }
    uploadQueue.value.push({
      id: Date.now() + Math.random(),
      file,
      status: 'pending'
    })
  })
}

const removeFromQueue = (id) => {
  uploadQueue.value = uploadQueue.value.filter(upload => upload.id !== id)
}

const uploadFiles = async () => {
  uploading.value = true
  for (const upload of uploadQueue.value) {
    if (upload.status !== 'pending') continue
    upload.status = 'uploading'
    try {
      const formData = new FormData()
      formData.append('file', upload.file)
      const response = await fetch(`${apiBase}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })
      if (response.ok) {
        upload.status = 'success'
      } else {
        upload.status = 'error'
      }
    } catch (error) {
      upload.status = 'error'
    }
  }
  uploading.value = false
  loadSamples()
  // Clear successful uploads after a delay
  setTimeout(() => {
    uploadQueue.value = uploadQueue.value.filter(upload => upload.status !== 'success')
  }, 2000)
}

const extractFunctions = async (sample) => {
  // Set loading state
  extractStatus.value[sample.md5] = { loading: true }
  try {
    const response = await fetch(`${apiBase}/extract/${sample.md5}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await response.json()
    if (response.ok) {
      // Update with success state and function count
      extractStatus.value[sample.md5] = {
        loading: false,
        success: true,
        count: data.function_count
      }
    } else {
      // Update with error state
      extractStatus.value[sample.md5] = {
        loading: false,
        error: true,
        message: data.detail || 'Extraction failed'
      }
    }
    // Wait 3 seconds, then reload samples
    setTimeout(() => {
      loadSamples()
    }, 3000)
  } catch (error) {
    // Update with error state
    extractStatus.value[sample.md5] = {
      loading: false,
      error: true,
      message: 'Network error'
    }
    setTimeout(() => {
      loadSamples()
    }, 3000)
  }
}

const analyzeFunction = async (sample) => {
  // Set loading state
  analysisStatus.value[sample.md5] = { loading: true }
  try {
    const response = await fetch(`${apiBase}/analyze/${sample.md5}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await response.json()
    // Wait 3 seconds, then reload samples
    setTimeout(() => {
      loadSamples()
    }, 3000)
    if (response.ok) {
      // Update with success state
      analysisStatus.value[sample.md5] = {
        loading: false,
        success: true
      }
      // Update the sample in our local array
      const sampleIndex = samples.value.findIndex(s => s.md5 === sample.md5)
      if (sampleIndex !== -1) {
        samples.value[sampleIndex].is_analyzed = true
      }
      // Navigate to the new report page
      router.push(`/report/${sample.md5}`)
    } else {
      // Update with error state
      analysisStatus.value[sample.md5] = {
        loading: false,
        error: true,
        message: data.detail || 'Analysis failed'
      }
      alert(`Analysis failed: ${data.detail || 'Unknown error'}`)
    }
  } catch (error) {
    // Update with error state
    analysisStatus.value[sample.md5] = {
      loading: false,
      error: true,
      message: 'Network error'
    }
    alert('Network error occurred during analysis')
  }
}

const viewAnalysis = async (sample) => {
  // Navigate to the new report page
  router.push(`/report/${sample.md5}`)
}

const closeAnalysisModal = () => {
  showAnalysisModal.value = false
  selectedSample.value = null
}

let pollInterval = null

const pollSamples = () => {
  if (pollInterval) clearInterval(pollInterval)
  pollInterval = setInterval(async () => {
    await loadSamples()
    // If no samples are in progress, stop polling
    if (!samples.value.some(s => [1, 3, 5].includes(s.analyze_state))) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }, 10000)
}

const loadSamples = async () => {
  loadingSamples.value = true
  try {
    const response = await fetch(`${apiBase}/samples`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      samples.value = data.samples
      // Initialize extract status from the function counts
      for (const sample of data.samples) {
        if (sample.function_count > 0) {
          extractStatus.value[sample.md5] = {
            loading: false,
            success: true,
            count: sample.function_count
          }
        }
      }
      // If any samples are in progress, start polling
      if (samples.value.some(s => [1, 3, 5].includes(s.analyze_state))) {
        pollSamples()
      }
      // AUTOMATION: If any sample is in state 2 (functions extracted), auto-analyze
      for (const sample of samples.value) {
        if (sample.analyze_state === 2) {
          analyzeFunction(sample)
        }
      }
    }
  } catch (error) {
    console.error('Failed to load samples:', error)
  } finally {
    loadingSamples.value = false
  }
}

const goToSuperSearch = () => {
  router.push('/supersearch')
}

onMounted(() => {
  loadSamples()
})
</script>

<style>
/* Add any component-specific styles here */
</style>