<template>
  <div class="function-tree">
    <div v-if="error" class="h-full flex flex-col items-center justify-center text-red-500 border-2 border-dashed border-red-200 rounded-lg p-4">
      <div class="text-4xl mb-3">⚠</div>
      <p class="text-lg font-medium text-center">Parsing Error</p>
      <p class="mt-2 text-sm text-center max-w-md">{{ error }}</p>
      <p class="mt-3 text-xs text-gray-500">Check your tree structure format</p>
    </div>
    <div v-else-if="tree" class="space-y-1.5 min-w-0">
      <div class="tree-wrapper">
        <div v-for="(node, index) in tree.children || [tree]" :key="node.name + '-' + index">
          <FunctionNode :node="node" @select="onSelect" />
        </div>
      </div>
    </div>
    <div v-else class="text-gray-400 text-sm">No function tree available.</div>
  </div>
</template>

<script setup>
import { defineProps, ref, defineEmits, watch } from 'vue'
import FunctionNode from './FunctionNode.vue'

const props = defineProps({
  sigfnTree: { type: String, required: true }
})
const emit = defineEmits(['select'])

const tree = ref(null)
const error = ref(null)

const parseTree = (input) => {
  try {
    if (!input || !input.trim()) return null
    
    const lines = input.split('\n').filter(line => line.trim() !== '')
    const dummyRoot = { name: 'root', children: [] }
    const stack = [dummyRoot]
    const allowedPrefixes = ['│  ', '   ', '├─ ', '└─ ']

    for (const line of lines) {
      // Count indentation level by scanning 3-character chunks
      let level = 0
      let pos = 0
      while (pos + 3 <= line.length) {
        const chunk = line.substring(pos, pos + 3)
        if (allowedPrefixes.includes(chunk)) {
          level++
          pos += 3
        } else {
          break
        }
      }

      // Extract node name and comment (split by '//')
      const fullName = line.substring(pos).trim()
      if (!fullName) continue
      
      const parts = fullName.split('//')
      const name = parts[0].trim()
      const comment = parts.length > 1 ? parts[1].trim() : ''

      // Adjust stack to current level
      while (stack.length > level + 1) {
        stack.pop()
      }

      // Create new node and add to parent
      const newNode = { name, comment, children: [] }
      stack[stack.length - 1].children.push(newNode)
      stack.push(newNode)
    }

    return dummyRoot
  } catch (err) {
    throw new Error(`Parsing error: ${err.message}`)
  }
}

// Parse tree when sigfnTree changes
watch(() => props.sigfnTree, (newInput) => {
  try {
    error.value = null
    if (!newInput || newInput.trim() === '') {
      tree.value = null
      return
    }
    
    tree.value = parseTree(newInput)
  } catch (err) {
    error.value = err.message
    tree.value = null
  }
}, { immediate: true })

function onSelect(node) {
  emit('select', node)
}
</script>

<style scoped>
.function-tree {
  font-size: 0.875rem;
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace;
}

/* Custom styling for details/summary to look like folder icons */
details > summary {
  list-style: none;
}

details > summary::-webkit-details-marker {
  display: none;
}

details[open] > summary .material-symbols-outlined {
  transform: rotate(0deg);
}

details:not([open]) > summary .material-symbols-outlined {
  transform: rotate(-90deg);
}

details > summary .material-symbols-outlined {
  transition: transform 0.2s ease;
}
</style>
