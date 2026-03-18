<template>
  <div class="flex flex-col h-full w-full min-h-0">
    <!-- Error Banner -->
    <div v-if="renderError" aria-live="assertive" role="alert" class="mb-3 p-3 bg-red-900/50 border border-red-500 rounded-lg flex items-start gap-2">
      <ExclamationCircleIcon class="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div class="flex-grow">
        <p class="text-red-200 text-sm">{{ renderError }}</p>
        <button
          @click="renderError = null"
          class="text-red-300 hover:text-red-100 text-sm underline mt-1"
          aria-label="Dismiss error"
        >
          Dismiss
        </button>
      </div>
    </div>

    <!-- Diagram type selector -->
    <div class="flex items-center gap-2 mb-2 flex-shrink-0">
      <label class="text-xs text-gray-400">Type:</label>
      <select
        v-model="diagramType"
        class="text-xs bg-gray-800 border border-gray-700 rounded px-2 py-1 text-gray-300 focus:outline-none focus:border-blue-500"
      >
        <option value="technical">Technical (Python)</option>
        <option value="mermaid">Mermaid</option>
      </select>
    </div>

    <!-- Code editor -->
    <div class="flex-grow min-h-0 relative">
      <textarea
        ref="codeEditor"
        v-model="code"
        class="w-full h-full p-3 bg-gray-900 text-gray-200 font-mono text-sm border border-gray-700 rounded-lg resize-none focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-400"
        :placeholder="diagramType === 'mermaid'
          ? 'Enter your Mermaid diagram code here...\n\nflowchart TD\n    A[Start] --> B[Process]\n    B --> C[End]'
          : 'Enter your Python diagram code here...\n\nwith Diagram(\"My Diagram\"):\n    ...'"
        spellcheck="false"
        :disabled="rendering"
      ></textarea>
    </div>

    <!-- No source code hint -->
    <div v-if="!code && !hasSourceCode" class="text-center py-3">
      <p class="text-xs text-gray-500">Select a version with source code, or start writing from scratch.</p>
    </div>

    <!-- Render button -->
    <div class="mt-3 flex-shrink-0">
      <button
        @click="handleRender"
        :disabled="rendering || !code.trim() || !diagram"
        class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 text-sm font-medium"
      >
        <template v-if="rendering">
          <span class="typing-dot" style="animation-delay: 0ms"></span>
          <span class="typing-dot" style="animation-delay: 160ms"></span>
          <span class="typing-dot" style="animation-delay: 320ms"></span>
          Rendering...
        </template>
        <template v-else>
          <PlayIcon class="h-4 w-4" />
          Render Diagram
        </template>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { ExclamationCircleIcon, PlayIcon } from '@heroicons/vue/24/outline';
import { renderCode } from '../lib/api';

const props = defineProps({
  diagram: Object,
  selectedVersion: Object,
});

const emit = defineEmits(['diagram-updated']);

const code = ref('');
const diagramType = ref('technical');
const rendering = ref(false);
const renderError = ref(null);
const codeEditor = ref(null);

const hasSourceCode = computed(() => {
  return !!(props.selectedVersion?.source_code);
});

// Load source code when selected version changes
watch(() => props.selectedVersion, (version) => {
  if (version?.source_code) {
    code.value = version.source_code;
    diagramType.value = version.diagram_type || 'technical';
  }
}, { immediate: true });

const handleRender = async () => {
  if (!code.value.trim() || rendering.value || !props.diagram) return;

  rendering.value = true;
  renderError.value = null;

  try {
    await renderCode(props.diagram.id, code.value, diagramType.value);
    emit('diagram-updated', props.diagram.id);
  } catch (error) {
    if (error.response) {
      const status = error.response.status;
      const errorDetail = error.response.data?.detail || error.response.data?.error;

      if (status === 429) {
        renderError.value = "Rate limit reached. Please wait before rendering again.";
      } else if (status === 400) {
        renderError.value = errorDetail || "Invalid code. Please check your syntax.";
      } else if (status >= 500) {
        renderError.value = "Server error occurred. Please try again later.";
      } else {
        renderError.value = errorDetail || "Failed to render diagram. Please try again.";
      }
    } else if (error.request) {
      if (!navigator.onLine) {
        renderError.value = "No internet connection. Please check your network.";
      } else {
        renderError.value = "Network timeout. Please check your connection.";
      }
    } else {
      renderError.value = "An unexpected error occurred. Please try again.";
    }
    console.error("Error rendering diagram:", error);
  } finally {
    rendering.value = false;
  }
};
</script>

<style scoped>
.typing-dot {
  display: inline-block;
  width: 0.375rem;
  height: 0.375rem;
  border-radius: 9999px;
  @apply bg-white;
  opacity: 0.3;
  animation: typing-pulse 1.2s ease-in-out infinite;
}

@keyframes typing-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
</style>
