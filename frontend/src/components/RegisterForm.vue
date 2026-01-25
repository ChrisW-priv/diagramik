<script setup lang="ts">
import { ref } from 'vue';
import { authApi } from '../lib/api';

const email = ref('');
const password1 = ref('');
const password2 = ref('');
const firstName = ref('');
const error = ref('');
const success = ref('');
const loading = ref(false);
const googleLoading = ref(false);

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
    await authApi.register(email.value, password1.value, password2.value, firstName.value);
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
  googleLoading.value = true;
  error.value = '';

  try {
    const authUrl = await authApi.getGoogleAuthUrl();
    window.location.href = authUrl;
  } catch (err: any) {
    error.value = 'Could not connect to Google. Please try again.';
    googleLoading.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-900">
    <div class="max-w-md w-full space-y-8 p-8 bg-gray-800 rounded-lg shadow-lg">
      <div>
        <h2 class="text-center text-3xl font-bold text-white">
          Create your account
        </h2>
        <p class="mt-2 text-center text-sm text-gray-400">
          Get started with Diagramik
        </p>
      </div>

      <div v-if="error" class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded">
        {{ error }}
      </div>

      <div v-if="success" class="bg-green-500/10 border border-green-500 text-green-400 px-4 py-3 rounded">
        {{ success }}
        <a href="/login" class="block mt-2 text-blue-400 hover:text-blue-300">
          Go to login
        </a>
      </div>

      <template v-if="!success">
        <!-- Google Sign Up Button -->
        <button
          @click="handleGoogleLogin"
          :disabled="googleLoading"
          class="w-full flex items-center justify-center gap-3 py-2 px-4 border border-gray-600 rounded-md shadow-sm text-sm font-medium text-white bg-gray-700 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          <span v-if="googleLoading">Connecting...</span>
          <span v-else>Sign up with Google</span>
        </button>

        <div class="relative">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-600"></div>
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="px-2 bg-gray-800 text-gray-400">Or sign up with email</span>
          </div>
        </div>

        <form class="space-y-6" @submit.prevent="handleSubmit">
          <div class="space-y-4">
            <div>
              <label for="firstName" class="block text-sm font-medium text-gray-300">
                How should we address you?
              </label>
              <input
                id="firstName"
                v-model="firstName"
                name="firstName"
                type="text"
                autocomplete="given-name"
                class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Your name (optional)"
              />
            </div>
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
              <label for="password1" class="block text-sm font-medium text-gray-300">
                Password
              </label>
              <input
                id="password1"
                v-model="password1"
                name="password1"
                type="password"
                autocomplete="new-password"
                required
                class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Create a password"
              />
            </div>
            <div>
              <label for="password2" class="block text-sm font-medium text-gray-300">
                Confirm Password
              </label>
              <input
                id="password2"
                v-model="password2"
                name="password2"
                type="password"
                autocomplete="new-password"
                required
                class="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Confirm your password"
              />
            </div>
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="loading">Creating account...</span>
            <span v-else>Create account</span>
          </button>
        </form>

        <p class="text-center text-sm text-gray-400">
          Already have an account?
          <a href="/login" class="text-blue-400 hover:text-blue-300">
            Sign in
          </a>
        </p>
      </template>
    </div>
  </div>
</template>
