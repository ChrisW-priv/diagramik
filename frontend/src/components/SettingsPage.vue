<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ArrowPathIcon } from '@heroicons/vue/24/outline';
import { authApi } from '../lib/api';
import { isAuthenticated, getStoredUser } from '../lib/auth';
import FormField from './base/FormField.vue';
import AlertError from './base/AlertError.vue';
import AlertSuccess from './base/AlertSuccess.vue';

const user = ref(getStoredUser());
const firstName = ref(user.value?.first_name ?? '');
const lastName = ref(user.value?.last_name ?? '');

const saveLoading = ref(false);
const saveSuccess = ref(false);
const saveError = ref('');

const showDeleteModal = ref(false);
const deleteConfirmEmail = ref('');
const deleteLoading = ref(false);
const deleteError = ref('');

onMounted(async () => {
  if (!isAuthenticated()) {
    window.location.href = '/login';
    return;
  }
  try {
    const fresh = await authApi.getUser();
    user.value = fresh;
    firstName.value = fresh.first_name;
    lastName.value = fresh.last_name;
  } catch {
    // Use cached user data if fetch fails
  }
});

const handleSaveProfile = async () => {
  saveLoading.value = true;
  saveSuccess.value = false;
  saveError.value = '';
  try {
    await authApi.updateUser({ first_name: firstName.value, last_name: lastName.value });
    saveSuccess.value = true;
  } catch {
    saveError.value = 'Failed to save profile. Please try again.';
  } finally {
    saveLoading.value = false;
  }
};

const openDeleteModal = () => {
  deleteConfirmEmail.value = '';
  deleteError.value = '';
  showDeleteModal.value = true;
};

const closeDeleteModal = () => {
  showDeleteModal.value = false;
  deleteConfirmEmail.value = '';
  deleteError.value = '';
};

const handleDeleteAccount = async () => {
  deleteLoading.value = true;
  deleteError.value = '';
  try {
    await authApi.deleteAccount();
    window.location.href = '/login?reason=account_deleted';
  } catch (err: any) {
    if (err.response?.status === 503) {
      deleteError.value = 'Account deletion is temporarily unavailable. Please try again later.';
    } else {
      deleteError.value = 'An error occurred. Please try again.';
    }
    deleteLoading.value = false;
  }
};
</script>

<template>
  <main id="main-content" class="container mx-auto px-4 py-8 max-w-2xl">
    <div class="flex justify-between items-center mb-8">
      <h1 class="text-2xl md:text-3xl font-bold">Account Settings</h1>
      <a
        href="/diagrams"
        class="text-sm text-gray-400 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded px-1 transition-colors"
      >
        ← Back to diagrams
      </a>
    </div>

    <!-- Profile Section -->
    <section class="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
      <h2 class="text-lg font-semibold mb-4">Profile</h2>
      <form @submit.prevent="handleSaveProfile" class="space-y-4">
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-300">Email</label>
          <p class="px-3 py-2.5 bg-gray-700/50 border border-gray-600 rounded-md text-gray-400 text-base">
            {{ user?.email }}
          </p>
        </div>

        <FormField
          id="first_name"
          label="First name"
          v-model="firstName"
          autocomplete="given-name"
          placeholder="Enter your first name"
        />

        <FormField
          id="last_name"
          label="Last name"
          v-model="lastName"
          autocomplete="family-name"
          placeholder="Enter your last name"
        />

        <AlertSuccess v-if="saveSuccess" message="Profile saved successfully." />
        <AlertError v-if="saveError" :message="saveError" dismissible @dismiss="saveError = ''" />

        <button
          type="submit"
          :disabled="saveLoading"
          :aria-busy="saveLoading"
          class="flex items-center justify-center gap-2 py-2.5 px-6 bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 focus-visible:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none rounded-lg text-sm font-medium transition-colors"
        >
          <ArrowPathIcon v-if="saveLoading" class="h-4 w-4 animate-spin" aria-hidden="true" />
          <span>{{ saveLoading ? 'Saving...' : 'Save changes' }}</span>
        </button>
      </form>
    </section>

    <!-- Danger Zone -->
    <section class="bg-gray-800 border border-red-900 rounded-lg p-6">
      <h2 class="text-lg font-semibold text-red-400 mb-2">Danger Zone</h2>
      <p class="text-sm text-gray-400 mb-4">
        Permanently delete your account. This action cannot be undone.
      </p>
      <button
        @click="openDeleteModal"
        class="py-2.5 px-6 border border-red-700 text-red-400 hover:bg-red-900/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 rounded-lg text-sm font-medium transition-colors"
      >
        Delete account
      </button>
    </section>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-modal-title"
    >
      <div class="bg-gray-800 border border-gray-700 rounded-lg p-6 max-w-md w-full">
        <h3 id="delete-modal-title" class="text-lg font-bold text-red-400 mb-2">
          Delete your account?
        </h3>
        <p class="text-sm text-gray-400 mb-4">
          This will permanently delete your account. To confirm, type your email address below.
        </p>

        <div class="space-y-2 mb-4">
          <label for="confirm-email" class="block text-sm font-medium text-gray-300">
            Your email address
          </label>
          <input
            id="confirm-email"
            v-model="deleteConfirmEmail"
            type="email"
            :placeholder="user?.email"
            autocomplete="off"
            class="block w-full px-3 py-2.5 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:border-transparent transition-colors text-base"
          />
        </div>

        <AlertError v-if="deleteError" :message="deleteError" class="mb-4" />

        <div class="flex gap-3">
          <button
            @click="closeDeleteModal"
            :disabled="deleteLoading"
            class="flex-1 py-2.5 px-4 bg-gray-700 hover:bg-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            @click="handleDeleteAccount"
            :disabled="deleteConfirmEmail !== user?.email || deleteLoading"
            :aria-busy="deleteLoading"
            class="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 bg-red-700 hover:bg-red-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none rounded-lg text-sm font-medium transition-colors"
          >
            <ArrowPathIcon v-if="deleteLoading" class="h-4 w-4 animate-spin" aria-hidden="true" />
            <span>{{ deleteLoading ? 'Deleting...' : 'Delete my account' }}</span>
          </button>
        </div>
      </div>
    </div>
  </main>
</template>
