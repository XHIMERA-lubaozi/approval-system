<script setup lang="ts">
import { computed, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    id: string
    name?: string
    autocomplete?: string
    invalid?: boolean
    describedby?: string
  }>(),
  {
    autocomplete: 'current-password',
    invalid: false,
    describedby: undefined,
  },
)

const model = defineModel<string>({ required: true })
const visible = ref(false)
const inputType = computed(() => (visible.value ? 'text' : 'password'))
const toggleLabel = computed(() =>
  visible.value ? '隐藏密码' : '显示密码',
)
</script>

<template>
  <div class="password-control">
    <input
      :id="props.id"
      v-model="model"
      :name="props.name"
      :type="inputType"
      :autocomplete="props.autocomplete"
      :aria-invalid="props.invalid"
      :aria-describedby="props.describedby"
    />
    <button
      class="password-toggle"
      type="button"
      :aria-label="toggleLabel"
      :title="toggleLabel"
      @click="visible = !visible"
    >
      <svg
        v-if="!visible"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" />
        <circle cx="12" cy="12" r="2.6" />
      </svg>
      <svg
        v-else
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M3 3l18 18" />
        <path d="M10.6 6.2A9.4 9.4 0 0 1 12 6c6 0 9.5 6 9.5 6a16.4 16.4 0 0 1-3.1 3.6" />
        <path d="M6.6 6.7C4 8.4 2.5 12 2.5 12s3.5 6 9.5 6a9.7 9.7 0 0 0 4.2-.9" />
        <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
      </svg>
    </button>
  </div>
</template>
