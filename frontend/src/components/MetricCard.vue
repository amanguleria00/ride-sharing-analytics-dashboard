<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  detail: { type: String, default: '' },
  icon: { type: String, required: true },
  tone: { type: String, default: 'blue' },
})
</script>

<template>
  <article class="metric-card">
    <div class="metric-topline">
      <span class="metric-label">{{ label }}</span>
      <span class="metric-icon" :class="`tone-${tone}`" aria-hidden="true">{{ icon }}</span>
    </div>
    <div class="metric-value">{{ value }}</div>
    <div class="metric-detail">{{ detail }}</div>
  </article>
</template>
