<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ArrowPathIcon } from '@heroicons/vue/24/outline';
import { authApi } from '../lib/api';
import { CONFIG } from '../lib/config';
import FormContainer from './base/FormContainer.vue';
import FormField from './base/FormField.vue';
import AlertError from './base/AlertError.vue';
import AlertSuccess from './base/AlertSuccess.vue';

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
  if (newPassword.value.length < CONFIG.VALIDATION.PASSWORD_MIN_LENGTH) {
    error.value = `Password must be at least ${CONFIG.VALIDATION.PASSWORD_MIN_LENGTH} characters long.`;
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
  <FormContainer
    title="Set New Password"
    :subtitle="isTokenMethod ? 'Enter your new password below' : 'Enter your current password and new password'"
  >
    <!-- Error Alert -->
    <AlertError v-if="error" :message="error" dismissible @dismiss="error = ''" />

    <!-- Success Alert -->
    <AlertSuccess
      v-if="success"
      message="Password changed successfully! You are now logged in. Redirecting to your diagrams..."
    />

    <form v-if="!success" class="space-y-4" @submit.prevent="handleSubmit">
      <!-- Old Password Method Fields -->
      <template v-if="!isTokenMethod">
        <FormField
          id="email"
          v-model="email"
          label="Email Address"
          type="email"
          required
          autocomplete="email"
          placeholder="your@email.com"
          :error="error && error.includes('email') ? error : undefined"
        />

        <FormField
          id="oldPassword"
          v-model="oldPassword"
          label="Current Password"
          type="password"
          required
          autocomplete="current-password"
          placeholder="Enter your current password"
          :error="error && error.includes('Invalid') ? error : undefined"
        />
      </template>

      <!-- Password Fields (both methods) -->
      <FormField
        id="newPassword"
        v-model="newPassword"
        label="New Password"
        type="password"
        required
        autocomplete="new-password"
        placeholder="Enter your new password"
        :error="error && error.includes('Password') && error.includes('least') ? error : undefined"
      />

      <FormField
        id="confirmPassword"
        v-model="confirmPassword"
        label="Confirm New Password"
        type="password"
        required
        autocomplete="new-password"
        placeholder="Confirm your new password"
        :error="error && error.includes('do not match') ? error : undefined"
      />

      <button
        type="submit"
        :disabled="!canSubmit"
        :aria-busy="loading"
        class="w-full flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 focus-visible:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none transition-colors font-medium"
      >
        <ArrowPathIcon v-if="loading" class="h-5 w-5 animate-spin mr-2" aria-hidden="true" />
        <span v-if="loading">Updating...</span>
        <span v-else>Update Password</span>
      </button>
    </form>
  </FormContainer>
</template>
