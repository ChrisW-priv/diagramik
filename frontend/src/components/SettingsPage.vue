<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ArrowPathIcon, Bars3Icon } from '@heroicons/vue/24/outline';
import { authApi } from '../lib/api';
import { isAuthenticated, getStoredUser } from '../lib/auth';
import DiagramsSidebar from './DiagramsSidebar.vue';
import FormField from './base/FormField.vue';
import AlertError from './base/AlertError.vue';
import AlertSuccess from './base/AlertSuccess.vue';

// ─── Layout ───────────────────────────────────────────────────────────────────
const mobileSidebarOpen = ref(false);

// ─── User data ────────────────────────────────────────────────────────────────
// Initialize to null so SSR and initial client hydration match.
// Populated in onMounted to avoid localStorage-driven hydration mismatches.
const user = ref<ReturnType<typeof getStoredUser>>(null);
const firstName = ref('');
const lastName = ref('');

// ─── Profile save ─────────────────────────────────────────────────────────────
const saveLoading = ref(false);
const saveSuccess = ref(false);
const saveError = ref('');

// ─── Delete account ───────────────────────────────────────────────────────────
const showDeleteModal = ref(false);
const deleteConfirmEmail = ref('');
const deleteLoading = ref(false);
const deleteError = ref('');

// ─── Section nav ──────────────────────────────────────────────────────────────
const sections = [
  { id: 'profile', label: 'Profile' },
  { id: 'appearance', label: 'Appearance' },
  { id: 'security', label: 'Security' },
  { id: 'danger-zone', label: 'Danger Zone' },
] as const;

type SectionId = typeof sections[number]['id'];

onMounted(async () => {
  if (!isAuthenticated()) {
    window.location.href = '/login';
    return;
  }
  // Load cached user first so the UI is immediately populated
  const cached = getStoredUser();
  if (cached) {
    user.value = cached;
    firstName.value = cached.first_name ?? '';
    lastName.value = cached.last_name ?? '';
  }
  try {
    const fresh = await authApi.getUser();
    user.value = fresh;
    firstName.value = fresh.first_name;
    lastName.value = fresh.last_name;
  } catch {
    // Use cached user data if fetch fails
  }

  // Scroll to hash section on load (hash set by a prior click, not auto-updated)
  const hash = window.location.hash.slice(1) as SectionId;
  if (hash && sections.some(s => s.id === hash)) {
    setTimeout(() => {
      document.getElementById(hash)?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }
});

// ─── Nav click ────────────────────────────────────────────────────────────────
const scrollToSection = (id: SectionId) => {
  history.pushState(null, '', `#${id}`);
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
};

// ─── Profile handlers ─────────────────────────────────────────────────────────
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

// ─── Navigation helpers ───────────────────────────────────────────────────────
const navigateToDiagram = (id: string) => {
  window.location.href = '/diagrams?id=' + id;
};
const navigateToNewDiagram = () => {
  window.location.href = '/diagrams';
};

// ─── Delete handlers ──────────────────────────────────────────────────────────
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
  <div class="flex flex-col md:flex-row h-screen overflow-hidden bg-gray-900">

    <!-- MOBILE-ONLY top bar: hamburger + brand name -->
    <header class="flex md:hidden h-14 items-center px-4 bg-gray-800 border-b border-gray-700 flex-shrink-0 gap-3">
      <button
        @click="mobileSidebarOpen = true"
        aria-label="Open sidebar"
        class="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
      >
        <Bars3Icon class="h-5 w-5" aria-hidden="true" />
      </button>
      <span class="text-sm font-semibold text-white tracking-tight">Diagramik</span>
    </header>

    <!-- Mobile backdrop -->
    <div
      v-if="mobileSidebarOpen"
      class="fixed inset-0 z-40 bg-black/50 md:hidden"
      aria-hidden="true"
      @click="mobileSidebarOpen = false"
    />

    <!-- Sidebar -->
    <DiagramsSidebar
      :active-diagram-id="null"
      :mobile-open="mobileSidebarOpen"
      @select-diagram="navigateToDiagram"
      @new-diagram="navigateToNewDiagram"
      @add-to-workspace="navigateToNewDiagram"
      @diagram-deleted="() => {}"
    />

    <!-- Main content -->
    <main id="main-content" class="flex-1 overflow-y-auto">

      <!-- Mobile section tabs -->
      <div class="flex md:hidden overflow-x-auto border-b border-gray-700 bg-gray-900 sticky top-0 z-10" style="scrollbar-width: none;">
        <a
          v-for="s in sections"
          :key="s.id"
          :href="`#${s.id}`"
          @click.prevent="scrollToSection(s.id)"
          class="flex-shrink-0 px-5 py-3 text-sm font-medium text-gray-400 hover:text-gray-200 transition-colors"
        >{{ s.label }}</a>
      </div>

      <!-- Centered 2-column panel -->
      <div class="max-w-3xl mx-auto px-6 md:px-8 py-10 flex gap-12 items-start">

        <!-- Settings nav (desktop only) -->
        <nav
          class="hidden md:flex flex-col gap-0.5 w-36 flex-shrink-0 sticky top-10 self-start pt-1"
          aria-label="Settings sections"
        >
          <p class="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3 px-2">Settings</p>
          <a
            v-for="s in sections"
            :key="s.id"
            :href="`#${s.id}`"
            @click.prevent="scrollToSection(s.id)"
            class="px-2 py-1.5 rounded text-sm text-gray-500 hover:text-gray-300 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
          >{{ s.label }}</a>
        </nav>

        <!-- Settings content -->
        <div class="flex-1 min-w-0 space-y-16 pb-16">

          <!-- ── Profile ─────────────────────────────────────────────────── -->
          <section id="profile">
            <h2 class="text-base font-semibold text-white mb-6">Profile</h2>

            <!-- Avatar -->
            <div class="flex items-center gap-4 mb-6">
              <img
                v-if="user?.pk"
                :src="`https://api.dicebear.com/9.x/identicon/svg?seed=${user.pk}`"
                :alt="`${user?.first_name ?? 'User'}'s avatar`"
                class="w-14 h-14 rounded-full bg-gray-700 ring-1 ring-gray-600 flex-shrink-0"
              />
              <div v-else class="w-14 h-14 rounded-full bg-gray-700 ring-1 ring-gray-600 flex-shrink-0" />
              <div>
                <p class="text-sm font-medium text-white leading-snug">
                  {{ [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email }}
                </p>
                <p class="text-xs text-gray-500 mt-0.5">Avatar is generated from your account</p>
              </div>
            </div>

            <form @submit.prevent="handleSaveProfile" class="space-y-4">
              <div class="space-y-1.5">
                <label class="block text-sm font-medium text-gray-300">Email</label>
                <p class="px-3 py-2.5 bg-gray-700/40 border border-gray-700 rounded-md text-gray-400 text-sm">
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
                class="flex items-center justify-center gap-2 py-2 px-5 bg-blue-600 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 focus-visible:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none rounded-lg text-sm font-medium transition-colors"
              >
                <ArrowPathIcon v-if="saveLoading" class="h-4 w-4 animate-spin" aria-hidden="true" />
                <span>{{ saveLoading ? 'Saving…' : 'Save changes' }}</span>
              </button>
            </form>
          </section>

          <!-- ── Appearance ─────────────────────────────────────────────── -->
          <section id="appearance">
            <h2 class="text-base font-semibold text-white mb-6">Appearance</h2>

            <div class="space-y-4">
              <!-- Theme row -->
              <div class="flex items-center justify-between py-3 border-b border-gray-800">
                <div>
                  <p class="text-sm font-medium text-gray-200">Theme</p>
                  <p class="text-xs text-gray-500 mt-0.5">Interface color scheme</p>
                </div>
                <span class="text-xs font-medium text-gray-400 bg-gray-800 border border-gray-700 px-2.5 py-1 rounded-md">
                  Dark
                </span>
              </div>

              <p class="text-xs text-gray-600 pt-1">Additional display preferences coming soon.</p>
            </div>
          </section>

          <!-- ── Security ───────────────────────────────────────────────── -->
          <section id="security">
            <h2 class="text-base font-semibold text-white mb-6">Security</h2>

            <div class="space-y-4">
              <div class="space-y-1.5">
                <label class="block text-sm font-medium text-gray-300">Current password</label>
                <input
                  type="password"
                  disabled
                  placeholder="••••••••"
                  class="block w-full px-3 py-2.5 bg-gray-700/40 border border-gray-700 rounded-md text-gray-500 placeholder-gray-600 text-sm cursor-not-allowed"
                />
              </div>
              <div class="space-y-1.5">
                <label class="block text-sm font-medium text-gray-300">New password</label>
                <input
                  type="password"
                  disabled
                  placeholder="••••••••"
                  class="block w-full px-3 py-2.5 bg-gray-700/40 border border-gray-700 rounded-md text-gray-500 placeholder-gray-600 text-sm cursor-not-allowed"
                />
              </div>
              <div class="space-y-1.5">
                <label class="block text-sm font-medium text-gray-300">Confirm new password</label>
                <input
                  type="password"
                  disabled
                  placeholder="••••••••"
                  class="block w-full px-3 py-2.5 bg-gray-700/40 border border-gray-700 rounded-md text-gray-500 placeholder-gray-600 text-sm cursor-not-allowed"
                />
              </div>
              <p class="text-xs text-gray-600 pt-1">Password changes are not yet available.</p>
            </div>
          </section>

          <!-- ── Danger Zone ─────────────────────────────────────────────── -->
          <section id="danger-zone">
            <h2 class="text-base font-semibold text-red-400 mb-2">Danger Zone</h2>
            <p class="text-sm text-gray-500 mb-5">
              Permanently delete your account. This action cannot be undone.
            </p>
            <button
              @click="openDeleteModal"
              class="py-2 px-5 border border-red-800 text-red-400 hover:bg-red-900/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 rounded-lg text-sm font-medium transition-colors"
            >
              Delete account
            </button>
          </section>

        </div>
      </div>
    </main>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-modal-title"
    >
      <div class="bg-gray-800 border border-gray-700 rounded-lg p-6 max-w-md w-full">
        <h3 id="delete-modal-title" class="text-base font-bold text-red-400 mb-2">
          Delete your account?
        </h3>
        <p class="text-sm text-gray-400 mb-4">
          This will permanently delete your account. To confirm, type your email address below.
        </p>

        <div class="space-y-1.5 mb-4">
          <label for="confirm-email" class="block text-sm font-medium text-gray-300">
            Your email address
          </label>
          <input
            id="confirm-email"
            v-model="deleteConfirmEmail"
            type="email"
            :placeholder="user?.email"
            autocomplete="off"
            class="block w-full px-3 py-2.5 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:border-transparent transition-colors text-sm"
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
            <span>{{ deleteLoading ? 'Deleting…' : 'Delete my account' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
