<template>
  <div class="flex flex-col h-full w-full">
    <p v-if="!diagram">Enter a prompt below to create your first diagram.</p>

    <!-- Error Banner -->
    <div v-if="generationError" class="mb-3 p-3 bg-red-900/50 border border-red-500 rounded-lg flex items-start gap-2">
      <ExclamationCircleIcon class="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
      <div class="flex-grow">
        <p class="text-red-200 text-sm">{{ generationError }}</p>
        <button
          @click="generationError = null"
          class="text-red-300 hover:text-red-100 text-xs underline mt-1"
        >
          Dismiss
        </button>
      </div>
    </div>

    <div class="flex-grow overflow-y-auto p-2 md:p-4 bg-gray-800 rounded-lg" ref="chatHistoryContainer">
      <div class="flex flex-col space-y-2">
        <div
          v-for="(message, index) in localChatHistory"
          :key="message.id"
          :class="[
            'p-2 rounded-lg relative w-full',
            message.role === 'user' ? 'bg-gray-700' : 'bg-blue-800',
            message.role === 'assistant' ? 'cursor-pointer hover:bg-blue-700' : '',
            isSelected(message, index) ? 'border-2 border-blue-500' : ''
          ]"
          @click="handleMessageClick(message, index)"
        >
          <span>{{ message.role === 'user' ? 'You' : 'AI' }}: {{ formatMessageContent(message.content) }}</span>
          <div v-if="isSelected(message, index)" class="text-xs text-right text-blue-300 mt-1">
            current
          </div>
        </div>
        <div v-if="generating" class="p-2 bg-blue-800 rounded-lg self-start animate-pulse">
          AI: Generating diagram...
        </div>
      </div>
    </div>

    <form @submit.prevent="submitPrompt" class="mt-4 flex">
      <textarea
        v-model="prompt"
        @keydown.enter="handleEnter"
        placeholder="Enter your prompt to generate a diagram..."
        class="flex-grow p-2 bg-gray-800 rounded-l-lg border border-gray-700 focus:outline-none focus:border-blue-500 resize-none h-10 overflow-hidden"
        :disabled="generating"
        rows="1"
      ></textarea>
      <button
        type="submit"
        class="flex items-center justify-center px-3 py-2 bg-gray-700 text-white rounded-r-lg hover:bg-gray-600 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white"
        :disabled="generating || !prompt.trim()"
        aria-label="Send prompt"
        title="Send prompt"
      >
        <PaperAirplaneIcon class="h-6 w-6" />
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue';
import { ExclamationCircleIcon, PaperAirplaneIcon } from '@heroicons/vue/24/outline';
import { createDiagramVersion, createDiagram } from '../lib/api';

const props = defineProps({
  diagram: Object,
  selectedVersionId: [String, Number],
});

const emit = defineEmits(['diagram-updated', 'diagram-created', 'version-selected']);

const prompt = ref('');
const generating = ref(false);
const generationError = ref(null);
const chatHistoryContainer = ref(null);
const localChatHistory = ref([]);

const scrollToBottom = () => {
  nextTick(() => {
    if (chatHistoryContainer.value) {
      chatHistoryContainer.value.scrollTop = chatHistoryContainer.value.scrollHeight;
    }
  });
};

watch(() => props.diagram ? props.diagram.chat_history : [], (newHistory) => {
  localChatHistory.value = [...newHistory];
  scrollToBottom();
}, { deep: true, immediate: true });

watch(prompt, () => {
  const textarea = chatHistoryContainer.value?.nextElementSibling?.querySelector('textarea');
  if (textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
  }
});

const handleEnter = (event) => {
  if (event.shiftKey) return;
  event.preventDefault();
  submitPrompt();
};

const formatMessageContent = (content) => {
  try {
    const parsedContent = JSON.parse(content);
    if (parsedContent && parsedContent.diagram_title) {
      return `Generated diagram: "${parsedContent.diagram_title}".`;
    }
  } catch (e) { /* Not JSON */ }
  return content;
};

const handleMessageClick = (message, index) => {
  if (message.role !== 'assistant' || !props.diagram || !props.diagram.versions) return;

  // Algorithm: Find the corresponding version based on the message's index.
  const versionIndex = (localChatHistory.value.length - 1 - index) / 2;

  if (versionIndex >= 0 && versionIndex < props.diagram.versions.length) {
    const selectedVersion = props.diagram.versions[versionIndex];
    if (selectedVersion) {
      emit('version-selected', selectedVersion);
    }
  }
};

const isSelected = (message, index) => {
  if (message.role !== 'assistant' || !props.selectedVersionId || !props.diagram || !props.diagram.versions) {
    return false;
  }

  // Algorithm: Find the version index for the currently selected ID.
  const versionIndex = props.diagram.versions.findIndex(v => v.id === props.selectedVersionId);
  if (versionIndex === -1) return false;

  // Find the chat index that corresponds to this version.
  const expectedChatIndex = localChatHistory.value.length - 1 - (versionIndex * 2);
  
  return index === expectedChatIndex;
};

const submitPrompt = async () => {
  if (!prompt.value.trim() || generating.value) return;

  generating.value = true;
  const currentPrompt = prompt.value;

  localChatHistory.value.push({
    id: Date.now(),
    role: 'user',
    content: currentPrompt,
    created_at: new Date().toISOString(),
  });
  scrollToBottom();
  prompt.value = '';

  try {
    generationError.value = null; // Clear any previous errors

    if (props.diagram && props.diagram.id) {
      await createDiagramVersion(props.diagram.id, currentPrompt);
      emit('diagram-updated', props.diagram.id);
    } else {
      const response = await createDiagram(currentPrompt);
      emit('diagram-created', response.data);
    }
  } catch (error) {
    // Comprehensive error handling
    localChatHistory.value.pop();
    prompt.value = currentPrompt;

    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const errorDetail = error.response.data?.detail || error.response.data?.error;

      if (status === 429) {
        generationError.value = "Rate limit reached. Please wait before generating another diagram.";
      } else if (status === 401) {
        generationError.value = "Your session has expired. Please log in again.";
      } else if (status === 400) {
        generationError.value = errorDetail || "Invalid request. Please check your input and try again.";
      } else if (status >= 500) {
        generationError.value = "Server error occurred. Please try again later.";
      } else {
        generationError.value = errorDetail || "Failed to generate diagram. Please try again.";
      }
    } else if (error.request) {
      // Request made but no response (network error)
      if (!navigator.onLine) {
        generationError.value = "No internet connection. Please check your network and try again.";
      } else {
        generationError.value = "Network timeout. Please check your connection and try again.";
      }
    } else {
      // Something else went wrong
      generationError.value = "An unexpected error occurred. Please try again.";
    }

    console.error("Error generating diagram:", error);
  } finally {
    generating.value = false;
  }
};
</script>