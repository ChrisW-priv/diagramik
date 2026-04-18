<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import {
  ExclamationCircleIcon,
  ArrowPathIcon,
  PlusCircleIcon,
  ArrowRightOnRectangleIcon,
  TrashIcon,
  PencilIcon,
  ChevronRightIcon,
  FolderIcon,
  FolderPlusIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
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
import { isAuthenticated } from '../lib/auth';

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

const formatRelativeTime = (isoString: string): string => {
  const diff = Date.now() - new Date(isoString).getTime();
  const minutes = Math.floor(diff / 60_000);
  const hours = Math.floor(diff / 3_600_000);
  const days = Math.floor(diff / 86_400_000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 30) return `${days}d ago`;
  return new Date(isoString).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
};

// --- State ---
const diagrams = ref<Diagram[]>([]);
const workspaces = ref<Workspace[]>([]);
const loading = ref(true);
const error = ref('');

// Delete
const deletingId = ref<string | null>(null);
const deleteInProgress = ref<string | null>(null);

// Rename diagram
const renamingId = ref<string | null>(null);
const renameValue = ref('');
const renameInProgress = ref(false);

// Workspace create/delete
const showWorkspaceModal = ref(false);
const newWorkspaceName = ref('');
const creatingWorkspace = ref(false);
const deletingWorkspaceId = ref<string | null>(null);
const workspaceModalInput = ref<HTMLInputElement | null>(null);

const openWorkspaceModal = () => {
  newWorkspaceName.value = '';
  showWorkspaceModal.value = true;
  nextTick(() => workspaceModalInput.value?.focus());
};

const closeWorkspaceModal = () => {
  showWorkspaceModal.value = false;
  newWorkspaceName.value = '';
};

// Rename workspace
const renamingWorkspaceId = ref<string | null>(null);
const renameWorkspaceValue = ref('');
const renameWorkspaceInProgress = ref(false);

// Workspace assign dropdown
const workspaceDropdownId = ref<string | null>(null);

// Search & filter
const searchQuery = ref('');
const activeWorkspaceFilter = ref<string | null | 'unassigned'>(undefined as any);

// Drag-and-drop
const draggedDiagramId = ref<string | null>(null);
const dragOverTarget = ref<string | null | 'unassigned'>(undefined as any);

// Sidebar
const sidebarOpen = ref(false);

// Collapse
const collapsedSections = ref<Set<string>>(new Set());

// Swipe (mobile)
const SWIPE_PANEL_WIDTH = 128;
const SWIPE_THRESHOLD = 50;
const swipedOpenId = ref<string | null>(null);
const touchStartX = ref(0);
const touchStartY = ref(0);
const touchCurrentX = ref(0);
const touchActiveDiagramId = ref<string | null>(null);
const isTouchActive = ref(false);

// Long press → touch drag (mobile workspace assignment)
const longPressTimer = ref<ReturnType<typeof setTimeout> | null>(null);
const longPressTargetId = ref<string | null>(null);
const touchDragId = ref<string | null>(null);
const touchCurrentY = ref(0);
const dragStartY = ref(0);
const touchDragOverTarget = ref<string | null | undefined>(undefined);

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
    // Collapse all sections by default
    const allKeys = [
      ...workspacesRes.data.map((w: any) => w.id),
      'unassigned',
    ];
    collapsedSections.value = new Set(allKeys);
  } catch (err: any) {
    if (err.response?.status === 401) return;
    if (err.response) {
      const status = err.response.status;
      if (status >= 500) {
        error.value = 'Server error occurred. Please try again later.';
      } else if (status === 403) {
        error.value = 'Access denied. You may not have permission to view diagrams.';
      } else {
        error.value = 'Failed to load diagrams. Please try again.';
      }
    } else if (err.request) {
      error.value = navigator.onLine
        ? 'Network timeout. Please check your connection and try again.'
        : 'No internet connection. Please check your network and try again.';
    } else {
      error.value = 'An unexpected error occurred while loading diagrams.';
    }
    console.error('Failed to fetch diagrams:', err);
  } finally {
    loading.value = false;
  }
};

const retryFetch = () => fetchDiagrams();

// --- Fuzzy match helper ---
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

// --- Computed grouped/filtered view ---
const filteredGroups = computed(() => {
  const q = searchQuery.value.trim();
  const wsFilter = activeWorkspaceFilter.value;

  const matchesDiagram = (d: Diagram) => fuzzyMatch(d.name, q);
  const matchesWorkspace = (ws: Workspace) => fuzzyMatch(ws.name, q);

  // Build workspace sections
  const sections: Array<{ id: string | null; name: string; isUnassigned: boolean; diagrams: Diagram[] }> = [];

  for (const ws of workspaces.value) {
    // Skip if workspace filter is active and this isn't the selected one
    if (wsFilter !== undefined && wsFilter !== null && wsFilter !== 'unassigned' && wsFilter !== ws.id) continue;

    const wsDiagrams = diagrams.value.filter(d => d.workspaceId === ws.id && matchesDiagram(d));
    // Include section if: workspace name matches search OR any diagram matches
    if (!q || matchesWorkspace(ws) || wsDiagrams.length > 0) {
      sections.push({ id: ws.id, name: ws.name, isUnassigned: false, diagrams: wsDiagrams });
    }
  }

  // Unassigned diagrams at the bottom
  if (wsFilter === undefined || wsFilter === null || wsFilter === 'unassigned') {
    const unassigned = diagrams.value.filter(d => d.workspaceId === null && matchesDiagram(d));
    if (unassigned.length > 0 || !q) {
      sections.push({ id: null, name: 'Unassigned', isUnassigned: true, diagrams: unassigned });
    }
  }

  return sections;
});

const hasWorkspaces = computed(() => workspaces.value.length > 0);
const totalDiagrams = computed(() => diagrams.value.length);

// --- Delete diagram ---
const requestDelete = (id: string, event: Event) => {
  event.preventDefault();
  event.stopPropagation();
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
  } catch {
    error.value = 'Failed to delete diagram. Please try again.';
    deletingId.value = null;
  } finally {
    deleteInProgress.value = null;
  }
};

// --- Rename diagram ---
const startRename = (diagram: Diagram, event: Event) => {
  event.preventDefault();
  event.stopPropagation();
  renamingId.value = diagram.id;
  renameValue.value = diagram.name;
};

const cancelRename = () => {
  renamingId.value = null;
  renameValue.value = '';
};

const submitRename = async (diagram: Diagram) => {
  const trimmed = renameValue.value.trim();
  if (!trimmed || trimmed === diagram.name) {
    cancelRename();
    return;
  }
  renameInProgress.value = true;
  try {
    await updateDiagram(diagram.id, trimmed);
    diagram.name = trimmed;
    cancelRename();
  } catch {
    error.value = 'Failed to rename diagram. Please try again.';
    cancelRename();
  } finally {
    renameInProgress.value = false;
  }
};

// --- Workspace actions ---
const handleCreateWorkspace = async () => {
  const name = newWorkspaceName.value.trim();
  if (!name) return;
  creatingWorkspace.value = true;
  try {
    const res = await createWorkspace(name);
    workspaces.value.push(res.data);
    workspaces.value.sort((a, b) => a.name.localeCompare(b.name));
    // Collapse the new workspace by default
    collapsedSections.value = new Set([...collapsedSections.value, res.data.id]);
    closeWorkspaceModal();
  } catch {
    error.value = 'Failed to create workspace. Please try again.';
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
  if (!trimmed || trimmed === ws.name) {
    cancelRenameWorkspace();
    return;
  }
  renameWorkspaceInProgress.value = true;
  try {
    await updateWorkspace(ws.id, trimmed);
    ws.name = trimmed;
    workspaces.value.sort((a, b) => a.name.localeCompare(b.name));
    cancelRenameWorkspace();
  } catch {
    error.value = 'Failed to rename workspace. Please try again.';
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
    // Move diagrams that were in this workspace to unassigned
    diagrams.value.forEach(d => {
      if (d.workspaceId === id) {
        d.workspaceId = null;
        d.workspaceName = null;
      }
    });
    deletingWorkspaceId.value = null;
  } catch {
    error.value = 'Failed to delete workspace. Please try again.';
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
    error.value = 'Failed to move diagram. Please try again.';
  }
};

// --- Toggle workspace filter ---
const setWorkspaceFilter = (id: string | null | 'unassigned', event: Event) => {
  event.stopPropagation();
  if (activeWorkspaceFilter.value === id) {
    activeWorkspaceFilter.value = undefined as any;
  } else {
    activeWorkspaceFilter.value = id;
  }
};

// --- Collapse toggle ---
const toggleSection = (sectionId: string) => {
  const key = sectionId ?? 'unassigned';
  if (collapsedSections.value.has(key)) {
    collapsedSections.value.delete(key);
  } else {
    collapsedSections.value.add(key);
  }
  // Force reactivity
  collapsedSections.value = new Set(collapsedSections.value);
};

const isSectionCollapsed = (id: string | null): boolean => {
  return collapsedSections.value.has(id ?? 'unassigned');
};

// --- Drag-and-drop ---
const onDragStart = (diagramId: string, event: DragEvent) => {
  draggedDiagramId.value = diagramId;
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', diagramId);
  }
};

const onDragEnd = () => {
  draggedDiagramId.value = null;
  dragOverTarget.value = undefined as any;
};

const onDragOver = (targetId: string | null | 'unassigned', event: DragEvent) => {
  event.preventDefault();
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
  dragOverTarget.value = targetId;
};

const onDragLeave = () => {
  dragOverTarget.value = undefined as any;
};

const onDrop = async (targetWorkspaceId: string | null, event: DragEvent) => {
  event.preventDefault();
  dragOverTarget.value = undefined as any;
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
    error.value = 'Failed to move diagram. Please try again.';
  }
};

// --- Swipe + long-press drag (mobile) ---
const getItemTransformStyle = (diagramId: string) => {
  if (touchDragId.value === diagramId) return {};
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

// Fade swipe panel in only after deliberate swipe (not micro-movements or long press)
const getSwipePanelOpacity = (diagramId: string): number => {
  if (touchDragId.value === diagramId) return 0;
  if (swipedOpenId.value === diagramId) return 1;
  if (isTouchActive.value && touchActiveDiagramId.value === diagramId) {
    const revealed = Math.max(0, touchStartX.value - touchCurrentX.value);
    const fadeStart = SWIPE_PANEL_WIDTH * 0.25;
    if (revealed < fadeStart) return 0;
    return Math.min(1, (revealed - fadeStart) / (SWIPE_PANEL_WIDTH * 0.5));
  }
  return 0;
};

// Lifted style applied to the whole <li> during touch drag
const getTouchDragStyle = (diagramId: string) => {
  if (touchDragId.value !== diagramId) return {};
  const dy = touchCurrentY.value - dragStartY.value;
  return {
    transform: `translateY(${dy}px)`,
    zIndex: 50,
    opacity: 0.92,
    boxShadow: '0 12px 32px rgba(0,0,0,0.55)',
    transition: 'none',
    pointerEvents: 'none' as const,
  };
};

const cancelLongPress = () => {
  if (longPressTimer.value) { clearTimeout(longPressTimer.value); longPressTimer.value = null; }
  longPressTargetId.value = null;
};

const onTouchStart = (diagramId: string, e: TouchEvent) => {
  if (swipedOpenId.value && swipedOpenId.value !== diagramId) swipedOpenId.value = null;
  touchActiveDiagramId.value = diagramId;
  touchStartX.value = touchCurrentX.value = e.touches[0].clientX;
  touchStartY.value = touchCurrentY.value = e.touches[0].clientY;
  isTouchActive.value = true;

  // Start long press → drag mode (only if workspaces exist)
  if (hasWorkspaces.value) {
    longPressTargetId.value = diagramId;
    longPressTimer.value = setTimeout(() => {
      longPressTargetId.value = null;
      longPressTimer.value = null;
      dragStartY.value = touchCurrentY.value;
      touchDragId.value = diagramId;
      isTouchActive.value = false;
      touchActiveDiagramId.value = null;
      if (navigator.vibrate) navigator.vibrate(40);
    }, 500);
  }
};

const onTouchMove = (diagramId: string, e: TouchEvent) => {
  const touch = e.touches[0];

  // Drag mode: track Y and detect which workspace section is under the finger
  if (touchDragId.value === diagramId) {
    e.preventDefault(); // prevent page scroll while dragging
    touchCurrentY.value = touch.clientY;
    // Detect section by checking bounding rects (no pointer-events hack needed)
    let found: string | null | undefined = undefined;
    const sections = document.querySelectorAll<HTMLElement>('[data-workspace-id]');
    for (const section of sections) {
      const rect = section.getBoundingClientRect();
      if (touch.clientY >= rect.top && touch.clientY <= rect.bottom) {
        const wsId = section.dataset.workspaceId;
        found = wsId === 'unassigned' ? null : wsId;
        break;
      }
    }
    touchDragOverTarget.value = found;
    return;
  }

  if (touchActiveDiagramId.value !== diagramId) return;
  touchCurrentX.value = touch.clientX;
  touchCurrentY.value = touch.clientY;
  // Cancel long press if finger moved (swipe takes precedence)
  const dx = Math.abs(touchCurrentX.value - touchStartX.value);
  const dy = Math.abs(touchCurrentY.value - touchStartY.value);
  if (dx > 8 || dy > 8) cancelLongPress();
};

const onTouchEnd = (diagramId: string) => {
  // Drag mode: drop into detected workspace
  if (touchDragId.value === diagramId) {
    const target = touchDragOverTarget.value;
    if (target !== undefined) {
      const diagram = diagrams.value.find(d => d.id === diagramId);
      if (diagram && diagram.workspaceId !== target) {
        assignWorkspace(diagram, target, new Event('dragdrop'));
      }
    }
    touchDragId.value = null;
    touchDragOverTarget.value = undefined;
    return;
  }

  cancelLongPress();
  if (touchActiveDiagramId.value !== diagramId) { isTouchActive.value = false; return; }
  const delta = touchCurrentX.value - touchStartX.value;
  const wasOpen = swipedOpenId.value === diagramId;
  if (delta < -SWIPE_THRESHOLD) swipedOpenId.value = diagramId;
  else if (delta > SWIPE_THRESHOLD || (!wasOpen && Math.abs(delta) < 8)) swipedOpenId.value = null;
  isTouchActive.value = false;
  touchActiveDiagramId.value = null;
};

// --- Close dropdowns on outside click ---
const closeDropdowns = () => {
  workspaceDropdownId.value = null;
  deletingWorkspaceId.value = null;
  swipedOpenId.value = null;
};

// --- Auth ---
const handleLogout = async () => {
  await authApi.logout();
  window.location.href = '/login';
};

onMounted(async () => {
  if (!isAuthenticated()) {
    window.location.href = '/login';
    return;
  }
  await fetchDiagrams();
  document.addEventListener('click', closeDropdowns);
});

onUnmounted(() => {
  document.removeEventListener('click', closeDropdowns);
});
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-gray-900">
    <!-- Sidebar -->
    <aside
      class="fixed inset-y-0 left-0 md:relative md:inset-auto flex-shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col overflow-hidden transition-all duration-200 ease-in-out z-40 md:z-auto"
      :class="sidebarOpen ? 'w-56' : 'w-14'"
    >
      <!-- Logo + toggle -->
      <div class="flex items-center justify-between px-3 h-14 border-b border-gray-800 flex-shrink-0">
        <span v-if="sidebarOpen" class="text-sm font-semibold text-white tracking-tight">Diagramik</span>
        <button
          @click="sidebarOpen = !sidebarOpen"
          :aria-label="sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'"
          :aria-expanded="sidebarOpen"
          class="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 flex-shrink-0"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <line x1="9" y1="3" x2="9" y2="21" />
          </svg>
        </button>
      </div>

      <!-- Nav space -->
      <div class="flex-1" />

      <!-- Sign out -->
      <div class="px-2 md:px-3 py-4 border-t border-gray-800">
        <button
          @click="handleLogout"
          aria-label="Sign out"
          class="flex items-center gap-2.5 w-full px-2 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
        >
          <ArrowRightOnRectangleIcon class="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span v-if="sidebarOpen">Sign out</span>
        </button>
      </div>
    </aside>

    <!-- Main panel -->
    <div
      class="flex flex-col flex-1 min-w-0 overflow-hidden transition-transform duration-200 ease-in-out md:translate-x-0 pl-14 md:pl-0"
      :class="{ 'translate-x-[10.5rem]': sidebarOpen }"
    >
      <!-- Top bar -->
      <header class="flex items-center gap-3 px-4 h-14 border-b border-gray-800 flex-shrink-0">
        <!-- Search -->
        <div class="relative flex-1">
          <MagnifyingGlassIcon class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500 pointer-events-none" aria-hidden="true" />
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search diagrams and workspaces…"
            class="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-9 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-400"
            aria-label="Search diagrams and workspaces"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-200"
            aria-label="Clear search"
          >
            <XMarkIcon class="h-4 w-4" />
          </button>
        </div>

        <!-- New workspace -->
        <button
          @click="openWorkspaceModal"
          class="flex items-center gap-1.5 px-3 py-2 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 flex-shrink-0"
          aria-label="New workspace"
        >
          <FolderPlusIcon class="h-4 w-4" aria-hidden="true" />
          <span class="hidden sm:inline">New workspace</span>
        </button>

        <!-- New diagram -->
        <a
          href="/diagrams/new"
          aria-label="New diagram"
          class="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 px-3 py-2 rounded-lg transition-colors flex-shrink-0 text-sm font-medium"
        >
          <PlusCircleIcon class="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span class="hidden sm:inline">New diagram</span>
        </a>
      </header>

      <!-- Scrollable content -->
      <main id="main-content" class="flex-1 overflow-y-auto px-4 py-6">
        <!-- Loading -->
        <div v-if="loading" aria-live="polite" aria-busy="true" class="space-y-4">
          <div
            v-for="(width, i) in ['72%', '55%', '83%']"
            :key="i"
            class="flex items-center justify-between gap-4 px-3 py-3 md:px-4 bg-gray-800 rounded-lg animate-pulse"
          >
            <div class="h-4 bg-gray-700 rounded" :style="{ width }"></div>
            <div class="h-3 w-12 bg-gray-700 rounded flex-shrink-0"></div>
          </div>
        </div>

        <!-- Error -->
        <div v-else-if="error" aria-live="assertive" role="alert" class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded flex items-start gap-3 mb-4">
          <ExclamationCircleIcon class="h-6 w-6 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div class="flex-grow">
            <p>{{ error }}</p>
            <button
              @click="retryFetch"
              class="flex items-center gap-2 mt-2 text-sm text-red-300 hover:text-red-100 underline"
            >
              <ArrowPathIcon class="h-4 w-4" aria-hidden="true" />
              Try Again
            </button>
          </div>
        </div>

        <template v-else>
          <!-- Active workspace filter chip -->
          <div v-if="activeWorkspaceFilter !== undefined" class="flex items-center gap-2 mb-4 text-sm">
            <span class="text-gray-400">Filtered by:</span>
            <span class="flex items-center gap-1.5 bg-blue-600/20 text-blue-400 border border-blue-600/40 rounded-full px-3 py-0.5">
              <FolderIcon class="h-3.5 w-3.5" aria-hidden="true" />
              {{
                activeWorkspaceFilter === 'unassigned'
                  ? 'Unassigned'
                  : workspaces.find(w => w.id === activeWorkspaceFilter)?.name ?? 'Workspace'
              }}
              <button @click="activeWorkspaceFilter = undefined as any" class="ml-1 hover:text-blue-200" aria-label="Clear filter">
                <XMarkIcon class="h-3.5 w-3.5" />
              </button>
            </span>
          </div>

          <!-- Empty state (no diagrams at all) -->
          <div v-if="totalDiagrams === 0" class="text-center py-12">
            <p class="text-gray-400 mb-4">No diagrams found yet.</p>
            <p class="text-sm text-gray-500 mb-6">Create your first diagram to get started with Diagramik.</p>
            <a href="/diagrams/new" class="inline-block bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 px-6 py-3 rounded-lg text-white font-medium transition-colors">
              Create your first diagram
            </a>
          </div>

          <!-- Grouped list -->
          <div v-else class="space-y-6">
            <section
              v-for="group in filteredGroups"
              :key="group.id ?? 'unassigned'"
              class="rounded-lg transition-colors"
              :data-workspace-id="group.isUnassigned ? 'unassigned' : group.id"
              :class="{
                'border-2 border-dashed border-blue-500/60 bg-blue-500/5':
                  dragOverTarget === (group.isUnassigned ? null : group.id) ||
                  touchDragOverTarget === (group.isUnassigned ? null : group.id),
              }"
              @dragover="onDragOver(group.isUnassigned ? null : group.id, $event)"
              @dragleave="onDragLeave"
              @drop="onDrop(group.isUnassigned ? null : group.id, $event)"
            >
              <!-- Section header (only show if there are workspaces OR a search is active) -->
              <div
                v-if="hasWorkspaces || searchQuery"
                class="flex items-center gap-2 mb-2 group/ws select-none"
              >
                <!-- Collapse toggle -->
                <button
                  @click.stop="toggleSection(group.id ?? 'unassigned')"
                  class="flex items-center gap-2 flex-1 text-left py-1 min-w-0"
                  :aria-expanded="!isSectionCollapsed(group.id)"
                >
                  <ChevronRightIcon
                    class="h-3.5 w-3.5 text-gray-500 flex-shrink-0 transition-transform duration-150"
                    :class="{ 'rotate-90': !isSectionCollapsed(group.id) }"
                    aria-hidden="true"
                  />
                  <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider truncate">{{ group.name }}</span>
                  <span class="text-xs text-gray-600 font-normal normal-case tracking-normal">({{ group.diagrams.length }})</span>
                </button>

                <!-- Workspace actions (only for named workspaces) -->
                <div v-if="!group.isUnassigned" class="flex items-center gap-1 flex-shrink-0 opacity-0 group-hover/ws:opacity-100 focus-within:opacity-100 transition-opacity">
                  <!-- Filter button -->
                  <button
                    @click="setWorkspaceFilter(group.id, $event)"
                    class="p-1 rounded text-gray-500 hover:text-blue-400 hover:bg-blue-400/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 transition-colors"
                    :class="{ 'text-blue-400 bg-blue-400/10': activeWorkspaceFilter === group.id }"
                    :aria-label="`Filter by ${group.name}`"
                    :title="`Filter by ${group.name}`"
                  >
                    <FolderIcon class="h-3.5 w-3.5" aria-hidden="true" />
                  </button>

                  <!-- Rename workspace -->
                  <button
                    v-if="renamingWorkspaceId !== group.id && deletingWorkspaceId !== group.id"
                    @click="startRenameWorkspace(group.id!, $event)"
                    class="p-1 rounded text-gray-500 hover:text-gray-200 hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 transition-colors"
                    :aria-label="`Rename ${group.name}`"
                    :title="`Rename ${group.name}`"
                  >
                    <PencilIcon class="h-3.5 w-3.5" aria-hidden="true" />
                  </button>

                  <!-- Delete workspace -->
                  <template v-if="deletingWorkspaceId !== group.id">
                    <button
                      v-if="renamingWorkspaceId !== group.id"
                      @click="requestDeleteWorkspace(group.id!, $event)"
                      class="p-1 rounded text-gray-500 hover:text-red-400 hover:bg-red-400/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 transition-colors"
                      :aria-label="`Delete ${group.name}`"
                      :title="`Delete ${group.name}`"
                    >
                      <TrashIcon class="h-3.5 w-3.5" aria-hidden="true" />
                    </button>
                  </template>
                  <template v-else>
                    <span class="text-xs text-gray-400 mr-1">Delete?</span>
                    <button
                      @click="confirmDeleteWorkspace(group.id!, $event)"
                      class="text-xs text-red-400 hover:text-red-300 font-medium px-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 rounded"
                    >Yes</button>
                    <button
                      @click="cancelDeleteWorkspace($event)"
                      class="text-xs text-gray-400 hover:text-gray-200 px-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded"
                    >Cancel</button>
                  </template>
                </div>
              </div>

              <!-- Rename workspace inline -->
              <form
                v-if="renamingWorkspaceId !== null && renamingWorkspaceId === group.id"
                @submit.prevent="submitRenameWorkspace(group.id!)"
                @click.stop
                class="flex items-center gap-2 mb-2"
              >
                <input
                  v-model="renameWorkspaceValue"
                  @keydown.escape="cancelRenameWorkspace"
                  class="flex-1 min-w-0 text-sm bg-gray-700 border border-blue-500 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  aria-label="Rename workspace"
                  autofocus
                />
                <button type="submit" :disabled="renameWorkspaceInProgress" class="text-xs text-blue-400 hover:text-blue-200 px-1">Save</button>
                <button type="button" @click.prevent="cancelRenameWorkspace" class="text-xs text-gray-400 hover:text-gray-200 px-1">Cancel</button>
              </form>

              <!-- Diagram items -->
              <ul
                v-show="!isSectionCollapsed(group.id)"
                :class="{ 'pl-2': hasWorkspaces || searchQuery }"
              >
                <li v-if="group.diagrams.length === 0 && !group.isUnassigned" class="text-sm text-gray-600 italic px-3 py-2">
                  No diagrams — drag one here
                </li>

                <li
                  v-for="diagram in group.diagrams"
                  :key="diagram.id"
                  class="relative touch-pan-y select-none"
                  draggable="true"
                  @dragstart="onDragStart(diagram.id, $event)"
                  @dragend="onDragEnd"
                  :class="{ 'opacity-40': draggedDiagramId === diagram.id }"
                  :style="getTouchDragStyle(diagram.id)"
                  @touchstart.passive="onTouchStart(diagram.id, $event)"
                  @touchmove="onTouchMove(diagram.id, $event)"
                  @touchend="onTouchEnd(diagram.id)"
                  @touchcancel="onTouchEnd(diagram.id)"
                  @contextmenu.prevent
                >
                  <!-- Swipe zone (overflow-hidden clips the panel) -->
                  <div class="relative overflow-hidden rounded-lg">
                    <!-- Swipe-reveal action panel (mobile only; Rename + Delete) -->
                    <div
                      class="absolute right-0 top-0 h-full flex items-stretch sm:hidden"
                      :style="{ width: SWIPE_PANEL_WIDTH + 'px', opacity: getSwipePanelOpacity(diagram.id) }"
                      @click.stop
                    >
                      <!-- Rename -->
                      <button
                        v-if="renamingId !== diagram.id"
                        @click.stop="startRename(diagram, $event); swipedOpenId = null"
                        class="flex-1 flex flex-col items-center justify-center gap-1 bg-gray-600 active:bg-gray-500 text-gray-100 text-xs transition-colors"
                        :aria-label="`Rename ${diagram.name}`"
                      >
                        <PencilIcon class="h-4 w-4" aria-hidden="true" />
                        <span>Rename</span>
                      </button>

                      <!-- Delete -->
                      <template v-if="deletingId !== diagram.id">
                        <button
                          @click.stop="requestDelete(diagram.id, $event); swipedOpenId = null"
                          class="flex-1 flex flex-col items-center justify-center gap-1 bg-red-700 active:bg-red-600 text-white text-xs rounded-r-lg transition-colors"
                          :aria-label="`Delete ${diagram.name}`"
                        >
                          <TrashIcon class="h-4 w-4" aria-hidden="true" />
                          <span>Delete</span>
                        </button>
                      </template>
                      <template v-else>
                        <div class="flex-1 flex flex-col items-center justify-center gap-1.5 bg-red-700 text-white text-xs rounded-r-lg">
                          <span class="font-medium text-sm">Delete?</span>
                          <div class="flex gap-3">
                            <button
                              @click.stop="confirmDelete(diagram.id, $event)"
                              :disabled="deleteInProgress === diagram.id"
                              class="font-semibold disabled:opacity-50"
                            >Yes</button>
                            <button
                              @click.stop="cancelDelete($event); swipedOpenId = null"
                              class="opacity-70 hover:opacity-100"
                            >No</button>
                          </div>
                        </div>
                      </template>
                    </div>

                    <!-- Main sliding content -->
                    <div
                      class="relative flex items-center gap-1 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors duration-200 group/item cursor-grab active:cursor-grabbing"
                      :class="{
                        'bg-blue-950 hover:bg-blue-950 ring-1 ring-blue-700/50': longPressTargetId === diagram.id,
                        'bg-blue-900/20 ring-1 ring-blue-500/60 scale-[1.01]': touchDragId === diagram.id,
                      }"
                      :style="getItemTransformStyle(diagram.id)"
                    >
                      <template v-if="renamingId !== diagram.id">
                        <!-- Link: name only -->
                        <a
                          :href="`/diagrams/view?id=${diagram.id}`"
                          class="flex items-center flex-1 min-w-0 px-3 py-3 md:px-4"
                          style="-webkit-touch-callout: none;"
                        >
                          <h2 class="text-sm font-medium truncate group-hover/item:text-blue-400 transition-colors" :title="diagram.name">{{ diagram.name }}</h2>
                        </a>

                        <!-- Right slot: time + desktop actions (hidden on mobile) -->
                        <div class="hidden sm:flex relative flex-shrink-0 items-center min-w-[96px] justify-end pr-2">
                          <!-- Time: visible at rest, fades out on hover -->
                          <time
                            :datetime="diagram.updatedAt"
                            class="text-xs text-gray-500 tabular-nums pointer-events-none transition-opacity duration-150 group-hover/item:opacity-0"
                            :class="{ 'opacity-0': deletingId === diagram.id }"
                            :title="new Date(diagram.updatedAt).toLocaleString()"
                          >{{ formatRelativeTime(diagram.updatedAt) }}</time>

                          <!-- Desktop action buttons: crossfade in on hover -->
                          <div class="absolute right-0 flex items-center gap-0.5 opacity-0 group-hover/item:opacity-100 focus-within:opacity-100 transition-opacity duration-150">
                            <!-- Rename -->
                            <button
                              v-if="deletingId !== diagram.id"
                              @click="startRename(diagram, $event)"
                              class="p-1.5 rounded text-gray-500 hover:text-gray-200 hover:bg-gray-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
                              :aria-label="`Rename ${diagram.name}`"
                            >
                              <PencilIcon class="h-4 w-4" aria-hidden="true" />
                            </button>

                            <!-- Move to workspace -->
                            <div class="relative" @click.stop>
                              <button
                                v-if="hasWorkspaces && deletingId !== diagram.id"
                                @click.stop="workspaceDropdownId = workspaceDropdownId === diagram.id ? null : diagram.id"
                                class="p-1.5 rounded text-gray-500 hover:text-blue-400 hover:bg-blue-400/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
                                :aria-label="`Move ${diagram.name} to workspace`"
                              >
                                <FolderIcon class="h-4 w-4" aria-hidden="true" />
                              </button>
                              <!-- Workspace dropdown -->
                              <div
                                v-if="workspaceDropdownId === diagram.id"
                                class="absolute right-0 top-full mt-1 z-20 bg-gray-900 border border-gray-700 rounded-lg shadow-xl py-1 min-w-44"
                                role="menu"
                              >
                                <button
                                  v-for="ws in workspaces"
                                  :key="ws.id"
                                  @click="assignWorkspace(diagram, ws.id, $event)"
                                  class="flex items-center gap-2 w-full text-left px-3 py-1.5 text-sm hover:bg-gray-700 transition-colors"
                                  :class="{ 'text-blue-400': diagram.workspaceId === ws.id }"
                                  role="menuitem"
                                >
                                  <FolderIcon class="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
                                  {{ ws.name }}
                                </button>
                                <div class="border-t border-gray-700 mt-1 pt-1">
                                  <button
                                    @click="assignWorkspace(diagram, null, $event)"
                                    class="flex items-center gap-2 w-full text-left px-3 py-1.5 text-sm hover:bg-gray-700 transition-colors"
                                    :class="{ 'text-blue-400': diagram.workspaceId === null }"
                                    role="menuitem"
                                  >
                                    <XMarkIcon class="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
                                    Remove from workspace
                                  </button>
                                </div>
                              </div>
                            </div>

                            <!-- Delete: normal -->
                            <button
                              v-if="deletingId !== diagram.id"
                              @click="requestDelete(diagram.id, $event)"
                              class="p-1.5 rounded text-gray-500 hover:text-red-400 hover:bg-red-400/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
                              :aria-label="`Delete ${diagram.name}`"
                            >
                              <TrashIcon class="h-4 w-4" aria-hidden="true" />
                            </button>

                            <!-- Delete: confirm -->
                            <div v-else class="flex items-center gap-1.5 text-xs px-1">
                              <span class="text-gray-400">Delete?</span>
                              <button
                                @click="confirmDelete(diagram.id, $event)"
                                :disabled="deleteInProgress === diagram.id"
                                class="text-red-400 hover:text-red-300 font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 rounded px-1 disabled:opacity-50"
                              >Yes</button>
                              <button
                                @click="cancelDelete($event)"
                                class="text-gray-400 hover:text-gray-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded px-1"
                              >Cancel</button>
                            </div>
                          </div>
                        </div>
                      </template>

                      <!-- Rename inline input -->
                      <form
                        v-else
                        @submit.prevent="submitRename(diagram)"
                        @click.stop
                        class="flex-1 flex items-center gap-2 px-3 py-2 min-w-0"
                      >
                        <input
                          v-model="renameValue"
                          @keydown.escape="cancelRename"
                          class="flex-1 min-w-0 text-sm bg-gray-700 border border-blue-500 rounded px-2 py-0.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          aria-label="Rename diagram"
                          autofocus
                        />
                        <button type="submit" :disabled="renameInProgress" class="text-xs text-blue-400 hover:text-blue-200 flex-shrink-0 disabled:opacity-50">Save</button>
                        <button type="button" @click.prevent="cancelRename" class="text-xs text-gray-400 hover:text-gray-200 flex-shrink-0">Cancel</button>
                      </form>
                    </div>
                  </div>

                </li>
              </ul>
            </section>

            <!-- No results for search -->
            <p v-if="filteredGroups.every(g => g.diagrams.length === 0) && searchQuery" class="text-center text-gray-500 text-sm py-8">
              No diagrams or workspaces match "{{ searchQuery }}"
            </p>
          </div>
        </template>
      </main>
    </div>
  </div>

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
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-gray-950/80 backdrop-blur-sm" aria-hidden="true" />

        <!-- Panel -->
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
            <!-- Header -->
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

            <!-- Form -->
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
                :aria-describedby="creatingWorkspace ? 'ws-creating' : undefined"
              />

              <!-- Actions -->
              <div class="flex items-center justify-end gap-2 mt-5">
                <button
                  type="button"
                  @click="closeWorkspaceModal"
                  class="px-3 py-1.5 text-sm text-gray-400 hover:text-gray-200 transition-colors rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  :disabled="creatingWorkspace || !newWorkspaceName.trim()"
                  class="flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
                >
                  <span id="ws-creating" v-if="creatingWorkspace">Creating…</span>
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
