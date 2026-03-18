<template>
  <div class="bg-gray-900 border border-gray-700 rounded-lg px-4 py-3">
    <p v-if="label" class="text-xs text-gray-500 mb-1.5">{{ label }}</p>
    <p class="text-sm text-gray-300 leading-relaxed"><slot /></p>
  </div>
</template>

<script setup>
defineProps({
  label: String,
});
</script>
