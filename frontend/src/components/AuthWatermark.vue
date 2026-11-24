<script setup lang="ts">
import watermarkUrl from '../assets/one-software-watermark.png'
</script>

<template>
  <img
    class="auth-watermark auth-watermark--top-left"
    :src="watermarkUrl"
    alt=""
    aria-hidden="true"
  />
  <img
    class="auth-watermark auth-watermark--top-right"
    :src="watermarkUrl"
    alt=""
    aria-hidden="true"
  />
  <img
    class="auth-watermark auth-watermark--bottom-left"
    :src="watermarkUrl"
    alt=""
    aria-hidden="true"
  />
  <img
    class="auth-watermark auth-watermark--side"
    :src="watermarkUrl"
    alt=""
    aria-hidden="true"
  />
</template>
