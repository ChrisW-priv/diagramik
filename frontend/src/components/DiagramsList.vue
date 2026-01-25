<script setup lang="ts">
import { ref, onMounted } from 'vue';
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

onMounted(async () => {
  // Check auth on client side
  if (!isAuthenticated()) {
    window.location.href = '/login';
    return;
  }

  displayName.value = getDisplayName();

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
    error.value = 'Failed to load diagrams';
    console.error('Failed to fetch diagrams:', err);
  } finally {
    loading.value = false;
  }
});

const handleLogout = async () => {
  await authApi.logout();
  window.location.href = '/login';
};
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-4xl font-bold">My Diagrams</h1>
        <p v-if="displayName" class="text-gray-400 mt-1">
          Welcome, {{ displayName }}
        </p>
      </div>
      <div class="flex gap-4">
        <a href="/diagrams/new" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
          Create New
        </a>
        <button @click="handleLogout" class="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded">
          Logout
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-gray-400">Loading diagrams...</div>

    <div v-else-if="error" class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded">
      {{ error }}
    </div>

    <ul v-else class="space-y-4">
      <p v-if="diagrams.length === 0" class="text-gray-400">
        No diagrams found. <a href="/diagrams/new" class="text-blue-400 hover:underline">Create one</a> to get started!
      </p>
      <li v-for="diagram in diagrams" :key="diagram.id">
        <a :href="`/diagrams/view?id=${diagram.id}`" class="block p-6 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors duration-200">
          <h2 class="text-2xl font-semibold">{{ diagram.name }}</h2>
        </a>
      </li>
    </ul>
  </div>
</template>
