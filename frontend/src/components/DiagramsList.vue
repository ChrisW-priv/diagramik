<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ExclamationCircleIcon, ArrowPathIcon, PlusCircleIcon, BookOpenIcon, ArrowRightOnRectangleIcon } from '@heroicons/vue/24/outline';
import { getDiagrams, authApi } from '../lib/api';
import { isAuthenticated } from '../lib/auth';

interface Diagram {
  id: number;
  name: string;
  updatedAt: string;
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

const diagrams = ref<Diagram[]>([]);
const loading = ref(true);
const error = ref('');

const fetchDiagrams = async () => {
  loading.value = true;
  error.value = '';

  try {
    const response = await getDiagrams();
    diagrams.value = response.data
      .map((d: any) => ({
        id: d.id,
        name: d.title,
        updatedAt: d.updated_at,
      }))
      .sort((a: Diagram, b: Diagram) =>
        new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
      );
  } catch (err: any) {
    if (err.response?.status === 401) {
      // Will be handled by interceptor, but just in case
      return;
    }

    // More descriptive error messages
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
      if (!navigator.onLine) {
        error.value = 'No internet connection. Please check your network and try again.';
      } else {
        error.value = 'Network timeout. Please check your connection and try again.';
      }
    } else {
      error.value = 'An unexpected error occurred while loading diagrams.';
    }

    console.error('Failed to fetch diagrams:', err);
  } finally {
    loading.value = false;
  }
};

const retryFetch = () => {
  fetchDiagrams();
};

onMounted(async () => {
  // Check auth on client side
  if (!isAuthenticated()) {
    window.location.href = '/login';
    return;
  }

  await fetchDiagrams();
});

const handleLogout = async () => {
  await authApi.logout();
  window.location.href = '/login';
};
</script>

<template>
  <main id="main-content" class="container mx-auto px-2 py-4 md:px-4 md:py-8">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl md:text-3xl font-bold">My Diagrams</h1>
      </div>
      <div class="flex gap-3 sm:gap-4">
        <a
          href="/diagrams/new"
          aria-label="New diagram"
          class="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 px-3 py-2.5 rounded-lg transition-colors min-h-12 min-w-12 sm:min-h-auto sm:min-w-auto"
        >
          <PlusCircleIcon class="h-5 w-5 flex-shrink-0" aria-hidden="true" />
          <span class="hidden sm:inline text-sm font-medium">New diagram</span>
        </a>
        <a
          href="/guide"
          aria-label="Guide"
          class="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 px-3 py-2.5 rounded-lg transition-colors min-h-12 min-w-12 sm:min-h-auto sm:min-w-auto"
        >
          <BookOpenIcon class="h-5 w-5 flex-shrink-0" aria-hidden="true" />
          <span class="hidden sm:inline text-sm font-medium">Guide</span>
        </a>
        <button
          @click="handleLogout"
          aria-label="Sign out"
          class="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 px-3 py-2.5 rounded-lg transition-colors min-h-12 min-w-12 sm:min-h-auto sm:min-w-auto"
        >
          <ArrowRightOnRectangleIcon class="h-5 w-5 flex-shrink-0" aria-hidden="true" />
          <span class="hidden sm:inline text-sm font-medium">Sign out</span>
        </button>
      </div>
    </div>

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

    <div v-else-if="error" aria-live="assertive" role="alert" class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded flex items-start gap-3">
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

    <ul v-else class="space-y-4">
      <li v-if="diagrams.length === 0" class="text-center py-12">
        <p class="text-gray-400 mb-4">
          No diagrams found yet.
        </p>
        <p class="text-sm text-gray-500 mb-6">
          Create your first diagram to get started with Diagramik.
        </p>
        <a href="/diagrams/new" class="inline-block bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 px-6 py-3 rounded-lg text-white font-medium transition-colors">
          Create your first diagram
        </a>
      </li>
      <li v-for="diagram in diagrams" :key="diagram.id">
        <a
          :href="`/diagrams/view?id=${diagram.id}`"
          class="flex items-center justify-between gap-4 px-3 py-3 md:px-4 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors duration-200 group"
        >
          <h2
            class="text-sm font-medium truncate group-hover:text-blue-400 transition-colors"
            :title="diagram.name"
          >{{ diagram.name }}</h2>
          <time
            :datetime="diagram.updatedAt"
            class="flex-shrink-0 text-xs text-gray-500 tabular-nums"
            :title="new Date(diagram.updatedAt).toLocaleString()"
          >{{ formatRelativeTime(diagram.updatedAt) }}</time>
        </a>
      </li>
    </ul>
  </main>
</template>
