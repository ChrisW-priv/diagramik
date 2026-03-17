<script setup lang="ts">
/**
 * StandardFormContainer - Normalized form wrapper component
 * Ensures consistent styling across all auth forms
 * Provides proper spacing, max-width, and dark theme styling
 */

interface Props {
  title: string;
  subtitle?: string;
}

withDefaults(defineProps<Props>(), {
  subtitle: '',
});
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-900 px-4">
    <div class="max-w-md w-full space-y-6 p-6 md:p-8 bg-gray-800 border border-gray-700 rounded-lg shadow-lg">
      <!-- Header -->
      <div>
        <h1 class="text-center text-2xl md:text-3xl font-bold text-white">
          {{ title }}
        </h1>
        <p v-if="subtitle" class="mt-2 text-center text-sm text-gray-400">
          {{ subtitle }}
        </p>
      </div>

      <!-- Form Content Slot -->
      <slot />
    </div>
  </div>
</template>
