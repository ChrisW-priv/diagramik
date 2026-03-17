<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ArrowPathIcon } from '@heroicons/vue/24/outline';
import { authApi } from '../lib/api';
import FormContainer from './base/FormContainer.vue';
import FormField from './base/FormField.vue';
import AlertError from './base/AlertError.vue';
import AlertSuccess from './base/AlertSuccess.vue';

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
  <FormContainer title="Set new password" subtitle="Enter your new password below">
    <!-- Invalid Link -->
    <div v-if="invalidLink" class="space-y-4">
      <AlertError message="This password reset link is invalid. Please request a new one." />
      <a
        href="/auth/forgot-password"
        class="w-full inline-flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 focus-visible:ring-blue-400 transition-colors font-medium"
      >
        <ArrowPathIcon class="h-5 w-5 mr-2" aria-hidden="true" />
        Request new link
      </a>
    </div>

    <!-- Error Alert -->
    <AlertError v-if="error && !invalidLink" :message="error" dismissible @dismiss="error = ''" />

    <!-- Success Alert -->
    <div v-if="success" class="space-y-4">
      <AlertSuccess message="Your password has been reset successfully!" />
      <a
        href="/login"
        class="w-full inline-flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 focus-visible:ring-blue-400 transition-colors font-medium"
      >
        Go to sign in
      </a>
    </div>

    <!-- Form -->
    <form v-if="!invalidLink && !success" class="space-y-4" @submit.prevent="handleSubmit">
      <FormField
        id="password1"
        v-model="password1"
        label="New Password"
        type="password"
        required
        autocomplete="new-password"
        placeholder="Enter your new password"
        :error="error && error.includes('password') ? error : undefined"
      />

      <FormField
        id="password2"
        v-model="password2"
        label="Confirm New Password"
        type="password"
        required
        autocomplete="new-password"
        placeholder="Confirm your new password"
        :error="error && error.includes('do not match') ? error : undefined"
      />

      <button
        type="submit"
        :disabled="loading"
        :aria-busy="loading"
        class="w-full flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 focus-visible:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none transition-colors font-medium"
      >
        <ArrowPathIcon v-if="loading" class="h-5 w-5 animate-spin mr-2" aria-hidden="true" />
        <span v-if="loading">Updating...</span>
        <span v-else>Set Password</span>
      </button>
    </form>
  </FormContainer>
</template>
