<script setup lang="ts">
import { ref } from 'vue';
import { authApi } from '../lib/api';

const email = ref('');
const error = ref('');
const success = ref(false);
const loading = ref(false);

const handleSubmit = async () => {
  error.value = '';
  loading.value = true;

  try {
    await authApi.requestPasswordReset(email.value);
    success.value = true;
  } catch (err: any) {
    if (err.response?.data?.email) {
      error.value = err.response.data.email[0];
    } else {
      error.value = 'An error occurred. Please try again.';
    }
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-900">
    <div class="max-w-md w-full space-y-8 p-8 bg-gray-800 rounded-lg shadow-lg">
      <div>
        <h2 class="text-center text-3xl font-bold text-white">
          Reset your password
        </h2>
        <p class="mt-2 text-center text-sm text-gray-400">
          Enter your email and we'll send you a reset link
        </p>
      </div>

      <div v-if="error" class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded">
        {{ error }}
      </div>

      <div v-if="success" class="space-y-6">
        <div class="bg-green-500/10 border border-green-500 text-green-400 px-4 py-3 rounded">
          <p>If an account with that email exists, we've sent a password reset link.</p>
          <p class="mt-2">Please check your email and follow the instructions.</p>
        </div>
        <a
          href="/login"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Back to login
        </a>
      </div>

      <form v-else class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div>
          <label for="email" class="block text-sm font-medium text-gray-300">
            Email address
          </label>
          <input
            id="email"
            v-model="email"
            name="email"
            type="email"
            autocomplete="email"
            required
            class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter your email"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading">Sending...</span>
          <span v-else>Send reset link</span>
        </button>

        <p class="text-center text-sm text-gray-400">
          Remember your password?
          <a href="/login" class="text-blue-400 hover:text-blue-300">
            Sign in
          </a>
        </p>
      </form>
    </div>
  </div>
</template>
