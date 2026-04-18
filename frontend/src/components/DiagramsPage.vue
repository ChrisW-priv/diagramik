<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { Bars3Icon } from '@heroicons/vue/24/outline';
import DiagramsSidebar from './DiagramsSidebar.vue';
import DiagramView from './DiagramView.vue';
import { updateDiagramWorkspace } from '../lib/api';
import { isAuthenticated } from '../lib/auth';

const sidebarOpen = ref(false);
const activeDiagramId = ref<string | null>(null);
const pendingWorkspaceId = ref<string | null>(null);
const sidebarRef = ref<InstanceType<typeof DiagramsSidebar> | null>(null);

const selectDiagram = (id: string) => {
  activeDiagramId.value = id;
  pendingWorkspaceId.value = null;
  history.pushState(null, '', `/diagrams?id=${id}`);
  sidebarOpen.value = false;
};

const handleNewDiagram = () => {
  activeDiagramId.value = null;
  pendingWorkspaceId.value = null;
  history.pushState(null, '', '/diagrams');
  sidebarOpen.value = false;
};

const handleAddToWorkspace = (workspaceId: string | null) => {
  pendingWorkspaceId.value = workspaceId;
  activeDiagramId.value = null;
  history.pushState(null, '', '/diagrams');
  sidebarOpen.value = false;
};

const handleDiagramCreated = async (newDiagram: any) => {
  const diagramId = newDiagram.diagram_id;
  if (pendingWorkspaceId.value) {
    try {
      await updateDiagramWorkspace(diagramId, pendingWorkspaceId.value);
    } catch (e) {
      console.error('Failed to assign workspace:', e);
    }
    pendingWorkspaceId.value = null;
  }
  activeDiagramId.value = diagramId;
  history.pushState(null, '', `/diagrams?id=${diagramId}`);
  sidebarRef.value?.refresh();
};

const handleDiagramDeleted = (id: string) => {
  if (activeDiagramId.value === id) {
    activeDiagramId.value = null;
    history.pushState(null, '', '/diagrams');
  }
};

const handlePopState = () => {
  const params = new URLSearchParams(window.location.search);
  activeDiagramId.value = params.get('id') || null;
};

onMounted(() => {
  if (!isAuthenticated()) {
    window.location.href = '/login';
    return;
  }
  const params = new URLSearchParams(window.location.search);
  activeDiagramId.value = params.get('id') || null;
  window.addEventListener('popstate', handlePopState);
});

onUnmounted(() => {
  window.removeEventListener('popstate', handlePopState);
});
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-gray-900">
    <!-- Mobile overlay backdrop -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="sidebarOpen"
        class="fixed inset-0 z-30 bg-gray-950/60 md:hidden"
        @click="sidebarOpen = false"
        aria-hidden="true"
      />
    </Transition>

    <!-- Sidebar -->
    <DiagramsSidebar
      ref="sidebarRef"
      :active-diagram-id="activeDiagramId"
      :is-open="sidebarOpen"
      @select-diagram="selectDiagram"
      @new-diagram="handleNewDiagram"
      @add-to-workspace="handleAddToWorkspace"
      @diagram-deleted="handleDiagramDeleted"
      @close="sidebarOpen = false"
    />

    <!-- Main area -->
    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <!-- Mobile top bar -->
      <div class="flex items-center px-3 h-11 border-b border-gray-800 flex-shrink-0 md:hidden">
        <button
          @click="sidebarOpen = true"
          aria-label="Open sidebar"
          class="p-1.5 rounded text-gray-400 hover:text-white hover:bg-gray-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
        >
          <Bars3Icon class="h-5 w-5" aria-hidden="true" />
        </button>
        <span class="ml-3 text-sm font-medium text-gray-400 select-none">Diagramik</span>
      </div>

      <!-- Editor panel -->
      <div class="flex-1 min-h-0 p-4">
        <DiagramView
          :diagram-id="activeDiagramId ?? undefined"
          @diagram-created="handleDiagramCreated"
        />
      </div>
    </div>
  </div>
</template>
