<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { setTokens } from '../lib/auth';

const error = ref('');
const loading = ref(true);

onMounted(async () => {
  const urlParams = new URLSearchParams(window.location.search);

  // Check for OAuth pending flow (new user needs to accept terms)
  const oauthPending = urlParams.get('oauth_pending');
  const stateToken = urlParams.get('state');

  if (oauthPending === 'google' && stateToken) {
    // New user - redirect to register with state
    window.location.href = `/auth/register?oauth_pending=google&state=${encodeURIComponent(stateToken)}`;
    return;
  }

  const accessToken = urlParams.get('access');
  const refreshToken = urlParams.get('refresh');
  const errorParam = urlParams.get('error');

  if (errorParam) {
    error.value = 'Google sign-in was cancelled or failed.';
    loading.value = false;
    return;
  }

  if (!accessToken || !refreshToken) {
    error.value = 'No tokens received from authentication server.';
    loading.value = false;
    return;
  }

  try {
    // Store tokens
    setTokens({ access: accessToken, refresh: refreshToken });

    // Redirect to diagrams page
    window.location.href = '/diagrams';
  } catch (err: any) {
    error.value = 'Failed to complete Google sign-in. Please try again.';
    loading.value = false;
  }
});
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-900">
    <div class="max-w-md w-full space-y-4 md:space-y-8 p-4 md:p-8 bg-gray-800 rounded-lg shadow-lg text-center">
      <div v-if="loading" class="space-y-4">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
        <p class="text-gray-300">Completing Google sign-in...</p>
      </div>

      <div v-else class="space-y-6">
        <div class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded">
          {{ error }}
        </div>
        <a
          href="/login"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Back to login
        </a>
      </div>
    </div>
  </div>
</template>
