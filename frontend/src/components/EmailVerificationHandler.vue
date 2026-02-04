<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { authApi } from '../lib/api';

const loading = ref(true);
const error = ref('');
const success = ref(false);

onMounted(async () => {
  try {
    // Extract uid and token from URL query parameters on the client side
    const urlParams = new URLSearchParams(window.location.search);
    const uid = urlParams.get('uid');
    const token = urlParams.get('token');

    if (!uid || !token) {
      error.value = 'Invalid verification link. Missing uid or token.';
      loading.value = false;
      return;
    }

    await authApi.verifyEmail(uid, token);
    success.value = true;
    // Redirect to diagrams after 2 seconds
    setTimeout(() => {
      window.location.href = '/diagrams';
    }, 2000);
  } catch (err: any) {
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail;
    } else {
      error.value = 'Verification failed. Please try again or request a new verification email.';
    }
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-900">
    <div class="max-w-md w-full space-y-8 p-8 bg-gray-800 rounded-lg shadow-lg">
      <div>
        <h2 class="text-center text-3xl font-bold text-white">
          Email Verification
        </h2>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="text-center">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <p class="mt-4 text-gray-400">Verifying your email...</p>
      </div>

      <!-- Success state -->
      <div v-else-if="success" class="space-y-4">
        <div class="bg-green-500/10 border border-green-500 text-green-400 px-4 py-3 rounded">
          <p class="font-semibold">Email verified successfully!</p>
          <p class="text-sm mt-1">You are now logged in. Redirecting to your diagrams...</p>
        </div>
      </div>

      <!-- Error state -->
      <div v-else class="space-y-4">
        <div class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded">
          {{ error }}
        </div>

        <div class="space-y-2">
          <a
            href="/auth/verification-pending"
            class="block w-full text-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            Request New Verification Email
          </a>
          <a
            href="/login"
            class="block w-full text-center py-2 px-4 border border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600"
          >
            Back to Login
          </a>
        </div>
      </div>
    </div>
  </div>
</template>
