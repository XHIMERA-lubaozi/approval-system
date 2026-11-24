<script setup lang="ts">
import markUrl from '../assets/approval-system-mark.png'

withDefaults(defineProps<{ compact?: boolean }>(), {
  compact: false,
})
</script>

<template>
  <span class="brand-lockup" :class="{ 'is-compact': compact }">
    <img class="brand-mark" :src="markUrl" alt="" aria-hidden="true" />
    <span class="brand-wordmark">Approval system</span>
  </span>
</template>

<style scoped>
.brand-lockup {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #101828;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1;
  white-space: nowrap;
}

.brand-mark {
  display: block;
  width: 36px;
  height: auto;
  flex: none;
}

.brand-wordmark {
  font-size: 1.32rem;
}

.brand-lockup.is-compact {
  gap: 8px;
}

.brand-lockup.is-compact .brand-mark {
  width: 26px;
}

.brand-lockup.is-compact .brand-wordmark {
  font-size: 0.95rem;
  letter-spacing: -0.01em;
}
</style>
