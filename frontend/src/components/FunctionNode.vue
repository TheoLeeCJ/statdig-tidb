<template>
  <div>
    <details v-if="node.children && node.children.length > 0" open class="mb-1">
      <summary class="cursor-pointer select-none flex items-center gap-2 text-gray-800 hover:bg-gray-100 rounded px-2 py-1">
        <span class="material-symbols-outlined text-blue-500 text-base folder-icon"></span>
        <span class="font-semibold truncate">{{ node.name }}</span>
        <span v-if="node.comment" class="text-gray-500 text-xs truncate ml-1">{{ node.comment }}</span>
      </summary>
      <div class="ml-4 mt-1 space-y-1 border-l border-gray-300 pl-2">
        <!-- Virtual "view code" entry for parent function -->
        <div class="flex items-center gap-2 px-2 py-1 rounded hover:bg-blue-50 transition-colors text-blue-600 cursor-pointer text-sm" 
             @click="handleViewCode">
          <span class="material-symbols-outlined text-blue-500 text-base">code</span>
          <span class="italic">view code for {{ node.name }}</span>
        </div>
        
        <!-- Child nodes -->
        <FunctionNode 
          v-for="(child, index) in node.children" 
          :key="child.name + '-' + index" 
          :node="child" 
          @select="$emit('select', $event)" 
        />
      </div>
    </details>
    <div v-else class="flex items-center gap-2 px-2 py-1 rounded hover:bg-gray-100 transition-colors text-gray-700 cursor-pointer" @click="handleClick">
      <span class="material-symbols-outlined text-green-500 text-base">code_blocks</span>
      <span class="font-semibold truncate">{{ node.name }}</span>
      <span v-if="node.comment" class="text-gray-500 text-xs truncate ml-1">{{ node.comment }}</span>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

// Define component name for self-reference
defineOptions({
  name: 'FunctionNode'
})

const props = defineProps({
  node: { type: Object, required: true }
})

const emit = defineEmits(['select'])

const handleClick = () => {
  emit('select', props.node)
}

const handleViewCode = () => {
  emit('select', props.node)
}
</script>

<style scoped>
/* Custom styling for details/summary to look like folder icons */
details > summary {
  list-style: none;
}

details > summary::-webkit-details-marker {
  display: none;
}

details[open] > summary .folder-icon:before {
  content: 'folder_open';
}

details:not([open]) > summary .folder-icon:before {
  content: 'folder';
}

.folder-icon {
  transition: all 0.2s ease;
}
</style>