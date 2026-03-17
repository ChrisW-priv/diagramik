<script setup lang="ts">
import { CheckCircleIcon } from '@heroicons/vue/24/outline';

interface Props {
  message: string;
}

defineProps<Props>();
</script>

<template>
  <div
    aria-live="polite"
    role="status"
    class="bg-green-500/10 border border-green-500 text-green-400 px-4 py-3 rounded-lg flex items-start gap-3"
  >
    <CheckCircleIcon class="h-5 w-5 flex-shrink-0 mt-0.5" aria-hidden="true" />
    <p class="text-sm">{{ message }}</p>
  </div>
</template>
