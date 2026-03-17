<script setup lang="ts">
/**
 * FormField - Normalized form input wrapper
 * Provides consistent label, input styling, and error message display
 */

interface Props {
  id: string;
  label: string;
  modelValue: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url';
  error?: string;
  required?: boolean;
  disabled?: boolean;
  placeholder?: string;
  autocomplete?: string;
  maxlength?: number;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  required: false,
  disabled: false,
  placeholder: '',
  autocomplete: '',
});

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();

const errorId = `${props.id}-error`;
</script>

<template>
  <div class="space-y-2">
    <label :for="id" class="block text-sm font-medium text-gray-300">
      {{ label }}
      <span v-if="required" aria-hidden="true" class="text-red-400 ml-1">*</span>
    </label>

    <input
      :id="id"
      :value="modelValue"
      :type="type"
      :disabled="disabled"
      :required="required"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      :maxlength="maxlength"
      :aria-required="required"
      :aria-describedby="error ? errorId : undefined"
      class="block w-full px-3 py-2.5 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:border-transparent transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-base"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />

    <!-- Error Message -->
    <p
      v-if="error"
      :id="errorId"
      class="text-sm text-red-400 mt-1"
    >
      {{ error }}
    </p>
  </div>
</template>
