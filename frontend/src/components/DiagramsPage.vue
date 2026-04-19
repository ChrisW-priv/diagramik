<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { Bars3Icon } from '@heroicons/vue/24/outline';
import DiagramsSidebar from './DiagramsSidebar.vue';
import DiagramView from './DiagramView.vue';
import { updateDiagramWorkspace } from '../lib/api';
import { isAuthenticated } from '../lib/auth';

const activeDiagramId = ref<string | null>(null);
const pendingWorkspaceId = ref<string | null>(null);
const sidebarRef = ref<InstanceType<typeof DiagramsSidebar> | null>(null);

// Mobile sidebar overlay state. Controlled here so the hamburger button
// in the mobile-only top bar can open the sidebar from outside it.
const mobileSidebarOpen = ref(false);

const selectDiagram = (id: string) => {
  activeDiagramId.value = id;
  pendingWorkspaceId.value = null;
  // Close mobile sidebar when user selects a diagram so the content is visible
  mobileSidebarOpen.value = false;
  history.pushState(null, '', `/diagrams?id=${id}`);
};

const handleNewDiagram = () => {
  activeDiagramId.value = null;
  pendingWorkspaceId.value = null;
  history.pushState(null, '', '/diagrams');
};

const handleAddToWorkspace = (workspaceId: string | null) => {
  pendingWorkspaceId.value = workspaceId;
  activeDiagramId.value = null;
  history.pushState(null, '', '/diagrams');
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
  <!-- Mobile: column layout (top bar + content). Desktop: row layout (sidebar + content). -->
  <div class="flex flex-col md:flex-row h-screen overflow-hidden bg-gray-900">

    <!-- MOBILE-ONLY top bar: hamburger + brand name.
         Hidden on md+ since the sidebar is always present there. -->
    <header class="flex md:hidden h-14 items-center px-4 bg-gray-800 border-b border-gray-700 flex-shrink-0 gap-3">
      <button
        @click="mobileSidebarOpen = true"
        aria-label="Open sidebar"
        class="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
      >
        <Bars3Icon class="h-5 w-5" aria-hidden="true" />
      </button>
      <!-- Brand name lives here on mobile; inside the sidebar on desktop -->
      <span class="text-sm font-semibold text-white tracking-tight">Diagramik</span>
    </header>

    <!-- Sidebar (fixed overlay on mobile, inline on desktop) -->
    <DiagramsSidebar
      ref="sidebarRef"
      :active-diagram-id="activeDiagramId"
      :mobile-open="mobileSidebarOpen"
      @select-diagram="selectDiagram"
      @new-diagram="handleNewDiagram"
      @add-to-workspace="handleAddToWorkspace"
      @diagram-deleted="handleDiagramDeleted"
      @close-mobile="mobileSidebarOpen = false"
    />

    <!-- Main area -->
    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <div class="flex-1 min-h-0 p-4">
        <DiagramView
          :diagram-id="activeDiagramId ?? undefined"
          @diagram-created="handleDiagramCreated"
        />
      </div>
    </div>
  </div>
</template>
