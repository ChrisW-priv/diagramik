<template>
  <div class="flex flex-col h-full">
    <p v-if="!selectedVersion">No diagram version selected. Go to the Work tab to choose one!</p>
    <div v-else class="flex flex-col h-full p-4 bg-gray-800 rounded-lg">
      <div class="flex-grow flex justify-center items-center overflow-auto">
        <img v-if="imageUrl" :src="imageUrl" alt="Diagram" class="max-w-full max-h-full h-auto rounded-lg">
        <p v-else>Loading diagram...</p>
      </div>
      <div class="flex-shrink-0 pt-4 flex justify-end">
        <button
            @click="downloadDiagram"
            class="p-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white"
            :disabled="!imageUrl"
            title="Download Diagram"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { apiClient } from '../lib/api';

const props = defineProps({
  diagram: Object,
  selectedVersion: Object,
});

const imageUrl = ref('');

watch(() => props.selectedVersion, async (newVersion) => {
  imageUrl.value = ''; // Clear previous image
  if (newVersion && newVersion.id) {
    try {
      // Show loading state while we fetch the new URL
      const response = await apiClient.get(`/diagrams/${newVersion.diagram_id}/versions/${newVersion.id}/image/?redirect=false`);
      if (response.data && response.data.image_url) {
        imageUrl.value = response.data.image_url;
      } else {
        console.error('Image URL not found in response.');
      }
    } catch (error) {
      console.error('Error fetching diagram image URL:', error);
    }
  }
}, { immediate: true, deep: true });


const downloadDiagram = () => {
  if (imageUrl.value) {
    const link = document.createElement('a');
    link.href = imageUrl.value;
    link.download = `diagram-version-${props.selectedVersion.id}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};
</script>
