<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="close">
    <div class="bg-gray-800 border border-gray-700 rounded-lg shadow-xl w-full max-w-sm mx-4 p-5">
      <h3 class="text-lg font-medium text-white mb-4">Tag as Checkpoint</h3>

      <div v-if="error" class="mb-3 p-2 bg-red-900/50 border border-red-500 rounded text-sm text-red-200">
        {{ error }}
      </div>

      <form @submit.prevent="handleCreate">
        <div class="mb-3">
          <label for="checkpoint-name" class="block text-sm text-gray-400 mb-1">Name</label>
          <input
            id="checkpoint-name"
            ref="nameInput"
            v-model="name"
            type="text"
            maxlength="100"
            class="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-400"
            placeholder="e.g. v1, baseline, before-refactor"
            :disabled="creating"
          />
        </div>

        <div class="mb-4">
          <label for="checkpoint-desc" class="block text-sm text-gray-400 mb-1">Description <span class="text-gray-600">(optional)</span></label>
          <input
            id="checkpoint-desc"
            v-model="description"
            type="text"
            class="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-400"
            placeholder="Brief description..."
            :disabled="creating"
          />
        </div>

        <div class="flex gap-2 justify-end">
          <button
            type="button"
            @click="close"
            class="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            :disabled="creating"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="creating || !name.trim()"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {{ creating ? 'Creating...' : 'Create Tag' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { createCheckpoint } from '../lib/api';

const props = defineProps({
  show: Boolean,
  diagramId: String,
  versionId: String,
});

const emit = defineEmits(['close', 'created']);

const name = ref('');
const description = ref('');
const creating = ref(false);
const error = ref(null);
const nameInput = ref(null);

watch(() => props.show, (isVisible) => {
  if (isVisible) {
    name.value = '';
    description.value = '';
    error.value = null;
    nextTick(() => nameInput.value?.focus());
  }
});

const close = () => {
  if (!creating.value) emit('close');
};

const handleCreate = async () => {
  if (!name.value.trim() || creating.value) return;

  creating.value = true;
  error.value = null;

  try {
    const response = await createCheckpoint(
      props.diagramId,
      props.versionId,
      name.value.trim(),
      description.value.trim()
    );
    emit('created', response.data);
    emit('close');
  } catch (err) {
    if (err.response?.data?.error) {
      error.value = err.response.data.error;
    } else {
      error.value = 'Failed to create checkpoint. Please try again.';
    }
  } finally {
    creating.value = false;
  }
};
</script>
