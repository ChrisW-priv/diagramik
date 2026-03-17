<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue';
import { EnvelopeIcon, ArrowPathIcon } from '@heroicons/vue/24/outline';
import { authApi } from '../lib/api';
import FormContainer from './base/FormContainer.vue';
import FormField from './base/FormField.vue';
import AlertError from './base/AlertError.vue';
import AlertSuccess from './base/AlertSuccess.vue';
import AlertWarning from './base/AlertWarning.vue';

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

// Cleanup interval on unmount
onUnmounted(() => {
  if (cooldownInterval.value) {
    clearInterval(cooldownInterval.value);
  }
});
</script>

<template>
  <FormContainer title="Reset your password" subtitle="Enter your email and we'll send you a reset link">
    <!-- Error Alert -->
    <AlertError v-if="error" :message="error" dismissible @dismiss="error = ''" />

    <!-- Email Verification Required -->
    <AlertWarning
      v-if="success && actionRequired === 'verify_email'"
      message="Your email is not verified. We've sent you a verification email instead. Please verify your email before resetting your password."
    />
    <div v-if="success && actionRequired === 'verify_email'" class="mt-2">
      <a
        :href="`/auth/verification-pending?email=${encodeURIComponent(email)}`"
        class="inline-block text-yellow-300 hover:text-yellow-200 underline text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-yellow-400 rounded px-1"
      >
        Go to verification page
      </a>
    </div>

    <!-- Success Alert -->
    <AlertSuccess
      v-if="success && !actionRequired"
      message="Password reset email sent! If an account exists with this email, you will receive password reset instructions. Please check your inbox and spam folder."
    />

    <!-- Form -->
    <form class="space-y-4" @submit.prevent="handleSubmit">
      <FormField
        id="email"
        v-model="email"
        label="Email address"
        type="email"
        required
        autocomplete="email"
        placeholder="Enter your email"
        :error="error ? error : undefined"
      />

      <button
        type="submit"
        :disabled="!canSubmit"
        :aria-busy="loading"
        class="w-full flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 focus-visible:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none transition-colors font-medium"
      >
        <ArrowPathIcon
          v-if="loading || cooldownMinutes > 0"
          class="h-5 w-5"
          :class="{ 'animate-spin': loading }"
          aria-hidden="true"
        />
        <EnvelopeIcon v-else class="h-5 w-5 mr-2" aria-hidden="true" />
        <span>{{ loading ? 'Sending...' : cooldownMinutes > 0 ? `Try again in ${cooldownMinutes}m` : 'Send reset link' }}</span>
      </button>
    </form>

    <!-- Links -->
    <div class="space-y-3 text-center">
      <p class="text-sm text-gray-400">
        Remember your password?
        <a href="/login" class="text-blue-400 hover:text-blue-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded px-1">
          Sign in
        </a>
      </p>
      <p class="text-sm text-gray-400">
        Don't have an account?
        <a href="/auth/register" class="text-blue-400 hover:text-blue-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded px-1">
          Sign up
        </a>
      </p>
    </div>
  </FormContainer>
</template>
