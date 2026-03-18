<template>
  <span class="inline-flex items-center gap-1 px-1.5 py-0.5 bg-amber-900/40 border border-amber-600/30 rounded text-xs text-amber-300 whitespace-nowrap">
    <TagIcon class="h-3 w-3" aria-hidden="true" />
    {{ name }}
  </span>
</template>

<script setup>
import { TagIcon } from '@heroicons/vue/24/solid';

defineProps({
  name: { type: String, required: true },
});
</script>
