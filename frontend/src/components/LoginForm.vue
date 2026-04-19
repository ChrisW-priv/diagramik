<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ArrowPathIcon } from '@heroicons/vue/24/outline';
import { authApi } from '../lib/api';
import { CONFIG } from '../lib/config';
import FormContainer from './base/FormContainer.vue';
import FormField from './base/FormField.vue';
import AlertError from './base/AlertError.vue';
import AlertWarning from './base/AlertWarning.vue';
import GoogleLogo from './base/GoogleLogo.vue';

const email = ref('');
const password = ref('');
const error = ref('');
const sessionMessage = ref('');
const loading = ref(false);
const googleLoading = ref(false);

// Check for session expiration or other reasons
onMounted(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const reason = urlParams.get('reason');

  if (reason === 'session_expired') {
    sessionMessage.value = 'Your session has expired. Please sign in again.';
  } else if (reason === 'account_deleted') {
    sessionMessage.value = 'Your account has been successfully deleted.';
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

  const redirectUri = `${CONFIG.API.BASE_URL}/api/v1/auth/social/google/`;
  const scope = 'openid email profile';
  const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
    `client_id=${encodeURIComponent(CONFIG.OAUTH.GOOGLE_CLIENT_ID)}&` +
    `redirect_uri=${encodeURIComponent(redirectUri)}&` +
    `response_type=code&` +
    `scope=${encodeURIComponent(scope)}`;

  window.location.href = authUrl;
};
</script>

<template>
  <FormContainer title="Sign in to Diagramik" subtitle="Sign in to start diagramming.">
    <!-- Session Warning -->
    <AlertWarning v-if="sessionMessage" :message="sessionMessage" />

    <!-- Login Error -->
    <AlertError v-if="error" :message="error" dismissible @dismiss="error = ''" />

    <!-- Google Sign In -->
    <button
      @click="handleGoogleLogin"
      :disabled="googleLoading"
      :aria-busy="googleLoading"
      class="w-full flex items-center justify-center gap-3 py-2.5 px-4 border border-gray-600 rounded-lg shadow-sm text-sm font-medium text-white bg-gray-700 hover:bg-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 focus-visible:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none transition-colors"
    >
      <GoogleLogo />
      <span v-if="googleLoading">Connecting...</span>
      <span v-else>Continue with Google</span>
    </button>

    <!-- Divider -->
    <div class="relative" role="separator">
      <hr class="border-gray-600" />
      <span class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 px-2 bg-gray-800 text-gray-400 text-sm">Or continue with email</span>
    </div>

    <!-- Email/Password Form -->
    <form class="space-y-4" @submit.prevent="handleSubmit">
      <FormField
        id="email"
        v-model="email"
        label="Email"
        type="email"
        required
        autocomplete="email"
        placeholder="Enter your email"
      />

      <FormField
        id="password"
        v-model="password"
        label="Password"
        type="password"
        required
        autocomplete="current-password"
        placeholder="Enter your password"
      />

      <div class="flex items-center justify-end">
        <a href="/auth/forgot-password" class="text-sm text-blue-400 hover:text-blue-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded px-1">
          Forgot your password?
        </a>
      </div>

      <button
        type="submit"
        :disabled="loading"
        :aria-busy="loading"
        class="w-full flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 focus-visible:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none transition-colors font-medium"
      >
        <ArrowPathIcon v-if="loading" class="h-5 w-5 animate-spin mr-2" aria-hidden="true" />
        <span v-if="loading">Signing in...</span>
        <span v-else>Sign in</span>
      </button>
    </form>

    <!-- Sign Up Link -->
    <p class="text-center text-sm text-gray-400">
      Don't have an account?
      <a href="/auth/register" class="text-blue-400 hover:text-blue-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded px-1">
        Sign up
      </a>
    </p>
  </FormContainer>
</template>
