<script setup>
defineProps({
  rides: { type: Array, required: true },
  loading: { type: Boolean, default: false },
  page: { type: Number, required: true },
  totalPages: { type: Number, required: true },
  total: { type: Number, required: true },
})

defineEmits(['change-page'])

function formatDate(value) {
  return new Date(value).toLocaleString(undefined, {
    month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit',
  })
}

function formatMoney(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value)
}
</script>

<template>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Ride</th>
          <th>Requested</th>
          <th>Driver</th>
          <th>Vehicle</th>
          <th>Fare</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody v-if="!loading && rides.length">
        <tr v-for="ride in rides" :key="ride.ride_id">
          <td>
            <span class="ride-number">#{{ String(ride.ride_id).padStart(4, '0') }}</span>
            <span class="route-label">{{ ride.pickup_location }} → {{ ride.dropoff_location }}</span>
          </td>
          <td class="muted-cell">{{ formatDate(ride.request_time) }}</td>
          <td>{{ ride.driver_name }}</td>
          <td><span class="vehicle-label">{{ ride.vehicle_type }}</span></td>
          <td class="fare-cell">{{ formatMoney(ride.fare) }}</td>
          <td><span class="status-pill" :class="`status-${ride.status}`">{{ ride.status }}</span></td>
        </tr>
      </tbody>
    </table>
    <div v-if="loading" class="table-state">Loading ride records…</div>
    <div v-else-if="!rides.length" class="table-state">No rides match this date range.</div>
    <div v-if="!loading && total" class="table-pagination">
      <span>Showing {{ rides.length }} of {{ total }} rides</span>
      <div class="pagination-actions">
        <button class="page-button" :disabled="page <= 1" @click="$emit('change-page', page - 1)">Previous</button>
        <span>Page {{ page }} of {{ totalPages }}</span>
        <button class="page-button" :disabled="page >= totalPages" @click="$emit('change-page', page + 1)">Next</button>
      </div>
    </div>
  </div>
</template>
