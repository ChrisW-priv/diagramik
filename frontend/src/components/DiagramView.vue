<template>
  <div class="border border-gray-700 rounded-lg">
    <!-- Tab buttons for small screens -->
    <div class="flex border-b border-gray-700 md:hidden">
      <button
        @click="activeTab = 'work'"
        :class="['px-4 py-2', activeTab === 'work' ? 'bg-gray-700' : '']"
      >
        Work
      </button>
      <button
        @click="activeTab = 'display'"
        :class="['px-4 py-2', activeTab === 'display' ? 'bg-gray-700' : '']"
        :disabled="!diagram"
      >
        Display
      </button>
    </div>

    <div class="p-4">
      <p v-if="loading" class="text-white">Loading diagram...</p>
      <p v-else-if="error" class="text-red-500">Error loading diagram: {{ error }}</p>
      <div v-else>
        <h2 class="text-3xl font-bold mb-4">{{ diagram ? diagram.title : 'New Diagram' }}</h2>
        
        <!-- Responsive layout -->
        <div class="flex flex-col md:flex-row" ref="containerRef">
          <!-- WorkTab -->
          <div :class="['w-full', activeTab === 'work' ? 'block' : 'hidden', 'md:flex']" :style="{ width: `calc(${dividerPosition}% - 0.5rem)` }">
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
          >
            <div class="w-1.5 h-full bg-ray-600 rounded-full hover:bg-blue-500 transition-colors"></div>
          </div>

          <!-- DisplayTab -->
          <div :class="['w-full', activeTab === 'display' ? 'block' : 'hidden', 'md:flex']" :style="{ width: `calc(${100 - dividerPosition}% - 0.5rem)` }">
            <DisplayTab :diagram="diagram" :selected-version="selectedVersion" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import WorkTab from './WorkTab.vue';
import DisplayTab from './DisplayTab.vue';
import { getDiagram } from '../lib/api';

const props = defineProps({
  id: String,
});

const activeTab = ref('work');
const diagram = ref(null);
const loading = ref(true);
const error = ref(null);
const selectedVersionId = ref(null);
const isResizing = ref(false);
const dividerPosition = ref(50); // Initial position in percentage
const containerRef = ref(null);

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
    error.value = err.message;
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
});

onUnmounted(() => {
  // Clean up global event listeners
  window.removeEventListener('mousemove', resize);
  window.removeEventListener('mouseup', stopResize);
});
</script>