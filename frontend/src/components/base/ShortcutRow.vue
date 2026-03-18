<template>
  <div class="flex items-center justify-between py-1.5">
    <span class="text-sm text-gray-300">{{ label }}</span>
    <span class="flex items-center gap-1 text-xs text-gray-400">
      <slot />
    </span>
  </div>
</template>

<script setup>
defineProps({
  label: String,
});
</script>

<style scoped>
:deep(kbd) {
  display: inline-block;
  padding: 2px 6px;
  font-size: 0.75rem;
  font-family: inherit;
  line-height: 1.25rem;
  color: #d1d5db;
  background-color: #374151;
  border: 1px solid #4b5563;
  border-radius: 0.375rem;
  min-width: 1.5rem;
  text-align: center;
}
</style>
