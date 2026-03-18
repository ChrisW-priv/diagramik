<template>
  <div class="flex flex-col h-full min-h-0">
    <!-- Header -->
    <div class="flex items-center justify-between px-3 py-2 border-b border-gray-700 flex-shrink-0">
      <h3 class="text-sm font-medium text-gray-300 flex items-center gap-1.5">
        <TagIcon class="h-4 w-4 text-amber-400" aria-hidden="true" />
        Checkpoints
      </h3>
      <button
        @click="$emit('close')"
        class="text-gray-500 hover:text-gray-300 transition-colors p-1"
        aria-label="Close checkpoints panel"
      >
        <XMarkIcon class="h-4 w-4" />
      </button>
    </div>

    <!-- Checkpoint list -->
    <div class="flex-grow overflow-y-auto p-2 space-y-2">
      <div v-if="!checkpoints || checkpoints.length === 0" class="text-center py-6">
        <TagIcon class="h-8 w-8 text-gray-700 mx-auto mb-2" />
        <p class="text-xs text-gray-500">No checkpoints yet.</p>
        <p class="text-xs text-gray-600 mt-1">Tag a version in the chat to create one.</p>
      </div>

      <div
        v-for="cp in checkpoints"
        :key="cp.id"
        class="bg-gray-800 border border-gray-700 rounded-lg p-2.5 hover:border-gray-600 transition-colors"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0">
            <p class="text-sm font-medium text-amber-300 truncate">{{ cp.name }}</p>
            <p v-if="cp.description" class="text-xs text-gray-500 mt-0.5 line-clamp-2">{{ cp.description }}</p>
            <p class="text-xs text-gray-600 mt-1">
              {{ cp.diagram_type }} &middot; {{ formatDate(cp.created_at) }}
            </p>
          </div>
        </div>

        <div class="mt-2 flex items-center gap-1.5">
          <button
            @click="$emit('view-checkpoint', cp)"
            class="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-white bg-gray-700 hover:bg-gray-600 rounded transition-colors"
            title="View this version"
          >
            <EyeIcon class="h-3 w-3" />
            View
          </button>
          <button
            @click="handleBranch(cp)"
            class="flex items-center gap-1 px-2 py-1 text-xs text-blue-400 hover:text-blue-200 bg-blue-900/30 hover:bg-blue-900/50 rounded transition-colors"
            title="Branch from this checkpoint"
          >
            <ArrowPathRoundedSquareIcon class="h-3 w-3" />
            Branch
          </button>
          <button
            @click="$emit('delete-checkpoint', cp)"
            class="flex items-center gap-1 px-2 py-1 text-xs text-red-400 hover:text-red-200 bg-red-900/20 hover:bg-red-900/40 rounded transition-colors ml-auto"
            title="Delete checkpoint"
          >
            <TrashIcon class="h-3 w-3" />
          </button>
        </div>

        <!-- Branch input (shown when branching) -->
        <div v-if="branchingCheckpoint === cp.id" class="mt-2">
          <form @submit.prevent="submitBranch(cp)" class="flex gap-1.5">
            <input
              ref="branchInput"
              v-model="branchText"
              type="text"
              class="flex-grow px-2 py-1.5 text-xs bg-gray-900 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
              placeholder="What do you want to change?"
              :disabled="branching"
            />
            <button
              type="submit"
              :disabled="branching || !branchText.trim()"
              class="px-2 py-1.5 text-xs bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 text-white rounded transition-colors"
            >
              {{ branching ? '...' : 'Go' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { TagIcon, XMarkIcon, EyeIcon, ArrowPathRoundedSquareIcon, TrashIcon } from '@heroicons/vue/24/outline';
import { branchFromCheckpoint } from '../lib/api';

const props = defineProps({
  checkpoints: Array,
  diagramId: String,
});

const emit = defineEmits(['close', 'view-checkpoint', 'delete-checkpoint', 'branched']);

const branchingCheckpoint = ref(null);
const branchText = ref('');
const branching = ref(false);
const branchInput = ref(null);

const formatDate = (dateStr) => {
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
};

const handleBranch = (cp) => {
  if (branchingCheckpoint.value === cp.id) {
    branchingCheckpoint.value = null;
    return;
  }
  branchingCheckpoint.value = cp.id;
  branchText.value = '';
  nextTick(() => {
    if (branchInput.value) {
      const input = Array.isArray(branchInput.value) ? branchInput.value[0] : branchInput.value;
      input?.focus();
    }
  });
};

const submitBranch = async (cp) => {
  if (!branchText.value.trim() || branching.value) return;

  branching.value = true;
  try {
    await branchFromCheckpoint(props.diagramId, cp.id, branchText.value.trim());
    branchingCheckpoint.value = null;
    branchText.value = '';
    emit('branched');
  } catch (error) {
    console.error('Error branching from checkpoint:', error);
  } finally {
    branching.value = false;
  }
};
</script>
