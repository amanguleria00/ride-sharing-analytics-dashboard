import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

function unwrap(response) {
  return response.data.data
}

export const dashboardApi = {
  summary: (filters) => api.get('/dashboard/summary', { params: filters }).then(unwrap),
  revenueTrend: (filters) => api.get('/dashboard/revenue-trend', {
    params: { ...filters, granularity: 'daily' },
  }).then(unwrap),
  ridesByStatus: (filters) => api.get('/dashboard/rides-by-status', { params: filters }).then(unwrap),
  ridesByVehicle: (filters) => api.get('/dashboard/rides-by-vehicle', { params: filters }).then(unwrap),
  topDrivers: (filters) => api.get('/dashboard/top-drivers', {
    params: { ...filters, limit: 5 },
  }).then(unwrap),
  peakHours: (filters) => api.get('/dashboard/peak-hours', { params: filters }).then(unwrap),
  rides: (filters) => api.get('/rides', { params: filters }).then(unwrap),
}

export function getApiError(error) {
  return error.response?.data?.error?.message || 'Unable to load dashboard data. Check that the API server is running.'
}
