<script setup lang="ts">
import { computed } from 'vue'

import type { RequestStatus } from '../api/requests'

const props = defineProps<{ status: RequestStatus }>()

const labels: Record<RequestStatus, string> = {
  draft: '草稿',
  in_review: '审批中',
  approved: '已通过',
  rejected: '已驳回',
}

const label = computed(() => labels[props.status])
</script>

<template>
  <span class="status-badge" :class="`is-${status}`">{{ label }}</span>
</template>
