<template>
  <main id="main-content" class="border border-gray-700 rounded-lg flex flex-col h-full">
    <!-- Tab buttons for small screens -->
    <div class="flex border-b border-gray-700 md:hidden" role="tablist" aria-label="Diagram panels">
      <button
        id="tab-chat"
        role="tab"
        @click="activeTab = 'chat'"
        :class="['flex flex-col items-center justify-center gap-1 flex-1 py-2.5 px-3 min-h-12', activeTab === 'chat' ? 'bg-gray-700 text-white' : 'text-gray-400', 'hover:bg-gray-700/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 transition-colors']"
        :aria-selected="activeTab === 'chat'"
        aria-controls="panel-chat"
      >
        <ChatBubbleLeftIcon class="h-5 w-5" aria-hidden="true" />
        <span class="text-xs font-medium">Chat</span>
      </button>
      <button
        id="tab-code"
        role="tab"
        @click="activeTab = 'code'"
        :class="['flex flex-col items-center justify-center gap-1 flex-1 py-2.5 px-3 min-h-12', activeTab === 'code' ? 'bg-gray-700 text-white' : 'text-gray-400', 'hover:bg-gray-700/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 transition-colors disabled:opacity-40 disabled:cursor-not-allowed']"
        :disabled="!diagram"
        :aria-selected="activeTab === 'code'"
        aria-controls="panel-code"
      >
        <CodeBracketIcon class="h-5 w-5" aria-hidden="true" />
        <span class="text-xs font-medium">Code</span>
      </button>
      <button
        id="tab-display"
        role="tab"
        @click="activeTab = 'display'"
        :class="['flex flex-col items-center justify-center gap-1 flex-1 py-2.5 px-3 min-h-12', activeTab === 'display' ? 'bg-gray-700 text-white' : 'text-gray-400', 'hover:bg-gray-700/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 transition-colors disabled:opacity-40 disabled:cursor-not-allowed']"
        :disabled="!diagram"
        :aria-disabled="!diagram"
        :aria-selected="activeTab === 'display'"
        aria-controls="panel-display"
      >
        <EyeIcon class="h-5 w-5" aria-hidden="true" />
        <span class="text-xs font-medium">Preview</span>
      </button>
    </div>

    <div class="p-2 md:p-4 flex-grow flex flex-col min-h-0">
      <div v-if="loading" aria-live="polite" aria-busy="true" class="flex flex-col gap-4 flex-grow min-h-0 animate-pulse">
        <div class="flex-1 bg-gray-800 rounded-lg"></div>
      </div>
      <p v-else-if="error" aria-live="assertive" role="alert" class="text-red-400 bg-red-500/10 border border-red-500 rounded px-3 py-2">{{ error }}</p>
      <div v-else class="flex flex-col flex-grow min-h-0">
        <!-- Responsive layout -->
        <div class="flex flex-col md:flex-row flex-grow min-h-0" ref="containerRef">
          <!-- Left panel: Chat/Code tabs (desktop has sub-tabs) -->
          <div :class="['w-full flex-col min-h-0', (activeTab === 'chat' || activeTab === 'code') ? 'block' : 'hidden', 'md:flex']" :style="isDesktop ? { width: `calc(${leftPanelWidth}% - 0.5rem)` } : {}">
            <!-- Desktop sub-tab toggle -->
            <div class="hidden md:flex mb-2 bg-gray-800 rounded-lg p-0.5 flex-shrink-0">
              <button
                @click="leftSubTab = 'chat'"
                :class="['flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors', leftSubTab === 'chat' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-300']"
              >
                <ChatBubbleLeftIcon class="h-3.5 w-3.5" />
                Chat
              </button>
              <button
                @click="leftSubTab = 'code'"
                :disabled="!diagram"
                :class="['flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors', leftSubTab === 'code' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-300', !diagram && 'opacity-40 cursor-not-allowed']"
              >
                <CodeBracketIcon class="h-3.5 w-3.5" />
                Code
              </button>
            </div>

            <!-- Chat panel -->
            <div v-show="currentLeftPanel === 'chat'" class="flex flex-col min-h-0 flex-grow">
              <ChatTab
                :diagram="diagram"
                :selected-version-id="selectedVersionId"
                @diagram-updated="fetchDiagram"
                @diagram-created="handleDiagramCreated"
                @version-selected="handleVersionSelected"
                @tag-version="handleTagVersion"
              />
            </div>

            <!-- Code panel -->
            <div v-show="currentLeftPanel === 'code'" class="flex flex-col min-h-0 flex-grow">
              <EditTab
                :diagram="diagram"
                :selected-version="selectedVersion"
                @diagram-updated="fetchDiagram"
              />
            </div>
          </div>

          <!-- Resizer -->
          <div
            class="hidden md:flex items-center cursor-col-resize px-1"
            @mousedown="startResize"
            @keydown="handleResizerKeydown"
            role="slider"
            :aria-valuenow="leftPanelWidth"
            aria-valuemin="15"
            aria-valuemax="85"
            aria-label="Resize panels divider"
            tabindex="0"
          >
            <div class="w-1.5 h-full bg-gray-600 rounded-full hover:bg-blue-500 focus-visible:bg-blue-500 transition-colors"></div>
          </div>

          <!-- DisplayTab -->
          <div id="panel-display" role="tabpanel" aria-labelledby="tab-display" :class="['w-full flex-col min-h-0', activeTab === 'display' ? 'block' : 'hidden', 'md:flex']" :style="isDesktop ? { width: `calc(${displayPanelWidth}% - 0.5rem)` } : {}">
            <DisplayTab :diagram="diagram" :selected-version="selectedVersion" />
          </div>

          <!-- Checkpoint sidebar toggle (desktop) -->
          <button
            v-if="diagram && !checkpointSidebarOpen"
            @click="checkpointSidebarOpen = true"
            class="hidden md:flex items-center justify-center w-8 bg-gray-800 hover:bg-gray-700 border-l border-gray-700 transition-colors"
            title="Show checkpoints"
          >
            <TagIcon class="h-4 w-4 text-amber-400" />
          </button>

          <!-- Checkpoint sidebar -->
          <div v-if="checkpointSidebarOpen && diagram" class="hidden md:flex flex-col w-56 border-l border-gray-700 bg-gray-900 min-h-0 flex-shrink-0">
            <CheckpointSidebar
              :checkpoints="diagram.checkpoints"
              :diagram-id="diagram.id"
              @close="checkpointSidebarOpen = false"
              @view-checkpoint="handleViewCheckpoint"
              @delete-checkpoint="handleDeleteCheckpoint"
              @branched="fetchDiagram(diagram.id)"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Create Checkpoint Modal -->
    <CreateCheckpointModal
      :show="showCheckpointModal"
      :diagram-id="diagram?.id"
      :version-id="tagTargetVersionId"
      @close="showCheckpointModal = false"
      @created="handleCheckpointCreated"
    />
  </main>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { ChatBubbleLeftIcon, CodeBracketIcon, EyeIcon, TagIcon } from '@heroicons/vue/24/outline';
import ChatTab from './ChatTab.vue';
import EditTab from './EditTab.vue';
import DisplayTab from './DisplayTab.vue';
import CheckpointSidebar from './CheckpointSidebar.vue';
import CreateCheckpointModal from './CreateCheckpointModal.vue';
import { getDiagram, deleteCheckpoint } from '../lib/api';
import { CONFIG } from '../lib/config';

const props = defineProps({
  id: String,
});

const activeTab = ref('chat');
const leftSubTab = ref('chat');
const diagram = ref(null);
const loading = ref(true);
const error = ref(null);
const selectedVersionId = ref(null);
const isResizing = ref(false);
const leftPanelWidth = ref(25);
const containerRef = ref(null);
const isDesktop = ref(typeof window !== 'undefined' && window.innerWidth >= 768);
const checkpointSidebarOpen = ref(false);
const showCheckpointModal = ref(false);
const tagTargetVersionId = ref(null);

// On desktop, left sub-tab controls which panel is shown
// On mobile, activeTab controls it directly
const currentLeftPanel = computed(() => {
  if (isDesktop.value) return leftSubTab.value;
  return activeTab.value === 'code' ? 'code' : 'chat';
});

const displayPanelWidth = computed(() => {
  const sidebarWidth = checkpointSidebarOpen.value ? 0 : 0; // sidebar is fixed width, doesn't affect calc
  return 100 - leftPanelWidth.value - sidebarWidth;
});

const selectedVersion = computed(() => {
  if (!diagram.value || !selectedVersionId.value) {
    return null;
  }
  return diagram.value.versions.find(v => v.id === selectedVersionId.value);
});

const startResize = (event) => {
  event.preventDefault();
  isResizing.value = true;
  document.addEventListener('mousemove', resize);
  document.addEventListener('mouseup', stopResize);
};

const resize = (event) => {
  if (isResizing.value && containerRef.value) {
    const containerRect = containerRef.value.getBoundingClientRect();
    const newWidth = ((event.clientX - containerRect.left) / containerRect.width) * 100;
    if (newWidth > 15 && newWidth < 85) {
      leftPanelWidth.value = newWidth;
    }
  }
};

const stopResize = () => {
  isResizing.value = false;
  document.removeEventListener('mousemove', resize);
  document.removeEventListener('mouseup', stopResize);
};

let resizeTimer = null;
const updateScreenSize = () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    isDesktop.value = window.innerWidth >= 768;
  }, CONFIG.TIMERS.DEBOUNCE_RESIZE);
};

const handleKeyDown = (event) => {
  if (event.altKey && event.key === 'Tab') {
    event.preventDefault();
    if (isDesktop.value) {
      // Cycle through: chat -> code -> display
      // (display doesn't apply on desktop since both are visible)
      leftSubTab.value = leftSubTab.value === 'chat' ? 'code' : 'chat';
    } else {
      const tabs = ['chat', 'code', 'display'];
      const currentIdx = tabs.indexOf(activeTab.value);
      activeTab.value = tabs[(currentIdx + 1) % tabs.length];
    }
  }
};

const handleResizerKeydown = (event) => {
  if (event.key === 'ArrowLeft') {
    event.preventDefault();
    const step = event.shiftKey ? 10 : 5;
    leftPanelWidth.value = Math.max(15, leftPanelWidth.value - step);
  } else if (event.key === 'ArrowRight') {
    event.preventDefault();
    const step = event.shiftKey ? 10 : 5;
    leftPanelWidth.value = Math.min(85, leftPanelWidth.value + step);
  }
};

const fetchDiagram = async (diagramId) => {
  if (!diagramId) {
    loading.value = false;
    return;
  }
  loading.value = true;
  error.value = null;
  try {
    const response = await getDiagram(diagramId);
    diagram.value = response.data;
    if (diagram.value && diagram.value.versions && diagram.value.versions.length > 0) {
      diagram.value.versions.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

      const urlParams = new URLSearchParams(window.location.search);
      const versionIdFromUrl = urlParams.get('version');

      if (versionIdFromUrl && diagram.value.versions.some(v => v.id === versionIdFromUrl)) {
        selectedVersionId.value = versionIdFromUrl;
      } else {
        selectedVersionId.value = diagram.value.versions[0].id;
      }
    }
  } catch (err) {
    if (err.response) {
      const status = err.response.status;

      if (status === 404) {
        error.value = 'Diagram not found. It may have been deleted.';
      } else if (status === 403) {
        error.value = 'Access denied. You may not have permission to view this diagram.';
      } else if (status >= 500) {
        error.value = 'Server error occurred. Please try again later.';
      } else {
        error.value = 'Failed to load diagram. Please try again.';
      }
    } else if (err.request) {
      if (!navigator.onLine) {
        error.value = 'No internet connection. Please check your network and try again.';
      } else {
        error.value = 'Network timeout. Please check your connection and try again.';
      }
    } else {
      error.value = 'An unexpected error occurred while loading the diagram.';
    }

    console.error("Failed to fetch diagram:", err);
  } finally {
    loading.value = false;
  }
};

const handleDiagramCreated = (newDiagram) => {
  if (newDiagram && newDiagram.diagram_id) {
    window.location.href = `/diagrams/view?id=${newDiagram.diagram_id}`;
  }
};

const handleVersionSelected = (version) => {
  selectedVersionId.value = version.id;
  const url = new URL(window.location);
  url.searchParams.set('version', version.id);
  window.history.pushState({}, '', url);
};

const handleTagVersion = (version) => {
  tagTargetVersionId.value = version.id;
  showCheckpointModal.value = true;
};

const handleCheckpointCreated = () => {
  if (diagram.value) {
    fetchDiagram(diagram.value.id);
  }
};

const handleViewCheckpoint = (checkpoint) => {
  // Find the version for this checkpoint and select it
  if (checkpoint.version_id) {
    const version = diagram.value?.versions?.find(v => v.id === checkpoint.version_id);
    if (version) {
      handleVersionSelected(version);
    }
  }
};

const handleDeleteCheckpoint = async (checkpoint) => {
  if (!diagram.value) return;
  try {
    await deleteCheckpoint(diagram.value.id, checkpoint.id);
    fetchDiagram(diagram.value.id);
  } catch (err) {
    console.error('Failed to delete checkpoint:', err);
  }
};

onMounted(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const idFromUrl = urlParams.get('id');
  if (idFromUrl) {
    fetchDiagram(idFromUrl);
  } else if (props.id) {
    fetchDiagram(props.id);
  }
  else {
    loading.value = false;
  }

  window.addEventListener('resize', updateScreenSize);
  window.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  // Clean up global event listeners
  document.removeEventListener('mousemove', resize);
  document.removeEventListener('mouseup', stopResize);
  window.removeEventListener('resize', updateScreenSize);
  window.removeEventListener('keydown', handleKeyDown);
});
</script>
