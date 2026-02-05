<template>
  <div class="flex flex-col h-full">
    <p v-if="!selectedVersion">No diagram version selected. Go to the Work tab to choose one!</p>
    <div v-else class="flex flex-col h-full p-2 md:p-4 bg-gray-800 rounded-lg">
      <div class="flex-grow flex justify-center items-center overflow-auto">
        <!-- Image Display -->
        <img v-if="imageUrl" :src="imageUrl" alt="Diagram" class="max-w-full max-h-full h-auto rounded-lg">

        <!-- Error State -->
        <div v-else-if="imageError" class="flex flex-col items-center gap-3 p-6 bg-red-900/30 border border-red-500/50 rounded-lg max-w-md">
          <ExclamationCircleIcon class="h-12 w-12 text-red-400" />
          <p class="text-red-200 text-center">{{ imageError }}</p>
          <button
            @click="retryImageLoad"
            class="flex items-center gap-2 px-4 py-2 bg-red-700 hover:bg-red-600 text-white rounded-lg transition-colors"
          >
            <ArrowPathIcon class="h-5 w-5" />
            Try Again
          </button>
        </div>

        <!-- Loading State -->
        <p v-else>Loading diagram...</p>
      </div>
      <div class="flex-shrink-0 pt-4 flex justify-end">
        <button
            @click="downloadDiagram"
            class="flex items-center justify-center p-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white"
            :disabled="!imageUrl"
            aria-label="Download diagram"
            title="Download diagram"
        >
          <ArrowDownTrayIcon class="h-6 w-6" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { ExclamationCircleIcon, ArrowPathIcon, ArrowDownTrayIcon } from '@heroicons/vue/24/outline';
import { apiClient } from '../lib/api';

const props = defineProps({
  diagram: Object,
  selectedVersion: Object,
});

const imageUrl = ref('');
const imageError = ref(null);

const loadImage = async (version) => {
  imageUrl.value = '';
  imageError.value = null;

  if (version && version.id) {
    try {
      const response = await apiClient.get(`/diagrams/${version.diagram_id}/versions/${version.id}/image/?redirect=false`);
      if (response.data && response.data.image_url) {
        imageUrl.value = response.data.image_url;
      } else {
        imageError.value = 'Image URL not found. The diagram may not have been generated correctly.';
      }
    } catch (error) {
      // Comprehensive error handling
      if (error.response) {
        const status = error.response.status;

        if (status === 404) {
          imageError.value = 'Diagram image not found. It may have been deleted or not yet generated.';
        } else if (status === 403) {
          imageError.value = 'Access denied. You may not have permission to view this diagram.';
        } else if (status >= 500) {
          imageError.value = 'Server error occurred while loading the diagram. Please try again.';
        } else {
          imageError.value = 'Failed to load diagram image. Please try again.';
        }
      } else if (error.request) {
        if (!navigator.onLine) {
          imageError.value = 'No internet connection. Please check your network and try again.';
        } else {
          imageError.value = 'Network timeout. Please check your connection and try again.';
        }
      } else {
        imageError.value = 'An unexpected error occurred while loading the diagram.';
      }

      console.error('Error fetching diagram image URL:', error);
    }
  }
};

watch(() => props.selectedVersion, loadImage, { immediate: true, deep: true });

const retryImageLoad = () => {
  loadImage(props.selectedVersion);
};


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
