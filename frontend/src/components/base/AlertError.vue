<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ExclamationCircleIcon } from '@heroicons/vue/24/outline';

interface Props {
  message: string;
  /** Optional: Show a close button */
  dismissible?: boolean;
  /** Optional: Auto-focus when mounted for accessibility */
  autofocus?: boolean;
}

withDefaults(defineProps<Props>(), {
  dismissible: false,
  autofocus: false,
});

const emit = defineEmits<{
  dismiss: [];
}>();

const alertRef = ref<HTMLDivElement | null>(null);

onMounted(() => {
  // Focus the alert so screen readers announce it and keyboard users have context
  alertRef.value?.focus();
});
</script>

<template>
  <div
    ref="alertRef"
    aria-live="assertive"
    role="alert"
    tabindex="-1"
    class="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded-lg flex items-start gap-3 focus:outline-none"
  >
    <ExclamationCircleIcon class="h-5 w-5 flex-shrink-0 mt-0.5" aria-hidden="true" />
    <div class="flex-grow">
      <p class="text-sm">{{ message }}</p>
      <button
        v-if="dismissible"
        @click="emit('dismiss')"
        class="text-red-300 hover:text-red-100 text-sm underline mt-1"
        aria-label="Dismiss error"
      >
        Dismiss
      </button>
    </div>
  </div>
</template>
