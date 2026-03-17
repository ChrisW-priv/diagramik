<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { UserPlusIcon, ArrowPathIcon } from '@heroicons/vue/24/outline';
import { authApi } from '../lib/api';
import { CONFIG } from '../lib/config';
import FormContainer from './base/FormContainer.vue';
import FormField from './base/FormField.vue';
import AlertError from './base/AlertError.vue';
import AlertSuccess from './base/AlertSuccess.vue';
import axios from 'axios';

const email = ref('');
const password1 = ref('');
const password2 = ref('');
const firstName = ref('');
const error = ref('');
const success = ref('');
const loading = ref(false);
const googleLoading = ref(false);

// OAuth pending state
const termsAccepted = ref(false);
const oauthPending = ref(false);
const oauthProvider = ref('');
const oauthStateToken = ref('');
const oauthUserData = ref<any>(null);

// Check if error is the unverified account message
const isUnverifiedAccountError = computed(() => {
  return error.value.includes('An unverified account with this email exists');
});

onMounted(async () => {
  // Check for OAuth pending flow
  const urlParams = new URLSearchParams(window.location.search);
  const pending = urlParams.get('oauth_pending');
  const state = urlParams.get('state');

  if (pending === 'google' && state) {
    oauthPending.value = true;
    oauthProvider.value = 'google';
    oauthStateToken.value = state;

    // Decode state to prefill user data
    try {
      const response = await axios.post(
        `${CONFIG.API.BASE_URL}/api/v1/auth/social/google/decode-state/`,
        { state_token: state }
      );
      oauthUserData.value = response.data;

      // Prefill form fields
      email.value = response.data.email;
      firstName.value = response.data.first_name;
    } catch (err) {
      error.value = 'Invalid or expired registration link. Please try again.';
    }
  }
});

const handleSubmit = async () => {
  error.value = '';
  success.value = '';
  loading.value = true;

  if (password1.value !== password2.value) {
    error.value = 'Passwords do not match';
    loading.value = false;
    return;
  }

  try {
    const response = await authApi.register(email.value, password1.value, password2.value, firstName.value);

    // Check if email verification is mandatory (no tokens in response)
    if (response.detail && response.detail.includes('Verification email sent')) {
      // Redirect to verification-pending page with email pre-filled
      window.location.href = `/auth/verification-pending?email=${encodeURIComponent(email.value)}`;
      return;
    }

    // If tokens are present, user is auto-logged in (optional verification mode)
    if (response.access && response.refresh) {
      window.location.href = '/diagrams';
      return;
    }

    success.value = 'Account created! Please check your email to verify your account.';
  } catch (err: any) {
    if (err.response?.data) {
      const data = err.response.data;
      if (data.email) {
        error.value = data.email[0];
      } else if (data.password1) {
        error.value = data.password1[0];
      } else if (data.non_field_errors) {
        error.value = data.non_field_errors[0];
      } else {
        error.value = 'Registration failed. Please try again.';
      }
    } else {
      error.value = 'An error occurred. Please try again.';
    }
  } finally {
    loading.value = false;
  }
};

const handleGoogleLogin = async () => {
  // Only allow if email is entered
  if (!email.value) {
    return;
  }

  googleLoading.value = true;
  error.value = '';

  try {
    const authUrl = await authApi.getGoogleAuthUrl(false, false);
    window.location.href = authUrl;
  } catch (err: any) {
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail;
    } else {
      error.value = 'Failed to initiate Google login. Please try again.';
    }
    googleLoading.value = false;
  }
};

const handleOAuthComplete = async () => {
  if (!oauthPending.value) {
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    const response = await authApi.completeOAuthRegistration(
      oauthStateToken.value,
      true
    );

    // Tokens are set by authApi, redirect to diagrams
    window.location.href = '/diagrams';
  } catch (err: any) {
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail;
    } else {
      error.value = 'Failed to complete registration. Please try again.';
    }
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <FormContainer title="Create your account" subtitle="Get started with Diagramik">
    <!-- Error Alert -->
    <AlertError v-if="error && !success" :message="error" dismissible @dismiss="error = ''" />

    <!-- Success Alert -->
    <AlertSuccess v-if="success" :message="success" />

    <template v-if="!success">
      <!-- OAuth Pending Welcome -->
      <div v-if="oauthPending" class="bg-blue-500/10 border border-blue-500 text-blue-400 px-4 py-3 rounded-lg mb-4">
        <h3 class="font-semibold mb-2">Welcome to Diagramik!</h3>
        <p class="text-sm">
          Since this is your first time signing in with Google, please review and accept our
          <a href="/terms" target="_blank" class="underline hover:text-blue-300">Terms and Conditions</a>
          to complete your registration.
        </p>
      </div>

      <!-- Google Sign Up (not OAuth pending) -->
      <button
        v-if="!oauthPending"
        @click="handleGoogleLogin"
        :disabled="googleLoading || !email"
        :aria-busy="googleLoading"
        class="w-full flex items-center justify-center gap-3 py-2.5 px-4 border border-gray-600 rounded-lg shadow-sm text-sm font-medium text-white bg-gray-700 hover:bg-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 focus-visible:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none transition-colors"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" aria-label="Google logo">
          <title>Google</title>
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        <span v-if="googleLoading">Connecting...</span>
        <span v-else>Sign up with Google</span>
      </button>

      <!-- Divider (not OAuth pending) -->
      <div v-if="!oauthPending" class="relative">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-gray-600"></div>
        </div>
        <div class="relative flex justify-center text-sm">
          <span class="px-2 bg-gray-800 text-gray-400">Or sign up with email</span>
        </div>
      </div>

      <!-- Email/Password Form (not OAuth pending) -->
      <form v-if="!oauthPending" class="space-y-4" @submit.prevent="handleSubmit">
        <FormField
          id="firstName"
          v-model="firstName"
          label="How should we address you?"
          type="text"
          autocomplete="given-name"
          placeholder="Your name (optional)"
          :maxlength="CONFIG.VALIDATION.NAME_MAX_LENGTH"
        />

        <FormField
          id="email"
          v-model="email"
          label="Email"
          type="email"
          required
          autocomplete="email"
          placeholder="Enter your email"
          :error="error && !isUnverifiedAccountError ? error : undefined"
        />

        <FormField
          id="password1"
          v-model="password1"
          label="Password"
          type="password"
          required
          autocomplete="new-password"
          placeholder="Create a password"
          :error="error && error.includes('password') ? error : undefined"
        />

        <FormField
          id="password2"
          v-model="password2"
          label="Confirm Password"
          type="password"
          required
          autocomplete="new-password"
          placeholder="Confirm your password"
          :error="error && error.includes('do not match') ? error : undefined"
        />

        <!-- Terms Checkbox -->
        <div class="flex items-start space-x-3 pt-2">
          <input
            id="acceptTerms"
            v-model="termsAccepted"
            type="checkbox"
            class="mt-1 h-4 w-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus-visible:ring-2 focus-visible:ring-blue-500 cursor-pointer"
            required
          />
          <label for="acceptTerms" class="text-sm text-gray-300 cursor-pointer">
            I accept the
            <a href="/terms" target="_blank" class="text-blue-400 hover:text-blue-300 underline">
              Terms and Conditions
            </a>
            <span aria-hidden="true" class="text-red-400 ml-1">*</span>
          </label>
        </div>

        <button
          type="submit"
          :disabled="loading || !termsAccepted"
          :aria-busy="loading"
          class="w-full flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 focus-visible:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none transition-colors font-medium"
        >
          <ArrowPathIcon v-if="loading" class="h-5 w-5 animate-spin mr-2" aria-hidden="true" />
          <span v-if="loading">Creating account...</span>
          <span v-else>Create account</span>
        </button>
      </form>

      <!-- OAuth Pending Form -->
      <div v-if="oauthPending" class="space-y-4">
        <div class="bg-gray-700/50 p-4 rounded-lg">
          <p class="text-sm text-gray-300 mb-2"><strong>Email:</strong> {{ email }}</p>
          <p class="text-sm text-gray-300"><strong>Name:</strong> {{ firstName || '(not provided)' }}</p>
        </div>

        <!-- Terms Checkbox (OAuth) -->
        <div class="flex items-start space-x-3">
          <input
            id="acceptTermsOAuth"
            v-model="termsAccepted"
            type="checkbox"
            class="mt-1 h-4 w-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus-visible:ring-2 focus-visible:ring-blue-500 cursor-pointer"
            required
          />
          <label for="acceptTermsOAuth" class="text-sm text-gray-300 cursor-pointer">
            I accept the
            <a href="/terms" target="_blank" class="text-blue-400 hover:text-blue-300 underline">
              Terms and Conditions
            </a>
            <span aria-hidden="true" class="text-red-400 ml-1">*</span>
          </label>
        </div>

        <button
          @click="handleOAuthComplete"
          :disabled="loading || !termsAccepted"
          :aria-busy="loading"
          class="w-full flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 focus-visible:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none transition-colors font-medium"
        >
          <ArrowPathIcon v-if="loading" class="h-5 w-5 animate-spin mr-2" aria-hidden="true" />
          <span v-else>Complete Registration</span>
        </button>
      </div>

      <!-- Sign In Link -->
      <p v-if="!oauthPending" class="text-center text-sm text-gray-400">
        Already have an account?
        <a href="/login" class="text-blue-400 hover:text-blue-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded px-1">
          Sign in
        </a>
      </p>
    </template>
  </FormContainer>
</template>
