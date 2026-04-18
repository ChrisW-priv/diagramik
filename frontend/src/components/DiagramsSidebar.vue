<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import {
  ExclamationCircleIcon,
  ArrowRightOnRectangleIcon,
  TrashIcon,
  PencilIcon,
  ChevronRightIcon,
  FolderIcon,
  FolderPlusIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
  PlusIcon,
  ArrowPathIcon,
} from '@heroicons/vue/24/outline';
import {
  getDiagrams,
  deleteDiagram,
  updateDiagram,
  getWorkspaces,
  createWorkspace,
  updateWorkspace,
  deleteWorkspace,
  updateDiagramWorkspace,
  authApi,
} from '../lib/api';

interface Workspace {
  id: string;
  name: string;
  created_at: string;
}

interface Diagram {
  id: string;
  name: string;
  updatedAt: string;
  workspaceId: string | null;
  workspaceName: string | null;
}

const props = defineProps<{
  activeDiagramId: string | null;
  isOpen: boolean;
}>();

const emit = defineEmits<{
  'select-diagram': [id: string];
  'new-diagram': [];
  'add-to-workspace': [workspaceId: string | null];
  'diagram-deleted': [id: string];
  'close': [];
}>();

// --- Sidebar layout state ---
const sidebarCollapsed = ref(false);
const sidebarWidth = ref(256);
const MIN_WIDTH = 160;
const MAX_WIDTH = 480;
let isResizingSidebar = false;

const startSidebarResize = (event: MouseEvent) => {
  if (sidebarCollapsed.value) return;
  event.preventDefault();
  isResizingSidebar = true;
  document.addEventListener('mousemove', onSidebarResize);
  document.addEventListener('mouseup', stopSidebarResize);
};

const onSidebarResize = (event: MouseEvent) => {
  if (!isResizingSidebar) return;
  sidebarWidth.value = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, event.clientX));
};

const stopSidebarResize = () => {
  isResizingSidebar = false;
  document.removeEventListener('mousemove', onSidebarResize);
  document.removeEventListener('mouseup', stopSidebarResize);
};

// --- Data state ---
const diagrams = ref<Diagram[]>([]);
const workspaces = ref<Workspace[]>([]);
const loading = ref(true);
const error = ref('');

const deletingId = ref<string | null>(null);
const deleteInProgress = ref<string | null>(null);

const renamingId = ref<string | null>(null);
const renameValue = ref('');
const renameInProgress = ref(false);

const showWorkspaceModal = ref(false);
const newWorkspaceName = ref('');
const creatingWorkspace = ref(false);
const workspaceModalInput = ref<HTMLInputElement | null>(null);

const renamingWorkspaceId = ref<string | null>(null);
const renameWorkspaceValue = ref('');
const renameWorkspaceInProgress = ref(false);

const deletingWorkspaceId = ref<string | null>(null);

const workspaceDropdownId = ref<string | null>(null);

const searchQuery = ref('');
const collapsedSections = ref<Set<string>>(new Set());

// --- Drag and drop ---
const draggedDiagramId = ref<string | null>(null);
const dragOverTarget = ref<string | null | undefined>(undefined);

const onDragStart = (diagramId: string, event: DragEvent) => {
  draggedDiagramId.value = diagramId;
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', diagramId);
  }
};

const onDragEnd = () => {
  draggedDiagramId.value = null;
  dragOverTarget.value = undefined;
};

const onDragOver = (targetId: string | null, event: DragEvent) => {
  event.preventDefault();
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
  dragOverTarget.value = targetId === null ? '__unassigned__' : targetId;
};

const onDragLeave = () => {
  dragOverTarget.value = undefined;
};

const onDrop = async (targetWorkspaceId: string | null, event: DragEvent) => {
  event.preventDefault();
  dragOverTarget.value = undefined;
  const id = draggedDiagramId.value;
  if (!id) return;
  const diagram = diagrams.value.find(d => d.id === id);
  if (!diagram || diagram.workspaceId === targetWorkspaceId) return;
  try {
    await updateDiagramWorkspace(id, targetWorkspaceId);
    const ws = workspaces.value.find(w => w.id === targetWorkspaceId);
    diagram.workspaceId = targetWorkspaceId;
    diagram.workspaceName = ws?.name ?? null;
  } catch {
    error.value = 'Failed to move diagram.';
  }
};

// --- Swipe to reveal delete (mobile) ---
const SWIPE_PANEL_WIDTH = 80;
const SWIPE_THRESHOLD = 40;
const swipedOpenId = ref<string | null>(null);
const touchStartX = ref(0);
const touchCurrentX = ref(0);
const touchActiveDiagramId = ref<string | null>(null);
const isTouchActive = ref(false);

const getItemTransformStyle = (diagramId: string) => {
  const open = swipedOpenId.value === diagramId;
  if (isTouchActive.value && touchActiveDiagramId.value === diagramId) {
    const base = open ? -SWIPE_PANEL_WIDTH : 0;
    const delta = touchCurrentX.value - touchStartX.value;
    const clamped = Math.max(-SWIPE_PANEL_WIDTH, Math.min(0, base + delta));
    return { transform: `translateX(${clamped}px)`, transition: 'none' };
  }
  return {
    transform: open ? `translateX(-${SWIPE_PANEL_WIDTH}px)` : 'translateX(0)',
    transition: 'transform 200ms ease-out',
  };
};

const getSwipePanelOpacity = (diagramId: string): number => {
  if (swipedOpenId.value === diagramId) return 1;
  if (isTouchActive.value && touchActiveDiagramId.value === diagramId) {
    const revealed = Math.max(0, touchStartX.value - touchCurrentX.value);
    const fadeStart = SWIPE_PANEL_WIDTH * 0.25;
    if (revealed < fadeStart) return 0;
    return Math.min(1, (revealed - fadeStart) / (SWIPE_PANEL_WIDTH * 0.5));
  }
  return 0;
};

const onTouchStart = (diagramId: string, e: TouchEvent) => {
  if (renamingId.value === diagramId || deletingId.value === diagramId) return;
  if (swipedOpenId.value && swipedOpenId.value !== diagramId) swipedOpenId.value = null;
  touchActiveDiagramId.value = diagramId;
  touchStartX.value = touchCurrentX.value = e.touches[0].clientX;
  isTouchActive.value = true;
};

const onTouchMove = (diagramId: string, e: TouchEvent) => {
  if (touchActiveDiagramId.value !== diagramId) return;
  touchCurrentX.value = e.touches[0].clientX;
};

const onTouchEnd = (diagramId: string) => {
  if (touchActiveDiagramId.value !== diagramId) { isTouchActive.value = false; return; }
  const delta = touchCurrentX.value - touchStartX.value;
  const wasOpen = swipedOpenId.value === diagramId;
  if (delta < -SWIPE_THRESHOLD) swipedOpenId.value = diagramId;
  else if (delta > SWIPE_THRESHOLD || (!wasOpen && Math.abs(delta) < 8)) swipedOpenId.value = null;
  isTouchActive.value = false;
  touchActiveDiagramId.value = null;
};

// --- Data fetching ---
const fetchDiagrams = async () => {
  loading.value = true;
  error.value = '';
  try {
    const [diagramsRes, workspacesRes] = await Promise.all([getDiagrams(), getWorkspaces()]);
    diagrams.value = diagramsRes.data
      .map((d: any) => ({
        id: d.id,
        name: d.title,
        updatedAt: d.updated_at,
        workspaceId: d.workspace_id ?? null,
        workspaceName: d.workspace_name ?? null,
      }))
      .sort((a: Diagram, b: Diagram) =>
        new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
      );
    workspaces.value = workspacesRes.data;
    const allKeys = [...workspacesRes.data.map((w: any) => w.id), 'unassigned'];
    collapsedSections.value = new Set(allKeys);
  } catch (err: any) {
    if (err.response?.status === 401) return;
    error.value = 'Failed to load diagrams.';
    console.error('Failed to fetch diagrams:', err);
  } finally {
    loading.value = false;
  }
};

defineExpose({ refresh: fetchDiagrams });

// --- Fuzzy match ---
const fuzzyMatch = (haystack: string, needle: string): boolean => {
  if (!needle) return true;
  const h = haystack.toLowerCase();
  const n = needle.toLowerCase();
  let hi = 0;
  for (let ni = 0; ni < n.length; ni++) {
    const idx = h.indexOf(n[ni], hi);
    if (idx === -1) return false;
    hi = idx + 1;
  }
  return true;
};

const filteredGroups = computed(() => {
  const q = searchQuery.value.trim();
  const matchesDiagram = (d: Diagram) => fuzzyMatch(d.name, q);
  const matchesWorkspace = (ws: Workspace) => fuzzyMatch(ws.name, q);
  const sections: Array<{ id: string | null; name: string; isUnassigned: boolean; diagrams: Diagram[] }> = [];
  for (const ws of workspaces.value) {
    const wsDiagrams = diagrams.value.filter(d => d.workspaceId === ws.id && matchesDiagram(d));
    if (!q || matchesWorkspace(ws) || wsDiagrams.length > 0) {
      sections.push({ id: ws.id, name: ws.name, isUnassigned: false, diagrams: wsDiagrams });
    }
  }
  const unassigned = diagrams.value.filter(d => d.workspaceId === null && matchesDiagram(d));
  if (unassigned.length > 0 || !q) {
    sections.push({ id: null, name: 'Unassigned', isUnassigned: true, diagrams: unassigned });
  }
  return sections;
});

// --- Collapse ---
const toggleSection = (sectionId: string | null) => {
  const key = sectionId ?? 'unassigned';
  const next = new Set(collapsedSections.value);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  collapsedSections.value = next;
};

const isSectionCollapsed = (id: string | null): boolean =>
  collapsedSections.value.has(id ?? 'unassigned');

// --- Delete diagram ---
const requestDelete = (id: string, event: Event) => {
  event.preventDefault();
  event.stopPropagation();
  swipedOpenId.value = null;
  deletingId.value = id;
};

const cancelDelete = (event: Event) => {
  event.preventDefault();
  event.stopPropagation();
  deletingId.value = null;
};

const confirmDelete = async (id: string, event: Event) => {
  event.preventDefault();
  event.stopPropagation();
  deleteInProgress.value = id;
  try {
    await deleteDiagram(id);
    diagrams.value = diagrams.value.filter(d => d.id !== id);
    deletingId.value = null;
    emit('diagram-deleted', id);
  } catch {
    error.value = 'Failed to delete diagram.';
    deletingId.value = null;
  } finally {
    deleteInProgress.value = null;
  }
};

// --- Rename diagram ---
const startRename = (diagram: Diagram, event: Event) => {
  event.preventDefault();
  event.stopPropagation();
  swipedOpenId.value = null;
  renamingId.value = diagram.id;
  renameValue.value = diagram.name;
};

const cancelRename = () => { renamingId.value = null; renameValue.value = ''; };

const submitRename = async (diagram: Diagram) => {
  const trimmed = renameValue.value.trim();
  if (!trimmed || trimmed === diagram.name) { cancelRename(); return; }
  renameInProgress.value = true;
  try {
    await updateDiagram(diagram.id, trimmed);
    diagram.name = trimmed;
    cancelRename();
  } catch {
    error.value = 'Failed to rename diagram.';
    cancelRename();
  } finally {
    renameInProgress.value = false;
  }
};

// --- Workspace actions ---
const openWorkspaceModal = () => {
  newWorkspaceName.value = '';
  showWorkspaceModal.value = true;
  nextTick(() => workspaceModalInput.value?.focus());
};

const closeWorkspaceModal = () => {
  showWorkspaceModal.value = false;
  newWorkspaceName.value = '';
};

const handleCreateWorkspace = async () => {
  const name = newWorkspaceName.value.trim();
  if (!name) return;
  creatingWorkspace.value = true;
  try {
    const res = await createWorkspace(name);
    workspaces.value.push(res.data);
    workspaces.value.sort((a, b) => a.name.localeCompare(b.name));
    collapsedSections.value = new Set([...collapsedSections.value, res.data.id]);
    closeWorkspaceModal();
  } catch {
    error.value = 'Failed to create workspace.';
  } finally {
    creatingWorkspace.value = false;
  }
};

const startRenameWorkspace = (wsId: string, event: Event) => {
  event.stopPropagation();
  const ws = workspaces.value.find(w => w.id === wsId);
  if (!ws) return;
  renamingWorkspaceId.value = ws.id;
  renameWorkspaceValue.value = ws.name;
};

const cancelRenameWorkspace = () => {
  renamingWorkspaceId.value = null;
  renameWorkspaceValue.value = '';
};

const submitRenameWorkspace = async (wsId: string) => {
  const ws = workspaces.value.find(w => w.id === wsId);
  if (!ws) return;
  const trimmed = renameWorkspaceValue.value.trim();
  if (!trimmed || trimmed === ws.name) { cancelRenameWorkspace(); return; }
  renameWorkspaceInProgress.value = true;
  try {
    await updateWorkspace(ws.id, trimmed);
    ws.name = trimmed;
    workspaces.value.sort((a, b) => a.name.localeCompare(b.name));
    cancelRenameWorkspace();
  } catch {
    error.value = 'Failed to rename workspace.';
    cancelRenameWorkspace();
  } finally {
    renameWorkspaceInProgress.value = false;
  }
};

const requestDeleteWorkspace = (id: string, event: Event) => {
  event.stopPropagation();
  deletingWorkspaceId.value = id;
};

const cancelDeleteWorkspace = (event: Event) => {
  event.stopPropagation();
  deletingWorkspaceId.value = null;
};

const confirmDeleteWorkspace = async (id: string, event: Event) => {
  event.stopPropagation();
  try {
    await deleteWorkspace(id);
    workspaces.value = workspaces.value.filter(w => w.id !== id);
    diagrams.value.forEach(d => {
      if (d.workspaceId === id) { d.workspaceId = null; d.workspaceName = null; }
    });
    deletingWorkspaceId.value = null;
  } catch {
    error.value = 'Failed to delete workspace.';
    deletingWorkspaceId.value = null;
  }
};

// --- Assign diagram to workspace ---
const assignWorkspace = async (diagram: Diagram, workspaceId: string | null, event: Event) => {
  event.stopPropagation();
  workspaceDropdownId.value = null;
  if (diagram.workspaceId === workspaceId) return;
  try {
    await updateDiagramWorkspace(diagram.id, workspaceId);
    const ws = workspaces.value.find(w => w.id === workspaceId);
    diagram.workspaceId = workspaceId;
    diagram.workspaceName = ws?.name ?? null;
  } catch {
    error.value = 'Failed to move diagram.';
  }
};

// --- Auth ---
const handleLogout = async () => {
  await authApi.logout();
  window.location.href = '/login';
};

// --- Close dropdowns on outside click ---
const closeDropdowns = (event: MouseEvent) => {
  workspaceDropdownId.value = null;
  swipedOpenId.value = null;
};

onMounted(async () => {
  await fetchDiagrams();
  document.addEventListener('click', closeDropdowns);
});

onUnmounted(() => {
  document.removeEventListener('click', closeDropdowns);
  document.removeEventListener('mousemove', onSidebarResize);
  document.removeEventListener('mouseup', stopSidebarResize);
});
</script>

<template>
  <aside
    :style="{
      width: sidebarCollapsed ? '56px' : `${sidebarWidth}px`,
      transition: 'width 200ms ease-in-out, transform 200ms ease-in-out',
    }"
    :class="[
      'fixed md:relative inset-y-0 left-0 flex-shrink-0 flex flex-col bg-gray-800 border-r border-gray-700 z-40 md:z-auto h-screen md:h-full overflow-hidden',
      isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
    ]"
    aria-label="Sidebar"
  >
    <!-- Header -->
    <div class="flex items-center px-3 h-14 border-b border-gray-700 flex-shrink-0 gap-2">
      <button
        v-if="!sidebarCollapsed"
        @click="emit('new-diagram')"
        class="flex-1 min-w-0 text-left text-sm font-semibold text-white tracking-tight hover:text-blue-300 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded"
        title="New diagram"
      >
        Diagramik
      </button>
      <!-- Collapse toggle (desktop only — on mobile the overlay is dismissed by clicking outside) -->
      <button
        @click="sidebarCollapsed = !sidebarCollapsed"
        :aria-label="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :title="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :class="[
          'hidden md:flex p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 flex-shrink-0',
          sidebarCollapsed ? 'mx-auto' : '',
        ]"
      >
        <!-- Panel icon (same as original) -->
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <line x1="9" y1="3" x2="9" y2="21" />
        </svg>
      </button>
    </div>

    <!-- Collapsible content -->
    <template v-if="!sidebarCollapsed">
      <!-- Search + New workspace -->
      <div class="flex-shrink-0 px-3 pt-3 pb-2 space-y-2 border-b border-gray-700">
        <div class="relative">
          <MagnifyingGlassIcon class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500 pointer-events-none" aria-hidden="true" />
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search diagrams..."
            class="w-full bg-gray-900 border border-gray-700 rounded-md pl-8 pr-7 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
            aria-label="Search diagrams"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''"
            class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
            aria-label="Clear search"
          >
            <XMarkIcon class="h-3.5 w-3.5" />
          </button>
        </div>
        <button
          @click="openWorkspaceModal"
          class="flex items-center gap-1.5 w-full px-1.5 py-1.5 md:py-1 text-sm md:text-xs text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
        >
          <FolderPlusIcon class="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
          <span>New workspace</span>
        </button>
      </div>

      <!-- Scrollable diagram list -->
      <div class="flex-1 min-h-0 overflow-y-auto sidebar-list py-2">
        <!-- Loading skeleton -->
        <div v-if="loading" class="px-3 space-y-1.5">
          <div v-for="i in 4" :key="i" class="h-6 rounded animate-pulse bg-gray-700/50" :style="{ width: ['70%','55%','80%','60%'][i-1] }" />
        </div>

        <!-- Error -->
        <div v-else-if="error" class="px-3">
          <div class="text-xs text-red-400 bg-red-500/10 border border-red-500/40 rounded px-2 py-1.5 flex items-start gap-1.5">
            <ExclamationCircleIcon class="h-3.5 w-3.5 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <p>{{ error }}</p>
              <button @click="fetchDiagrams" class="underline hover:text-red-200 flex items-center gap-1 mt-0.5">
                <ArrowPathIcon class="h-3 w-3" />Retry
              </button>
            </div>
          </div>
        </div>

        <!-- Workspace groups -->
        <template v-else>
          <div
            v-for="group in filteredGroups"
            :key="group.id ?? 'unassigned'"
            class="mb-1"
            :data-workspace-id="group.isUnassigned ? 'unassigned' : group.id"
            :class="{
              'bg-blue-500/8 outline outline-1 outline-blue-500/40 rounded mx-1':
                dragOverTarget === (group.isUnassigned ? '__unassigned__' : group.id),
            }"
            @dragover="onDragOver(group.isUnassigned ? null : group.id, $event)"
            @dragleave="onDragLeave"
            @drop="onDrop(group.isUnassigned ? null : group.id, $event)"
          >
            <!-- Workspace header row -->
            <div class="flex items-center px-2 py-1.5 md:py-1 group/ws min-h-[34px] md:min-h-[28px] select-none">
              <!-- Rename workspace inline -->
              <form
                v-if="renamingWorkspaceId === group.id && !group.isUnassigned"
                @submit.prevent="submitRenameWorkspace(group.id!)"
                @click.stop
                class="flex items-center gap-1 flex-1 min-w-0"
              >
                <input
                  v-model="renameWorkspaceValue"
                  @keydown.escape="cancelRenameWorkspace"
                  class="flex-1 min-w-0 text-xs bg-gray-700 border border-blue-500 rounded px-1.5 py-0.5 focus:outline-none focus:ring-1 focus:ring-blue-400"
                  aria-label="Rename workspace"
                  autofocus
                />
                <button type="submit" :disabled="renameWorkspaceInProgress" class="text-xs text-blue-400 hover:text-blue-200 disabled:opacity-50">Save</button>
                <button type="button" @click.prevent="cancelRenameWorkspace" class="text-xs text-gray-400 hover:text-gray-200">×</button>
              </form>

              <template v-else>
                <button
                  @click.stop="toggleSection(group.id)"
                  class="flex items-center gap-1.5 flex-1 min-w-0 text-left"
                  :aria-expanded="!isSectionCollapsed(group.id)"
                >
                  <ChevronRightIcon
                    class="h-3 w-3 text-gray-500 flex-shrink-0 transition-transform duration-150"
                    :class="{ 'rotate-90': !isSectionCollapsed(group.id) }"
                    aria-hidden="true"
                  />
                  <span class="text-sm md:text-xs font-medium md:font-semibold text-gray-300 md:text-gray-400 md:uppercase md:tracking-wider truncate">{{ group.name }}</span>
                </button>

                <!-- Delete confirm inline -->
                <div
                  v-if="deletingWorkspaceId === group.id && !group.isUnassigned"
                  class="flex items-center gap-1 flex-shrink-0"
                  @click.stop
                >
                  <span class="text-xs text-gray-400">Delete?</span>
                  <button @click="confirmDeleteWorkspace(group.id!, $event)" class="text-xs text-red-400 hover:text-red-300 font-medium focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-red-400 rounded px-0.5">Yes</button>
                  <button @click="cancelDeleteWorkspace($event)" class="text-xs text-gray-400 hover:text-gray-200 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-400 rounded px-0.5">Cancel</button>
                </div>

                <!-- Workspace hover actions -->
                <div
                  v-else
                  class="flex items-center gap-0.5 flex-shrink-0 opacity-0 group-hover/ws:opacity-100 focus-within:opacity-100 transition-opacity"
                >
                  <button
                    v-if="!group.isUnassigned"
                    @click.stop="startRenameWorkspace(group.id!, $event)"
                    class="p-1 rounded text-gray-500 hover:text-gray-200 hover:bg-gray-700 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-400"
                    :aria-label="`Rename ${group.name}`"
                  >
                    <PencilIcon class="h-3 w-3" aria-hidden="true" />
                  </button>
                  <button
                    v-if="!group.isUnassigned"
                    @click.stop="requestDeleteWorkspace(group.id!, $event)"
                    class="p-1 rounded text-gray-500 hover:text-red-400 hover:bg-red-400/10 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-red-400"
                    :aria-label="`Delete ${group.name}`"
                  >
                    <TrashIcon class="h-3 w-3" aria-hidden="true" />
                  </button>
                  <button
                    @click.stop="emit('add-to-workspace', group.id)"
                    class="p-1 rounded text-gray-500 hover:text-gray-200 hover:bg-gray-700 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-400"
                    :aria-label="group.isUnassigned ? 'New unassigned diagram' : `New diagram in ${group.name}`"
                    :title="group.isUnassigned ? 'New unassigned diagram' : `New diagram in ${group.name}`"
                  >
                    <PlusIcon class="h-3 w-3" aria-hidden="true" />
                  </button>
                </div>
              </template>
            </div>

            <!-- Diagram items -->
            <ul v-show="!isSectionCollapsed(group.id)" role="listbox">
              <li
                v-if="group.diagrams.length === 0 && !group.isUnassigned"
                class="px-5 py-2 md:py-1 text-sm md:text-xs text-gray-600 italic"
              >
                No diagrams — drag one here
              </li>

              <li
                v-for="diagram in group.diagrams"
                :key="diagram.id"
                class="relative group/item touch-pan-y select-none"
                role="option"
                :aria-selected="props.activeDiagramId === diagram.id"
                draggable="true"
                :class="{ 'opacity-40': draggedDiagramId === diagram.id }"
                @dragstart="onDragStart(diagram.id, $event)"
                @dragend="onDragEnd"
                @touchstart.passive="onTouchStart(diagram.id, $event)"
                @touchmove="onTouchMove(diagram.id, $event)"
                @touchend="onTouchEnd(diagram.id)"
                @touchcancel="onTouchEnd(diagram.id)"
                @contextmenu.prevent
              >
                <!-- Active indicator bar -->
                <div
                  v-if="props.activeDiagramId === diagram.id"
                  class="absolute left-0 top-1 bottom-1 w-0.5 rounded-r bg-blue-500 z-10"
                  aria-hidden="true"
                />

                <!-- Rename form -->
                <form
                  v-if="renamingId === diagram.id"
                  @submit.prevent="submitRename(diagram)"
                  @click.stop
                  class="flex items-center gap-1 px-4 py-1.5 min-w-0"
                >
                  <input
                    v-model="renameValue"
                    @keydown.escape="cancelRename"
                    class="flex-1 min-w-0 text-xs bg-gray-700 border border-blue-500 rounded px-1.5 py-0.5 focus:outline-none focus:ring-1 focus:ring-blue-400"
                    aria-label="Rename diagram"
                    autofocus
                  />
                  <button type="submit" :disabled="renameInProgress" class="text-xs text-blue-400 hover:text-blue-200 disabled:opacity-50">Save</button>
                  <button type="button" @click.prevent="cancelRename" class="text-xs text-gray-400 hover:text-gray-200">×</button>
                </form>

                <!-- Delete confirm -->
                <div
                  v-else-if="deletingId === diagram.id"
                  class="flex items-center gap-1 px-4 py-1.5"
                  @click.stop
                >
                  <span class="text-xs text-gray-400 flex-1 truncate">Delete "{{ diagram.name }}"?</span>
                  <button
                    @click="confirmDelete(diagram.id, $event)"
                    :disabled="deleteInProgress === diagram.id"
                    class="text-xs text-red-400 hover:text-red-300 font-medium disabled:opacity-50 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-red-400 rounded px-0.5 flex-shrink-0"
                  >Yes</button>
                  <button
                    @click="cancelDelete($event)"
                    class="text-xs text-gray-400 hover:text-gray-200 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-400 rounded px-0.5 flex-shrink-0"
                  >Cancel</button>
                </div>

                <!-- Normal item with swipe zone -->
                <div v-else class="relative overflow-hidden rounded-sm">
                  <!-- Swipe-reveal delete panel (right side, mobile) -->
                  <div
                    class="absolute right-0 top-0 h-full flex items-stretch sm:hidden"
                    :style="{ width: SWIPE_PANEL_WIDTH + 'px', opacity: getSwipePanelOpacity(diagram.id) }"
                    @click.stop
                  >
                    <button
                      @click.stop="requestDelete(diagram.id, $event)"
                      class="flex-1 flex flex-col items-center justify-center gap-1 bg-red-700 active:bg-red-600 text-white text-xs rounded-r-sm transition-colors"
                      :aria-label="`Delete ${diagram.name}`"
                    >
                      <TrashIcon class="h-4 w-4" aria-hidden="true" />
                      <span>Delete</span>
                    </button>
                  </div>

                  <!-- Sliding item content -->
                  <div
                    :style="{ ...getItemTransformStyle(diagram.id), WebkitTouchCallout: 'none' }"
                    class="flex items-center w-full pl-4 pr-2 py-2.5 md:py-1.5 cursor-pointer transition-colors"
                    :class="
                      props.activeDiagramId === diagram.id
                        ? 'bg-gray-700 text-white'
                        : 'text-gray-300 hover:bg-gray-700/40 hover:text-white'
                    "
                    @click="emit('select-diagram', diagram.id); emit('close')"
                  >
                    <span class="flex-1 min-w-0 text-sm md:text-xs truncate" :title="diagram.name">{{ diagram.name }}</span>

                    <!-- Hover actions (desktop only) -->
                    <div
                      class="hidden sm:flex items-center gap-0.5 flex-shrink-0 opacity-0 group-hover/item:opacity-100 focus-within:opacity-100 transition-opacity"
                      @click.stop
                    >
                      <button
                        @click.stop="startRename(diagram, $event)"
                        class="p-1 rounded text-gray-500 hover:text-gray-200 hover:bg-gray-600 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-400"
                        :aria-label="`Rename ${diagram.name}`"
                      >
                        <PencilIcon class="h-3 w-3" aria-hidden="true" />
                      </button>

                      <!-- Move to workspace -->
                      <div v-if="workspaces.length > 0" class="relative" @click.stop>
                        <button
                          @click.stop="workspaceDropdownId = workspaceDropdownId === diagram.id ? null : diagram.id"
                          class="p-1 rounded text-gray-500 hover:text-blue-400 hover:bg-blue-400/10 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-400"
                          :aria-label="`Move ${diagram.name} to workspace`"
                        >
                          <FolderIcon class="h-3 w-3" aria-hidden="true" />
                        </button>
                        <div
                          v-if="workspaceDropdownId === diagram.id"
                          class="absolute left-0 top-full mt-1 z-20 bg-gray-900 border border-gray-700 rounded-lg shadow-xl py-1 min-w-44"
                          role="menu"
                        >
                          <button
                            v-for="ws in workspaces"
                            :key="ws.id"
                            @click="assignWorkspace(diagram, ws.id, $event)"
                            class="flex items-center gap-2 w-full text-left px-3 py-2 md:py-1.5 text-sm md:text-xs hover:bg-gray-700 transition-colors"
                            :class="{ 'text-blue-400': diagram.workspaceId === ws.id }"
                            role="menuitem"
                          >
                            <FolderIcon class="h-3 w-3 flex-shrink-0" aria-hidden="true" />
                            {{ ws.name }}
                          </button>
                          <div class="border-t border-gray-700 mt-1 pt-1">
                            <button
                              @click="assignWorkspace(diagram, null, $event)"
                              class="flex items-center gap-2 w-full text-left px-3 py-2 md:py-1.5 text-sm md:text-xs hover:bg-gray-700 transition-colors"
                              :class="{ 'text-blue-400': diagram.workspaceId === null }"
                              role="menuitem"
                            >
                              <XMarkIcon class="h-3 w-3 flex-shrink-0" aria-hidden="true" />
                              Remove from workspace
                            </button>
                          </div>
                        </div>
                      </div>

                      <button
                        @click.stop="requestDelete(diagram.id, $event)"
                        class="p-1 rounded text-gray-500 hover:text-red-400 hover:bg-red-400/10 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-red-400"
                        :aria-label="`Delete ${diagram.name}`"
                      >
                        <TrashIcon class="h-3 w-3" aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                </div>
              </li>
            </ul>
          </div>

          <!-- No search results -->
          <p
            v-if="searchQuery && filteredGroups.every(g => g.diagrams.length === 0)"
            class="px-3 text-sm md:text-xs text-gray-500 py-4 text-center"
          >
            No results for "{{ searchQuery }}"
          </p>
        </template>
      </div>

      <!-- Footer: sign out -->
      <div class="flex-shrink-0 border-t border-gray-700 px-3 py-3">
        <button
          @click="handleLogout"
          aria-label="Sign out"
          class="flex items-center gap-2 w-full px-2 py-1.5 rounded text-sm text-gray-400 hover:text-white hover:bg-gray-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
        >
          <ArrowRightOnRectangleIcon class="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span>Sign out</span>
        </button>
      </div>
    </template>

    <!-- Resize handle (desktop, expanded only) -->
    <div
      v-if="!sidebarCollapsed"
      class="hidden md:block absolute right-0 top-0 bottom-0 w-1 cursor-col-resize group/resize z-10"
      @mousedown.prevent="startSidebarResize"
      title="Drag to resize"
    >
      <div class="absolute inset-y-0 right-0 w-1 bg-transparent group-hover/resize:bg-blue-500/50 transition-colors duration-150" />
    </div>
  </aside>

  <!-- New Workspace Modal -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="showWorkspaceModal"
        class="fixed inset-0 z-50 flex items-center justify-center px-4"
        @click.self="closeWorkspaceModal"
        @keydown.escape="closeWorkspaceModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="workspace-modal-title"
      >
        <div class="absolute inset-0 bg-gray-950/80 backdrop-blur-sm" aria-hidden="true" />
        <Transition
          enter-active-class="transition duration-150 ease-out"
          enter-from-class="opacity-0 scale-95 translate-y-1"
          enter-to-class="opacity-100 scale-100 translate-y-0"
          leave-active-class="transition duration-100 ease-in"
          leave-from-class="opacity-100 scale-100 translate-y-0"
          leave-to-class="opacity-0 scale-95 translate-y-1"
          appear
        >
          <div
            v-if="showWorkspaceModal"
            class="relative w-full max-w-sm bg-gray-800 border border-gray-700 rounded-xl shadow-2xl p-6"
          >
            <div class="flex items-start justify-between mb-5">
              <div>
                <h2 id="workspace-modal-title" class="text-base font-semibold text-white">New workspace</h2>
                <p class="mt-0.5 text-xs text-gray-400">Group diagrams into a named workspace.</p>
              </div>
              <button
                @click="closeWorkspaceModal"
                class="ml-4 flex-shrink-0 p-1 rounded text-gray-500 hover:text-gray-300 hover:bg-gray-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
                aria-label="Close"
              >
                <XMarkIcon class="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
            <form @submit.prevent="handleCreateWorkspace">
              <label for="workspace-name-input" class="block text-xs font-medium text-gray-400 mb-1.5">Name</label>
              <input
                id="workspace-name-input"
                ref="workspaceModalInput"
                v-model="newWorkspaceName"
                type="text"
                placeholder="e.g. Backend architecture"
                maxlength="255"
                autocomplete="off"
                class="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
              />
              <div class="flex items-center justify-end gap-2 mt-5">
                <button
                  type="button"
                  @click="closeWorkspaceModal"
                  class="px-3 py-1.5 text-sm text-gray-400 hover:text-gray-200 transition-colors rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
                >Cancel</button>
                <button
                  type="submit"
                  :disabled="creatingWorkspace || !newWorkspaceName.trim()"
                  class="flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
                >
                  <span v-if="creatingWorkspace">Creating…</span>
                  <span v-else>Create workspace</span>
                </button>
              </div>
            </form>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sidebar-list {
  scrollbar-width: none;
}
.sidebar-list::-webkit-scrollbar {
  width: 0;
}
.sidebar-list:hover {
  scrollbar-width: thin;
  scrollbar-color: #4b5563 transparent;
}
.sidebar-list:hover::-webkit-scrollbar {
  width: 4px;
}
.sidebar-list:hover::-webkit-scrollbar-track {
  background: transparent;
}
.sidebar-list:hover::-webkit-scrollbar-thumb {
  background-color: #4b5563;
  border-radius: 9999px;
}
</style>
