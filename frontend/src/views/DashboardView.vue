<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import AnalyticsChart from '../components/AnalyticsChart.vue'
import MetricCard from '../components/MetricCard.vue'
import RideTable from '../components/RideTable.vue'
import { dashboardApi, getApiError } from '../services/api.js'

const filters = reactive({
  start_date: '',
  end_date: '',
})
const summary = ref(null)
const revenue = ref([])
const statuses = ref([])
const vehicles = ref([])
const drivers = ref([])
const hours = ref([])
const ridePage = ref({ items: [], page: 1, per_page: 10, total: 0, total_pages: 0 })
const loading = ref(true)
const errorMessage = ref('')
const ridesLoading = ref(false)
const page = ref(1)

const money = (value) => new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', maximumFractionDigits: 0,
}).format(value || 0)
const percent = (value) => `${Number(value || 0).toFixed(1)}%`

const revenueChart = computed(() => ({
  labels: revenue.value.map((item) => {
    const date = new Date(`${item.period}T00:00:00`)
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  }),
  datasets: [{
    label: 'Revenue',
    data: revenue.value.map((item) => item.revenue),
    borderColor: '#5268e8',
    backgroundColor: 'rgba(82, 104, 232, 0.12)',
    fill: true,
    tension: 0.36,
    pointRadius: 2,
    pointHoverRadius: 5,
  }],
}))
const statusChart = computed(() => ({
  labels: statuses.value.map((item) => item.status),
  datasets: [{
    data: statuses.value.map((item) => item.rides),
    backgroundColor: statuses.value.map((item) => ({
      requested: '#5268e8',
      ongoing: '#f2ad4b',
      completed: '#34b78c',
      cancelled: '#ed7180',
    })[item.status] || '#a0a8b6'),
    borderWidth: 0,
    hoverOffset: 7,
  }],
}))
const vehicleChart = computed(() => ({
  labels: vehicles.value.map((item) => item.vehicle_type),
  datasets: [{
    label: 'Rides',
    data: vehicles.value.map((item) => item.rides),
    backgroundColor: ['#5268e8', '#8a78e8', '#36b79a', '#f1ae50'],
    borderRadius: 7,
    maxBarThickness: 40,
  }],
}))
const driverChart = computed(() => ({
  labels: drivers.value.map((driver) => driver.name),
  datasets: [{
    label: 'Completed rides',
    data: drivers.value.map((driver) => driver.completed_rides),
    backgroundColor: '#6578eb',
    borderRadius: 6,
    maxBarThickness: 24,
  }],
}))
const peakHoursChart = computed(() => {
  const counts = new Map(hours.value.map((item) => [item.hour, item.rides]))
  return {
    labels: Array.from({ length: 24 }, (_, hour) => `${String(hour).padStart(2, '0')}:00`),
    datasets: [{
      label: 'Ride requests',
      data: Array.from({ length: 24 }, (_, hour) => counts.get(hour) || 0),
      backgroundColor: '#48b99b',
      borderRadius: 4,
      maxBarThickness: 22,
    }],
  }
})

function sharedFilters() {
  const params = {}
  if (filters.start_date) params.start_date = filters.start_date
  if (filters.end_date) params.end_date = filters.end_date
  return params
}

async function fetchDashboard() {
  loading.value = true
  errorMessage.value = ''
  page.value = 1
  try {
    const params = sharedFilters()
    const [summaryData, revenueData, statusData, vehicleData, driverData, hoursData] = await Promise.all([
      dashboardApi.summary(params),
      dashboardApi.revenueTrend(params),
      dashboardApi.ridesByStatus(params),
      dashboardApi.ridesByVehicle(params),
      dashboardApi.topDrivers(params),
      dashboardApi.peakHours(params),
    ])
    summary.value = summaryData
    revenue.value = revenueData
    statuses.value = statusData
    vehicles.value = vehicleData
    drivers.value = driverData
    hours.value = hoursData
  } catch (error) {
    errorMessage.value = getApiError(error)
    summary.value = null
    revenue.value = []
    statuses.value = []
    vehicles.value = []
    drivers.value = []
    hours.value = []
  } finally {
    loading.value = false
  }
}

async function fetchRides() {
  ridesLoading.value = true
  try {
    ridePage.value = await dashboardApi.rides({ ...sharedFilters(), page: page.value, per_page: 10 })
  } catch (error) {
    errorMessage.value = getApiError(error)
    ridePage.value = { items: [], page: 1, per_page: 10, total: 0, total_pages: 0 }
  } finally {
    ridesLoading.value = false
  }
}

function applyDateRange() {
  if (filters.start_date && filters.end_date && filters.start_date > filters.end_date) {
    errorMessage.value = 'The start date must be on or before the end date.'
    return
  }
  fetchDashboard()
  fetchRides()
}

function changePage(nextPage) {
  page.value = nextPage
  fetchRides()
}

watch(() => [filters.start_date, filters.end_date], () => {
  if (filters.start_date && filters.end_date && filters.start_date > filters.end_date) {
    errorMessage.value = 'The start date must be on or before the end date.'
    return
  }
  applyDateRange()
})

onMounted(() => {
  fetchDashboard()
  fetchRides()
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <a class="brand" href="#" aria-label="Ridewise home">
        <span class="brand-mark">R</span>
        <span>ridewise<span class="brand-period">.</span></span>
      </a>
      <div class="nav-caption">WORKSPACE</div>
      <nav>
        <a class="nav-item active" href="#overview"><span class="nav-icon">▦</span> Overview</a>
        <a class="nav-item" href="#rides"><span class="nav-icon">↗</span> Ride activity</a>
        <a class="nav-item" href="#drivers"><span class="nav-icon">♙</span> Drivers</a>
      </nav>
      <div class="sidebar-bottom">
        <div class="live-indicator"><span></span> Analytics active</div>
        <div class="sidebar-note">Operations dashboard<br />Live data from your database</div>
      </div>
    </aside>

    <main id="overview" class="main-content">
      <header class="topbar">
        <div class="breadcrumb">Workspace <span>/</span> Analytics</div>
        <div class="topbar-right"><span class="status-dot"></span><span>Connected to local data</span></div>
      </header>

      <section class="page-heading">
        <div>
          <div class="eyebrow">OPERATIONS OVERVIEW</div>
          <h1>Good day, here's your overview</h1>
          <p class="page-subtitle">Track ride activity and performance across your fleet.</p>
        </div>
        <div class="date-filters">
          <label>
            <span>From</span>
            <input v-model="filters.start_date" type="date" aria-label="Start date" />
          </label>
          <span class="date-divider">—</span>
          <label>
            <span>To</span>
            <input v-model="filters.end_date" type="date" aria-label="End date" />
          </label>
          <button class="filter-button" aria-label="Refresh dashboard" @click="applyDateRange">↻</button>
        </div>
      </section>

      <div v-if="errorMessage" class="error-banner" role="alert">
        <span>{{ errorMessage }}</span><button @click="applyDateRange">Retry</button>
      </div>

      <section class="metrics-grid" aria-label="Key performance indicators">
        <MetricCard label="Total rides" :value="summary ? summary.total_rides.toLocaleString() : '—'" detail="In selected period" icon="↗" />
        <MetricCard label="Completed rides" :value="summary ? summary.completed_rides.toLocaleString() : '—'" detail="Successfully completed" icon="✓" tone="green" />
        <MetricCard label="Total revenue" :value="summary ? money(summary.total_revenue) : '—'" detail="Successful completed rides" icon="₹" tone="purple" />
        <MetricCard label="Average fare" :value="summary ? money(summary.average_fare) : '—'" detail="Per completed ride" icon="⌁" tone="orange" />
        <MetricCard label="Cancellation rate" :value="summary ? percent(summary.cancellation_rate) : '—'" detail="Cancelled rides / total rides" icon="⊘" tone="red" />
      </section>

      <section class="charts-grid">
        <article class="panel revenue-panel">
          <div class="panel-heading">
            <div><h2>Revenue over time</h2><p>Successful payments from completed rides</p></div>
            <span class="panel-tag">DAILY</span>
          </div>
          <div v-if="loading" class="chart-state">Loading revenue data…</div>
          <div v-else-if="!revenue.length" class="chart-state">No revenue in this date range.</div>
          <AnalyticsChart v-else type="line" :data="revenueChart" currency />
        </article>
        <article class="panel status-panel">
          <div class="panel-heading"><div><h2>Ride status</h2><p>Requests by current status</p></div></div>
          <div v-if="loading" class="chart-state">Loading ride statuses…</div>
          <div v-else-if="!statuses.length" class="chart-state">No ride records found.</div>
          <AnalyticsChart v-else type="doughnut" :data="statusChart" />
        </article>
        <article class="panel">
          <div class="panel-heading"><div><h2>Rides by vehicle</h2><p>Fleet utilization by vehicle type</p></div></div>
          <div v-if="loading" class="chart-state">Loading vehicle data…</div>
          <div v-else-if="!vehicles.length" class="chart-state">No ride records found.</div>
          <AnalyticsChart v-else type="bar" :data="vehicleChart" />
        </article>
        <article id="drivers" class="panel">
          <div class="panel-heading"><div><h2>Top drivers</h2><p>Ranked by completed rides</p></div><span class="panel-tag">TOP 5</span></div>
          <div v-if="loading" class="chart-state">Loading driver data…</div>
          <div v-else-if="!drivers.length || drivers.every((driver) => !driver.completed_rides)" class="chart-state">No completed rides found.</div>
          <AnalyticsChart v-else type="bar" :data="driverChart" horizontal />
        </article>
        <article class="panel peak-panel">
          <div class="panel-heading"><div><h2>Peak request hours</h2><p>Ride requests by hour of day</p></div><span class="panel-tag">24 HOURS</span></div>
          <div v-if="loading" class="chart-state">Loading peak-hour data…</div>
          <div v-else-if="!hours.length" class="chart-state">No ride requests found.</div>
          <AnalyticsChart v-else type="bar" :data="peakHoursChart" />
        </article>
      </section>

      <section id="rides" class="panel rides-panel">
        <div class="panel-heading rides-heading">
          <div><h2>Recent rides</h2><p>Ride-level activity in the selected period</p></div>
          <span v-if="ridePage.total" class="results-count">{{ ridePage.total }} records</span>
        </div>
        <RideTable :rides="ridePage.items" :loading="ridesLoading" :page="ridePage.page"
          :total-pages="ridePage.total_pages" :total="ridePage.total" @change-page="changePage" />
      </section>
      <footer class="page-footer">Ridewise Analytics <span>·</span> Metrics update from your selected date range</footer>
    </main>
  </div>
</template>
