<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ArrowRightCircleIcon, ArrowPathIcon } from '@heroicons/vue/24/outline';
import { authApi } from '../lib/api';

// Google OAuth configuration
const GOOGLE_CLIENT_ID = import.meta.env.PUBLIC_GOOGLE_CLIENT_ID ||
  '904069135998-4h84vjsjnjvo5d442gsqvlummq6ebdj3.apps.googleusercontent.com';

const API_BASE_URL = import.meta.env.PROD
  ? 'https://diagramik.com'
  : 'http://localhost:8000';

const email = ref('');
const password = ref('');
const error = ref('');
const sessionMessage = ref('');
const loading = ref(false);
const googleLoading = ref(false);
const acceptedTerms = ref(false);

// Check for session expiration or other reasons
onMounted(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const reason = urlParams.get('reason');

  if (reason === 'session_expired') {
    sessionMessage.value = 'Your session has expired. Please sign in again.';
  } else if (reason) {
    sessionMessage.value = decodeURIComponent(reason);
  }

  // Clean URL after reading parameter
  if (reason && window.history.replaceState) {
    const cleanUrl = window.location.pathname;
    window.history.replaceState({}, document.title, cleanUrl);
  }
});

const handleSubmit = async () => {
  error.value = '';
  loading.value = true;

  try {
    await authApi.login(email.value, password.value);
    window.location.href = '/diagrams';
  } catch (err: any) {
    if (err.response?.status === 403) {
      const errorCode = err.response.data.error_code;

      if (errorCode === 'EMAIL_NOT_VERIFIED') {
        // Redirect to verification-pending page with email pre-filled
        window.location.href = `/auth/verification-pending?email=${encodeURIComponent(email.value)}`;
        return;
      } else if (errorCode === 'ACCOUNT_DISABLED') {
        error.value = 'Your account has been disabled. Please contact support.';
        return;
      }
    }

    if (err.response?.status === 400 || err.response?.status === 401) {
      error.value = 'Invalid email or password';
    } else {
      error.value = 'An error occurred. Please try again.';
    }
  } finally {
    loading.value = false;
  }
};

const handleGoogleLogin = () => {
  googleLoading.value = true;
  error.value = '';

  const redirectUri = `${API_BASE_URL}/api/v1/auth/social/google/`;
  const scope = 'openid email profile';
  const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
    `client_id=${encodeURIComponent(GOOGLE_CLIENT_ID)}&` +
    `redirect_uri=${encodeURIComponent(redirectUri)}&` +
    `response_type=code&` +
    `scope=${encodeURIComponent(scope)}`;

  window.location.href = authUrl;
};
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-900">
    <div class="max-w-md w-full space-y-4 md:space-y-8 p-4 md:p-8 bg-gray-800 rounded-lg shadow-lg">
      <div>
        <h2 class="text-center text-2xl md:text-3xl font-bold text-white">
          Sign in to Diagramik
        </h2>
        <p class="mt-2 text-center text-sm text-gray-400">
          Enter your credentials to continue
        </p>
      </div>

      <!-- Session Expiration Warning -->
      <div v-if="sessionMessage" class="bg-yellow-500/10 border border-yellow-500 text-yellow-400 px-4 py-3 rounded">
        {{ sessionMessage }}
      </div>

      <!-- Login Error -->
      <div v-if="error" class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded">
        {{ error }}
      </div>

      <!-- Google Sign In Button -->
      <button
        @click="handleGoogleLogin"
        :disabled="googleLoading || !acceptedTerms"
        class="w-full flex items-center justify-center gap-3 py-2 px-4 border border-gray-600 rounded-md shadow-sm text-sm font-medium text-white bg-gray-700 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        <span v-if="googleLoading">Connecting...</span>
        <span v-else>Continue with Google</span>
      </button>

      <!-- Terms and Conditions Checkbox -->
      <div class="flex items-start space-x-2">
        <input
          id="acceptTerms"
          v-model="acceptedTerms"
          type="checkbox"
          class="mt-1 h-4 w-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-2 focus:ring-blue-500"
        />
        <label for="acceptTerms" class="text-sm text-gray-300">
          I accept the
          <a href="/terms" target="_blank" class="text-blue-400 hover:text-blue-300 underline">
            Terms and Conditions
          </a>
        </label>
      </div>

      <div class="relative">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-gray-600"></div>
        </div>
        <div class="relative flex justify-center text-sm">
          <span class="px-2 bg-gray-800 text-gray-400">Or continue with email</span>
        </div>
      </div>

      <form class="space-y-6" @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <div>
            <label for="email" class="block text-sm font-medium text-gray-300">
              Email
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
          <div>
            <label for="password" class="block text-sm font-medium text-gray-300">
              Password
            </label>
            <input
              id="password"
              v-model="password"
              name="password"
              type="password"
              autocomplete="current-password"
              required
              class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your password"
            />
          </div>
        </div>

        <div class="flex items-center justify-end">
          <a href="/auth/forgot-password" class="text-sm text-blue-400 hover:text-blue-300">
            Forgot your password?
          </a>
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full flex items-center justify-center p-3 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Sign in"
          title="Sign in"
        >
          <span v-if="loading">Signing in...</span>
          <span v-else>Sign in</span>
        </button>
      </form>

      <p class="text-center text-sm text-gray-400">
        Don't have an account?
        <a href="/auth/register" class="text-blue-400 hover:text-blue-300">
          Sign up
        </a>
      </p>
    </div>
  </div>
</template>
