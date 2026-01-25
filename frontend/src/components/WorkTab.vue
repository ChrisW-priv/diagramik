<template>
  <div class="flex flex-col h-full w-full">
    <p v-if="!diagram">Enter a prompt below to create your first diagram.</p>
    <div class="flex-grow overflow-y-auto p-4 bg-gray-800 rounded-lg" ref="chatHistoryContainer">
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
        class="px-3 py-2 bg-gray-700 text-white rounded-r-lg hover:bg-gray-600 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white"
        :disabled="generating || !prompt.trim()"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue';
import { createDiagramVersion, createDiagram } from '../lib/api';

const props = defineProps({
  diagram: Object,
  selectedVersionId: [String, Number],
});

const emit = defineEmits(['diagram-updated', 'diagram-created', 'version-selected']);

const prompt = ref('');
const generating = ref(false);
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
    if (props.diagram && props.diagram.id) {
      await createDiagramVersion(props.diagram.id, currentPrompt);
      emit('diagram-updated', props.diagram.id);
    } else {
      const response = await createDiagram(currentPrompt);
      emit('diagram-created', response.data);
    }
  } catch (error) {
    console.error("Error generating diagram:", error);
    localChatHistory.value.pop();
    prompt.value = currentPrompt;
  } finally {
    generating.value = false;
  }
};
</script>