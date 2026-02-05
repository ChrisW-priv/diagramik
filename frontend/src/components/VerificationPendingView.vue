<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { ArrowPathIcon } from '@heroicons/vue/24/outline';
import { authApi } from '../lib/api';

const props = defineProps<{
  initialEmail?: string;
}>();

const email = ref(props.initialEmail || '');
const error = ref('');
const success = ref(false);
const loading = ref(false);
const resendCount = ref(0);
const maxResends = ref(5);
const cooldownMinutes = ref(0);
const cooldownInterval = ref<number | null>(null);

const canResend = computed(() => !loading.value && cooldownMinutes.value === 0);

onMounted(() => {
  // Try to get email from multiple sources (in order of priority):
  // 1. Props (initialEmail)
  // 2. URL query parameter
  // 3. localStorage

  if (!email.value) {
    // Check URL query parameters
    const urlParams = new URLSearchParams(window.location.search);
    const emailParam = urlParams.get('email');
    if (emailParam) {
      email.value = emailParam;
    } else {
      // Fallback to localStorage if no URL param
      const savedEmail = localStorage.getItem('verification_email');
      if (savedEmail) {
        email.value = savedEmail;
      }
    }
  }

  // Focus email field if not pre-filled
  if (!email.value) {
    document.getElementById('email')?.focus();
  }
});

onUnmounted(() => {
  if (cooldownInterval.value) {
    clearInterval(cooldownInterval.value);
  }
});

const startCooldownTimer = (minutes: number) => {
  cooldownMinutes.value = minutes;

  // Clear existing interval
  if (cooldownInterval.value) {
    clearInterval(cooldownInterval.value);
  }

  // Countdown every minute
  cooldownInterval.value = window.setInterval(() => {
    cooldownMinutes.value--;
    if (cooldownMinutes.value <= 0) {
      if (cooldownInterval.value) {
        clearInterval(cooldownInterval.value);
      }
    }
  }, 60000);
};

const handleSubmit = async () => {
  error.value = '';
  success.value = false;
  loading.value = true;

  try {
    const response = await authApi.resendVerification(email.value);
    success.value = true;
    resendCount.value = response.resend_count || 0;
    maxResends.value = response.max_resends || 5;

    // Save email to localStorage for future autofill
    localStorage.setItem('verification_email', email.value);

    // Start 10-minute cooldown
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
      error.value = err.response.data.detail || 'Email is already verified.';
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
          Verify Your Email
        </h2>
        <p class="mt-2 text-center text-sm text-gray-400">
          We've sent a verification link to your email address.
          Check your inbox and click the link to activate your account.
        </p>
      </div>

      <div v-if="error" class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded">
        {{ error }}
      </div>

      <div v-if="success" class="bg-green-500/10 border border-green-500 text-green-400 px-4 py-3 rounded">
        <p class="font-semibold">Verification email sent!</p>
        <p class="text-sm mt-1">Please check your inbox for the verification link.</p>
        <p class="text-xs mt-2 text-gray-400">
          Attempts: {{ resendCount }} of {{ maxResends }}
        </p>
      </div>

      <div class="bg-blue-500/10 border border-blue-400 text-blue-300 px-4 py-3 rounded text-sm">
        <p class="font-semibold">Haven't received the email?</p>
        <ul class="mt-2 ml-4 list-disc space-y-1">
          <li>Check your spam/junk folder</li>
          <li>Make sure the email address is correct</li>
          <li>Request a new verification email below</li>
        </ul>
      </div>

      <form class="space-y-6" @submit.prevent="handleSubmit">
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
            inputmode="email"
            spellcheck="false"
            required
            :disabled="loading"
            class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            placeholder="Enter your email"
          />
        </div>

        <button
          type="submit"
          :disabled="!canResend"
          class="w-full flex items-center justify-center p-3 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Resend verification email"
          title="Resend verification email"
        >
          <ArrowPathIcon class="h-6 w-6" :class="{ 'animate-spin': loading }" />
        </button>
      </form>

      <p class="text-center text-sm text-gray-400">
        Already verified?
        <a href="/login" class="text-blue-400 hover:text-blue-300">
          Sign in
        </a>
      </p>
    </div>
  </div>
</template>
