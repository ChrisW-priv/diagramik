<template>
  <main id="main-content" class="border border-gray-700 rounded-lg flex flex-col h-full">
    <!-- Tab buttons for small screens -->
    <div class="flex border-b border-gray-700 md:hidden" role="tablist" aria-label="Diagram panels">
      <button
        id="tab-work"
        role="tab"
        @click="activeTab = 'work'"
        :class="['flex flex-col items-center justify-center gap-1 flex-1 py-2.5 px-3 min-h-12', activeTab === 'work' ? 'bg-gray-700 text-white' : 'text-gray-400', 'hover:bg-gray-700/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 transition-colors']"
        :aria-selected="activeTab === 'work'"
        aria-controls="panel-work"
      >
        <PencilIcon class="h-5 w-5" aria-hidden="true" />
        <span class="text-xs font-medium">Edit</span>
      </button>
      <button
        id="tab-display"
        role="tab"
        @click="diagram && (activeTab = 'display')"
        :class="['flex flex-col items-center justify-center gap-1 flex-1 py-2.5 px-3 min-h-12', activeTab === 'display' ? 'bg-gray-700 text-white' : 'text-gray-400', 'hover:bg-gray-700/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 transition-colors', !diagram ? 'opacity-40 cursor-not-allowed pointer-events-none' : '']"
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
          <!-- WorkTab -->
          <div id="panel-work" role="tabpanel" aria-labelledby="tab-work" :class="['w-full flex-col min-h-0', activeTab === 'work' ? 'block' : 'hidden', 'md:flex']" :style="isDesktop ? { width: `calc(${dividerPosition}% - 0.5rem)` } : {}">
            <WorkTab
              :diagram="diagram"
              :selected-version-id="selectedVersionId"
              @diagram-updated="fetchDiagram"
              @diagram-created="handleDiagramCreated"
              @version-selected="handleVersionSelected"
            />
          </div>

          <!-- Resizer -->
          <div
            class="hidden md:flex items-center cursor-col-resize px-1"
            @mousedown="startResize"
            @keydown="handleResizerKeydown"
            role="slider"
            :aria-valuenow="dividerPosition"
            aria-valuemin="15"
            aria-valuemax="85"
            aria-label="Resize panels divider"
            tabindex="0"
          >
            <div class="w-1.5 h-full bg-gray-600 rounded-full hover:bg-blue-500 focus-visible:bg-blue-500 transition-colors"></div>
          </div>

          <!-- DisplayTab -->
          <div id="panel-display" role="tabpanel" aria-labelledby="tab-display" :class="['w-full flex-col min-h-0', activeTab === 'display' ? 'block' : 'hidden', 'md:flex']" :style="isDesktop ? { width: `calc(${100 - dividerPosition}% - 0.5rem)` } : {}">
            <DisplayTab :diagram="diagram" :selected-version="selectedVersion" />
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { PencilIcon, EyeIcon } from '@heroicons/vue/24/outline';
import WorkTab from './WorkTab.vue';
import DisplayTab from './DisplayTab.vue';
import { getDiagram } from '../lib/api';
import { CONFIG } from '../lib/config';

const props = defineProps({
  id: String,
});

const activeTab = ref('work');
const diagram = ref(null);
const loading = ref(true);
const error = ref(null);
const selectedVersionId = ref(null);
const isResizing = ref(false);
const dividerPosition = ref(25); // Initial position in percentage (1:3 work:display ratio)
const containerRef = ref(null);
const isDesktop = ref(typeof window !== 'undefined' && window.innerWidth >= 768);

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
    if (newWidth > 15 && newWidth < 85) { // Constrain the resize
      dividerPosition.value = newWidth;
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
  // Alt + Tab (or Option + Tab on Mac)
  if (event.altKey && event.key === 'Tab') {
    event.preventDefault();
    activeTab.value = activeTab.value === 'work' ? 'display' : 'work';
  }
};

const handleResizerKeydown = (event) => {
  // Keyboard support for resizable splitter
  if (event.key === 'ArrowLeft') {
    event.preventDefault();
    const step = event.shiftKey ? 10 : 5; // Shift for larger steps
    dividerPosition.value = Math.max(15, dividerPosition.value - step);
  } else if (event.key === 'ArrowRight') {
    event.preventDefault();
    const step = event.shiftKey ? 10 : 5; // Shift for larger steps
    dividerPosition.value = Math.min(85, dividerPosition.value + step);
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
      // Sort versions by date descending to ensure the latest is first
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
    // User-friendly error messages
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
  window.removeEventListener('mousemove', resize);
  window.removeEventListener('mouseup', stopResize);
  window.removeEventListener('resize', updateScreenSize);
  window.removeEventListener('keydown', handleKeyDown);
});
</script>