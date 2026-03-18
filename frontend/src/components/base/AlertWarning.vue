<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline';

interface Props {
  message: string;
}

defineProps<Props>();

const alertRef = ref<HTMLDivElement | null>(null);

onMounted(() => {
  alertRef.value?.focus();
});
</script>

<template>
  <div
    ref="alertRef"
    aria-live="polite"
    role="status"
    tabindex="-1"
    class="bg-yellow-500/10 border border-yellow-500 text-yellow-400 px-4 py-3 rounded-lg flex items-start gap-3 focus:outline-none"
  >
    <ExclamationTriangleIcon class="h-5 w-5 flex-shrink-0 mt-0.5" aria-hidden="true" />
    <p class="text-sm">{{ message }}</p>
  </div>
</template>
