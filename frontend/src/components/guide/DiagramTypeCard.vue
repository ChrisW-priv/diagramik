<template>
  <div class="bg-gray-800 rounded-lg p-6">
    <h3 class="text-xl font-semibold text-white mb-2">{{ title }}</h3>
    <p class="text-gray-400 text-sm mb-4">{{ description }}</p>
    <div class="flex flex-wrap gap-2 mb-5">
      <span
        v-for="tag in tags"
        :key="tag"
        class="bg-gray-700 rounded px-2 py-1 text-xs text-gray-300"
      >{{ tag }}</span>
    </div>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  title: String,
  description: String,
  tags: Array,
});
</script>
