<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { LockClosedIcon, ArrowPathIcon } from '@heroicons/vue/24/outline';
import { authApi } from '../lib/api';

const props = defineProps<{
  uid?: string;
  token?: string;
}>();

// Form fields
const email = ref('');
const oldPassword = ref('');
const newPassword = ref('');
const confirmPassword = ref('');

// State
const error = ref('');
const success = ref(false);
const loading = ref(false);
const isTokenMethod = ref(false);

// Computed
const passwordsMatch = computed(() => newPassword.value === confirmPassword.value);
const canSubmit = computed(() => {
  if (loading.value) return false;
  if (!newPassword.value || !confirmPassword.value) return false;
  if (!passwordsMatch.value) return false;
  
  if (isTokenMethod.value) {
    return props.uid && props.token;
  } else {
    return email.value && oldPassword.value;
  }
});

onMounted(() => {
  // Determine authentication method
  isTokenMethod.value = !!(props.uid && props.token);
});

const handleSubmit = async () => {
  error.value = '';
  success.value = false;

  // Validate passwords match
  if (!passwordsMatch.value) {
    error.value = 'Passwords do not match.';
    return;
  }

  // Validate password length
  if (newPassword.value.length < 8) {
    error.value = 'Password must be at least 8 characters long.';
    return;
  }

  loading.value = true;

  try {
    let response;

    if (isTokenMethod.value) {
      // Email token method
      response = await authApi.setNewPassword(
        props.uid,
        props.token,
        undefined,
        undefined,
        newPassword.value
      );
    } else {
      // Old password method
      response = await authApi.setNewPassword(
        undefined,
        undefined,
        email.value,
        oldPassword.value,
        newPassword.value
      );
    }

    success.value = true;

    // Auto-redirect to diagrams after 2 seconds
    setTimeout(() => {
      window.location.href = '/diagrams';
    }, 2000);

  } catch (err: any) {
    if (err.response?.status === 400) {
      error.value = err.response.data.detail || 'Invalid request. Please try again.';
    } else if (err.response?.status === 401) {
      error.value = err.response.data.detail || 'Invalid email or password.';
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
          Set New Password
        </h2>
        <p class="mt-2 text-center text-sm text-gray-400">
          <span v-if="isTokenMethod">Enter your new password below</span>
          <span v-else>Enter your current password and new password</span>
        </p>
      </div>

      <div v-if="error" class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded">
        {{ error }}
      </div>

      <div v-if="success" class="bg-green-500/10 border border-green-500 text-green-400 px-4 py-3 rounded">
        <p class="font-semibold">Password changed successfully!</p>
        <p class="text-sm mt-1">You are now logged in. Redirecting to your diagrams...</p>
      </div>

      <form class="space-y-6" @submit.prevent="handleSubmit">
        <!-- Old Password Method Fields -->
        <div v-if="!isTokenMethod" class="space-y-4">
          <div>
            <label for="email" class="block text-sm font-medium text-gray-300">
              Email Address
            </label>
            <input
              id="email"
              v-model="email"
              name="email"
              type="email"
              autocomplete="email"
              required
              :disabled="loading"
              class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              placeholder="Enter your email"
            />
          </div>

          <div>
            <label for="old-password" class="block text-sm font-medium text-gray-300">
              Current Password
            </label>
            <input
              id="old-password"
              v-model="oldPassword"
              name="old-password"
              type="password"
              autocomplete="current-password"
              required
              :disabled="loading"
              class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              placeholder="Enter your current password"
            />
          </div>
        </div>

        <!-- New Password Fields (both methods) -->
        <div class="space-y-4">
          <div>
            <label for="new-password" class="block text-sm font-medium text-gray-300">
              New Password
            </label>
            <input
              id="new-password"
              v-model="newPassword"
              name="new-password"
              type="password"
              autocomplete="new-password"
              required
              :disabled="loading"
              class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              placeholder="Enter new password"
            />
            <p class="mt-1 text-xs text-gray-400">
              Must be at least 8 characters long
            </p>
          </div>

          <div>
            <label for="confirm-password" class="block text-sm font-medium text-gray-300">
              Confirm New Password
            </label>
            <input
              id="confirm-password"
              v-model="confirmPassword"
              name="confirm-password"
              type="password"
              autocomplete="new-password"
              required
              :disabled="loading"
              class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              :class="{ 'border-red-500': confirmPassword && !passwordsMatch }"
              placeholder="Confirm new password"
            />
            <p v-if="confirmPassword && !passwordsMatch" class="mt-1 text-xs text-red-400">
              Passwords do not match
            </p>
          </div>
        </div>

        <button
          type="submit"
          :disabled="!canSubmit"
          class="w-full flex items-center justify-center p-3 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Set new password"
          title="Set new password"
        >
          <ArrowPathIcon v-if="loading" class="h-6 w-6 animate-spin" />
          <LockClosedIcon v-else class="h-6 w-6" />
        </button>
      </form>

      <p class="text-center text-sm text-gray-400">
        <a href="/login" class="text-blue-400 hover:text-blue-300">
          Back to login
        </a>
      </p>
    </div>
  </div>
</template>
