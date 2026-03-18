<template>
  <div class="flex flex-col h-full w-full min-h-0">
    <!-- Error Banner -->
    <div v-if="generationError" aria-live="assertive" role="alert" class="mb-3 p-3 bg-red-900/50 border border-red-500 rounded-lg flex items-start gap-2">
      <ExclamationCircleIcon class="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div class="flex-grow">
        <p class="text-red-200 text-sm">{{ generationError }}</p>
        <button
          @click="generationError = null"
          class="text-red-300 hover:text-red-100 text-sm underline mt-1"
          aria-label="Dismiss error"
        >
          Dismiss
        </button>
      </div>
    </div>

    <!-- Branched from banner -->
    <div v-if="parentCheckpointName" class="mb-2 px-3 py-1.5 bg-blue-900/30 border border-blue-500/30 rounded-lg text-xs text-blue-300 flex items-center gap-1.5">
      <ArrowUturnLeftIcon class="h-3.5 w-3.5" aria-hidden="true" />
      Branched from: <span class="font-medium">{{ parentCheckpointName }}</span>
    </div>

    <div class="flex-grow overflow-y-auto p-2 md:p-4 bg-gray-800 rounded-lg" ref="chatHistoryContainer">
      <div class="flex flex-col space-y-3">
        <div
          v-for="(message, index) in localChatHistory"
          :key="message.id"
          :class="message.role === 'user' ? 'flex justify-end' : 'flex justify-start'"
        >
          <!-- User message -->
          <div
            v-if="message.role === 'user'"
            class="max-w-[85%] px-3 py-2 text-sm leading-relaxed break-words bg-gray-700 text-white rounded-lg rounded-br-sm"
          >
            {{ formatMessageContent(message.content) }}
          </div>

          <!-- Assistant message -->
          <div
            v-else
            :class="[
              'max-w-[88%] px-3 py-2 text-sm leading-relaxed break-words rounded-r-lg rounded-tl-lg border-l-2 transition-colors duration-150 cursor-pointer focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-400',
              isSelected(message, index)
                ? 'bg-blue-600/20 border-blue-400 text-gray-100'
                : 'bg-gray-900/40 border-blue-500/25 text-gray-300 hover:bg-blue-500/8 hover:border-blue-400/50'
            ]"
            role="button"
            tabindex="0"
            :aria-label="`View diagram version: ${formatMessageContent(message.content)}`"
            :aria-pressed="isSelected(message, index)"
            @click="handleMessageClick(message, index)"
            @keydown.enter.prevent="handleMessageClick(message, index)"
            @keydown.space.prevent="handleMessageClick(message, index)"
          >
            <div class="flex items-start justify-between gap-2">
              <span>{{ formatMessageContent(message.content) }}</span>
              <!-- Checkpoint badge -->
              <CheckpointBadge
                v-if="getCheckpointForMessage(message, index)"
                :name="getCheckpointForMessage(message, index)"
              />
            </div>
            <div class="mt-1.5 flex items-center justify-between">
              <span :class="['flex items-center gap-1 text-xs transition-colors', isSelected(message, index) ? 'text-blue-300' : 'text-gray-500']">
                <EyeIcon class="h-3 w-3" aria-hidden="true" />
                {{ isSelected(message, index) ? 'Previewing this version' : 'View this diagram' }}
              </span>
              <button
                v-if="isSelected(message, index) && getVersionForMessage(message, index)"
                @click.stop="$emit('tag-version', getVersionForMessage(message, index))"
                class="flex items-center gap-1 text-xs text-gray-500 hover:text-blue-300 transition-colors"
                title="Tag as checkpoint"
              >
                <TagIcon class="h-3 w-3" />
                Tag
              </button>
            </div>
          </div>
        </div>

        <!-- Generating indicator -->
        <div v-if="generating" class="flex justify-start" aria-live="polite" aria-busy="true" aria-label="Generating diagram…">
          <div class="px-3 py-2.5 rounded-r-lg rounded-tl-lg border-l-2 border-blue-500/30 bg-gray-900/40 flex items-center gap-1.5">
            <span class="typing-dot" style="animation-delay: 0ms"></span>
            <span class="typing-dot" style="animation-delay: 160ms"></span>
            <span class="typing-dot" style="animation-delay: 320ms"></span>
          </div>
        </div>
      </div>
    </div>

    <form @submit.prevent="submitPrompt" class="mt-4 flex flex-shrink-0">
      <textarea
        ref="promptTextarea"
        v-model="prompt"
        @keydown.enter="handleEnter"
        placeholder="Describe your idea here..."
        aria-label="Diagram prompt"
        class="flex-grow p-2.5 sm:p-2 bg-gray-800 rounded-l-lg border border-r-0 border-gray-700 focus-visible:outline-none focus-visible:border-blue-500 resize-none h-10 overflow-hidden focus-visible:ring-2 focus-visible:ring-blue-400 transition-colors text-base"
        :disabled="generating"
        rows="1"
      ></textarea>
      <button
        type="submit"
        class="flex items-center justify-center px-3 py-2 sm:px-4 bg-gray-700 text-white rounded-r-lg border border-gray-700 hover:bg-gray-600 transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 focus-visible:ring-blue-400"
        :disabled="generating || !prompt.trim()"
        aria-label="Send prompt"
      >
        <PaperAirplaneIcon class="h-5 w-5 sm:h-6 sm:w-6" />
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue';
import { ExclamationCircleIcon, PaperAirplaneIcon, EyeIcon, TagIcon, ArrowUturnLeftIcon } from '@heroicons/vue/24/outline';
import { createDiagramVersion, createDiagram } from '../lib/api';
import CheckpointBadge from './CheckpointBadge.vue';

const props = defineProps({
  diagram: Object,
  selectedVersionId: [String, Number],
});

const emit = defineEmits(['diagram-updated', 'diagram-created', 'version-selected', 'tag-version']);

const prompt = ref('');
const generating = ref(false);
const generationError = ref(null);
const chatHistoryContainer = ref(null);
const promptTextarea = ref(null);
const localChatHistory = ref([]);

const parentCheckpointName = computed(() => {
  return props.diagram?.active_session?.parent_checkpoint_name || null;
});

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
  if (promptTextarea.value) {
    promptTextarea.value.style.height = 'auto';
    promptTextarea.value.style.height = promptTextarea.value.scrollHeight + 'px';
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

const getVersionForMessage = (message, index) => {
  if (message.role !== 'assistant' || !props.diagram?.versions) return null;
  const versionIndex = (localChatHistory.value.length - 1 - index) / 2;
  if (versionIndex >= 0 && versionIndex < props.diagram.versions.length) {
    return props.diagram.versions[versionIndex];
  }
  return null;
};

const getCheckpointForMessage = (message, index) => {
  const version = getVersionForMessage(message, index);
  return version?.checkpoint_name || null;
};

const handleMessageClick = (message, index) => {
  if (message.role !== 'assistant' || !props.diagram || !props.diagram.versions) return;

  const version = getVersionForMessage(message, index);
  if (version) {
    emit('version-selected', version);
  }
};

const isSelected = (message, index) => {
  if (message.role !== 'assistant' || !props.selectedVersionId || !props.diagram || !props.diagram.versions) {
    return false;
  }

  const versionIndex = props.diagram.versions.findIndex(v => v.id === props.selectedVersionId);
  if (versionIndex === -1) return false;

  // Map version index back to chat index: each version corresponds to a user/assistant pair (* 2)
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

<style scoped>
.typing-dot {
  display: block;
  width: 0.375rem;  /* 6px */
  height: 0.375rem;
  border-radius: 9999px;
  @apply bg-blue-400;
  opacity: 0.3;
  animation: typing-pulse 1.2s ease-in-out infinite;
  will-change: opacity;
}

@keyframes typing-pulse {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 1;
  }
}
</style>
