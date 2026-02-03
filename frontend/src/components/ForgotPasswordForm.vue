<script setup lang="ts">
import { ref, computed } from 'vue';
import { authApi } from '../lib/api';

const email = ref('');
const error = ref('');
const success = ref(false);
const loading = ref(false);
const actionRequired = ref<string | null>(null);
const cooldownMinutes = ref(0);
const cooldownInterval = ref<number | null>(null);

const canSubmit = computed(() => !loading.value && cooldownMinutes.value === 0 && email.value.trim() !== '');

const startCooldownTimer = (minutes: number) => {
  cooldownMinutes.value = minutes;

  // Clear existing interval
  if (cooldownInterval.value) {
    clearInterval(cooldownInterval.value);
  }

  // Countdown every minute
  cooldownInterval.value = setInterval(() => {
    cooldownMinutes.value--;
    if (cooldownMinutes.value <= 0) {
      if (cooldownInterval.value) {
        clearInterval(cooldownInterval.value);
      }
    }
  }, 60000) as unknown as number;
};

const handleSubmit = async () => {
  error.value = '';
  success.value = false;
  actionRequired.value = null;
  loading.value = true;

  try {
    const response = await authApi.requestPasswordResetNew(email.value);
    success.value = true;

    // Check if user needs to verify email first
    if (response.action_required === 'verify_email') {
      actionRequired.value = 'verify_email';
    }

    // Start cooldown timer
    startCooldownTimer(10);

  } catch (err: any) {
    if (err.response?.status === 429) {
      // Rate limit error - extract minutes from message
      const detail = err.response.data.detail || '';
      const match = detail.match(/(\d+) more minute/);
      if (match) {
        const minutes = parseInt(match[1]);
        startCooldownTimer(minutes);
        error.value = detail;
      } else {
        error.value = err.response.data.detail || 'Too many requests. Please try again later.';
      }
    } else if (err.response?.status === 400) {
      error.value = err.response.data.detail || 'Please enter a valid email address.';
    } else if (err.response?.status === 500) {
      error.value = 'Failed to send email. Please try again later.';
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

      <div v-if="success && actionRequired === 'verify_email'" class="bg-yellow-500/10 border border-yellow-500 text-yellow-400 px-4 py-3 rounded">
        <p class="font-semibold">Email verification required</p>
        <p class="text-sm mt-1">
          Your email is not verified. We've sent you a verification email instead. Please verify your email before resetting your password.
        </p>
        <div class="mt-3">
          <a
            :href="`/auth/verification-pending?email=${encodeURIComponent(email)}`"
            class="inline-block text-yellow-300 hover:text-yellow-200 underline text-sm"
          >
            Go to verification page
          </a>
        </div>
      </div>

      <div v-else-if="success" class="bg-green-500/10 border border-green-500 text-green-400 px-4 py-3 rounded">
        <p class="font-semibold">Password reset email sent!</p>
        <p class="text-sm mt-1">
          If an account exists with this email, you will receive password reset instructions. Please check your inbox and spam folder.
        </p>
      </div>

      <form class="mt-8 space-y-6" @submit.prevent="handleSubmit">
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
          :disabled="!canSubmit"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading">Sending...</span>
          <span v-else-if="cooldownMinutes > 0">Wait {{ cooldownMinutes }} minute{{ cooldownMinutes === 1 ? '' : 's' }}</span>
          <span v-else>Send reset link</span>
        </button>

        <div class="text-center space-y-2">
          <p class="text-sm text-gray-400">
            Remember your password?
            <a href="/login" class="text-blue-400 hover:text-blue-300">
              Sign in
            </a>
          </p>
          <p class="text-sm text-gray-400">
            Don't have an account?
            <a href="/auth/register" class="text-blue-400 hover:text-blue-300">
              Sign up
            </a>
          </p>
        </div>
      </form>
    </div>
  </div>
</template>
