<script setup lang="ts">
import watermarkUrl from '../assets/one-software-watermark.png'
</script>

<template>
  <div class="app-watermark-layer" aria-hidden="true">
    <img
      class="app-watermark app-watermark--top-right"
      :src="watermarkUrl"
      alt=""
    />
    <img
      class="app-watermark app-watermark--center-right"
      :src="watermarkUrl"
      alt=""
    />
    <img
      class="app-watermark app-watermark--bottom-right"
      :src="watermarkUrl"
      alt=""
    />
  </div>
</template>
