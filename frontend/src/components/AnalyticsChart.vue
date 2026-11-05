<script setup>
import { computed } from 'vue'
import { Bar, Doughnut, Line } from 'vue-chartjs'

const props = defineProps({
  type: { type: String, required: true },
  data: { type: Object, required: true },
  horizontal: { type: Boolean, default: false },
  currency: { type: Boolean, default: false },
})

const chartComponent = computed(() => ({
  line: Line,
  bar: Bar,
  doughnut: Doughnut,
})[props.type])

const options = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: props.horizontal ? 'y' : 'x',
  plugins: {
    legend: {
      display: props.type === 'doughnut',
      position: 'bottom',
      labels: { usePointStyle: true, padding: 18, color: '#68748a', font: { size: 11 } },
    },
    tooltip: {
      callbacks: props.currency ? {
        label: (context) => ` ${context.dataset.label || ''}: ₹${Number(context.raw).toLocaleString('en-IN')}`,
      } : {},
    },
  },
  scales: props.type === 'doughnut' ? {} : {
    x: {
      beginAtZero: true,
      grid: { display: false },
      ticks: { color: '#8993a5', maxRotation: props.type === 'line' ? 0 : 0 },
      border: { display: false },
    },
    y: {
      beginAtZero: true,
      grid: { color: '#edf0f5' },
      ticks: props.currency ? {
        color: '#8993a5',
        callback: (value) => `₹${Number(value).toLocaleString('en-IN')}`,
      } : { color: '#8993a5', precision: 0 },
      border: { display: false },
    },
  },
}))
</script>

<template>
  <div class="chart-canvas">
    <component :is="chartComponent" :data="data" :options="options" />
  </div>
</template>
