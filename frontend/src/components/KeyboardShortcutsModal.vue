<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      @keydown.escape="$emit('close')"
    >
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60" @click="$emit('close')"></div>

      <!-- Dialog -->
      <div
        ref="dialogRef"
        role="dialog"
        aria-modal="true"
        aria-label="Keyboard shortcuts"
        tabindex="-1"
        class="relative bg-gray-800 border border-gray-700 rounded-lg shadow-xl w-full max-w-lg max-h-[80vh] overflow-y-auto"
      >
        <div class="flex items-center justify-between p-5 border-b border-gray-700">
          <h2 class="text-lg font-semibold text-white">Keyboard Shortcuts</h2>
          <button
            @click="$emit('close')"
            class="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 transition-colors"
            aria-label="Close"
          >
            <XMarkIcon class="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <div class="p-5 space-y-6">
          <!-- Editor -->
          <section>
            <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">Editor</h3>
            <div class="space-y-2">
              <ShortcutRow label="Submit message"><kbd>Enter</kbd></ShortcutRow>
              <ShortcutRow label="New line"><kbd>Shift</kbd> + <kbd>Enter</kbd></ShortcutRow>
            </div>
          </section>

          <!-- Layout -->
          <section>
            <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">Layout</h3>
            <div class="space-y-2">
              <ShortcutRow label="Toggle panels"><kbd>{{ altKey }}</kbd> + <kbd>Tab</kbd></ShortcutRow>
              <ShortcutRow label="Resize panels"><kbd>Arrow Left</kbd> / <kbd>Arrow Right</kbd></ShortcutRow>
              <ShortcutRow label="Larger resize step"><kbd>Shift</kbd> + <kbd>Arrow</kbd></ShortcutRow>
            </div>
          </section>

          <!-- General -->
          <section>
            <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">General</h3>
            <div class="space-y-2">
              <ShortcutRow label="Show shortcuts"><kbd>?</kbd></ShortcutRow>
              <ShortcutRow label="Close dialog"><kbd>Esc</kbd></ShortcutRow>
            </div>
          </section>
        </div>

        <div class="px-5 py-4 border-t border-gray-700 text-sm text-gray-400">
          <a href="/guide#keyboard-shortcuts" class="text-blue-400 hover:text-blue-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded px-1">
            View full guide
          </a>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue';
import { XMarkIcon } from '@heroicons/vue/24/outline';
import ShortcutRow from './base/ShortcutRow.vue';

const props = defineProps({
  open: Boolean,
});

defineEmits(['close']);

const dialogRef = ref(null);

const isMac = computed(() => {
  if (typeof navigator === 'undefined') return false;
  return /Mac|iPhone|iPad|iPod/.test(navigator.platform || navigator.userAgent);
});

const altKey = computed(() => isMac.value ? 'Option' : 'Alt');

watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    await nextTick();
    dialogRef.value?.focus();
  }
});
</script>
