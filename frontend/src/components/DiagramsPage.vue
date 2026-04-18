<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import DiagramsSidebar from './DiagramsSidebar.vue';
import DiagramView from './DiagramView.vue';
import { updateDiagramWorkspace } from '../lib/api';
import { isAuthenticated } from '../lib/auth';

const activeDiagramId = ref<string | null>(null);
const pendingWorkspaceId = ref<string | null>(null);
const sidebarRef = ref<InstanceType<typeof DiagramsSidebar> | null>(null);

const selectDiagram = (id: string) => {
  activeDiagramId.value = id;
  pendingWorkspaceId.value = null;
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
  <div class="flex h-screen overflow-hidden bg-gray-900">
    <!-- Sidebar -->
    <DiagramsSidebar
      ref="sidebarRef"
      :active-diagram-id="activeDiagramId"
      @select-diagram="selectDiagram"
      @new-diagram="handleNewDiagram"
      @add-to-workspace="handleAddToWorkspace"
      @diagram-deleted="handleDiagramDeleted"
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
