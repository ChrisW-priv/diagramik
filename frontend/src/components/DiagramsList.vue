<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ExclamationCircleIcon, ArrowPathIcon, PlusCircleIcon, ArrowRightOnRectangleIcon } from '@heroicons/vue/24/outline';
import { getDiagrams, authApi } from '../lib/api';
import { isAuthenticated, getDisplayName } from '../lib/auth';

interface Diagram {
  id: number;
  name: string;
  updatedAt: string;
}

const diagrams = ref<Diagram[]>([]);
const loading = ref(true);
const error = ref('');
const displayName = ref('');

const fetchDiagrams = async () => {
  loading.value = true;
  error.value = '';

  try {
    const response = await getDiagrams();
    diagrams.value = response.data.map((d: any) => ({
      id: d.id,
      name: d.title,
      updatedAt: d.created_at,
    }));
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

  displayName.value = getDisplayName();
  await fetchDiagrams();
});

const handleLogout = async () => {
  await authApi.logout();
  window.location.href = '/login';
};
</script>

<template>
  <div class="container mx-auto px-2 py-4 md:px-4 md:py-8">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl md:text-4xl font-bold">My Diagrams</h1>
        <p v-if="displayName" class="text-gray-400 mt-1">
          Welcome, {{ displayName }}
        </p>
      </div>
      <div class="flex gap-4">
        <a
          href="/diagrams/new"
          class="flex items-center justify-center bg-blue-500 hover:bg-blue-700 p-3 rounded-lg transition-colors"
          aria-label="Create new diagram"
          title="Create new diagram"
        >
          <PlusCircleIcon class="h-6 w-6" />
        </a>
        <button
          @click="handleLogout"
          class="flex items-center justify-center bg-gray-600 hover:bg-gray-700 p-3 rounded-lg transition-colors"
          aria-label="Logout"
          title="Logout"
        >
          <ArrowRightOnRectangleIcon class="h-6 w-6" />
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-gray-400">Loading diagrams...</div>

    <div v-else-if="error" class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded flex items-start gap-3">
      <ExclamationCircleIcon class="h-6 w-6 flex-shrink-0 mt-0.5" />
      <div class="flex-grow">
        <p>{{ error }}</p>
        <button
          @click="retryFetch"
          class="flex items-center gap-2 mt-2 text-sm text-red-300 hover:text-red-100 underline"
        >
          <ArrowPathIcon class="h-4 w-4" />
          Try Again
        </button>
      </div>
    </div>

    <ul v-else class="space-y-4">
      <p v-if="diagrams.length === 0" class="text-gray-400">
        No diagrams found. <a href="/diagrams/new" class="text-blue-400 hover:underline">Create one</a> to get started!
      </p>
      <li v-for="diagram in diagrams" :key="diagram.id">
        <a :href="`/diagrams/view?id=${diagram.id}`" class="block p-3 md:p-6 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors duration-200">
          <h2 class="text-lg md:text-2xl font-semibold">{{ diagram.name }}</h2>
        </a>
      </li>
    </ul>
  </div>
</template>
