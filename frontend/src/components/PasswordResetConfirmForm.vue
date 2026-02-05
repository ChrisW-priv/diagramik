<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { LockClosedIcon, ArrowPathIcon, ArrowRightCircleIcon } from '@heroicons/vue/24/outline';
import { authApi } from '../lib/api';

const uid = ref('');
const token = ref('');
const password1 = ref('');
const password2 = ref('');
const error = ref('');
const success = ref(false);
const loading = ref(false);
const invalidLink = ref(false);

onMounted(() => {
  // Parse uid and token from URL path: /auth/password-reset?uid=xxx&token=yyy
  const urlParams = new URLSearchParams(window.location.search);
  uid.value = urlParams.get('uid') || '';
  token.value = urlParams.get('token') || '';

  if (!uid.value || !token.value) {
    invalidLink.value = true;
  }
});

const handleSubmit = async () => {
  error.value = '';
  loading.value = true;

  if (password1.value !== password2.value) {
    error.value = 'Passwords do not match';
    loading.value = false;
    return;
  }

  try {
    await authApi.confirmPasswordReset(
      uid.value,
      token.value,
      password1.value,
      password2.value
    );
    success.value = true;
  } catch (err: any) {
    if (err.response?.data) {
      const data = err.response.data;
      if (data.new_password1) {
        error.value = data.new_password1[0];
      } else if (data.new_password2) {
        error.value = data.new_password2[0];
      } else if (data.token) {
        error.value = 'This password reset link is invalid or has expired.';
      } else if (data.uid) {
        error.value = 'This password reset link is invalid.';
      } else {
        error.value = 'Failed to reset password. Please try again.';
      }
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
    <div class="max-w-md w-full space-y-4 md:space-y-8 p-4 md:p-8 bg-gray-800 rounded-lg shadow-lg">
      <div>
        <h2 class="text-center text-2xl md:text-3xl font-bold text-white">
          Set new password
        </h2>
        <p class="mt-2 text-center text-sm text-gray-400">
          Enter your new password below
        </p>
      </div>

      <div v-if="invalidLink" class="space-y-6">
        <div class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded">
          This password reset link is invalid. Please request a new one.
        </div>
        <a
          href="/auth/forgot-password"
          class="w-full flex items-center justify-center p-3 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          aria-label="Request new link"
          title="Request new link"
        >
          <ArrowPathIcon class="h-6 w-6" />
        </a>
      </div>

      <div v-else-if="error" class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded">
        {{ error }}
      </div>

      <div v-if="success" class="space-y-6">
        <div class="bg-green-500/10 border border-green-500 text-green-400 px-4 py-3 rounded">
          Your password has been reset successfully!
        </div>
        <a
          href="/login"
          class="w-full flex items-center justify-center p-3 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          aria-label="Go to login"
          title="Go to login"
        >
          <ArrowRightCircleIcon class="h-6 w-6" />
        </a>
      </div>

      <form v-else-if="!invalidLink" class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <div>
            <label for="password1" class="block text-sm font-medium text-gray-300">
              New Password
            </label>
            <input
              id="password1"
              v-model="password1"
              name="password1"
              type="password"
              autocomplete="new-password"
              required
              class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter new password"
            />
          </div>
          <div>
            <label for="password2" class="block text-sm font-medium text-gray-300">
              Confirm New Password
            </label>
            <input
              id="password2"
              v-model="password2"
              name="password2"
              type="password"
              autocomplete="new-password"
              required
              class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Confirm new password"
            />
          </div>
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full flex items-center justify-center p-3 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Reset password"
          title="Reset password"
        >
          <ArrowPathIcon v-if="loading" class="h-6 w-6 animate-spin" />
          <LockClosedIcon v-else class="h-6 w-6" />
        </button>
      </form>
    </div>
  </div>
</template>
