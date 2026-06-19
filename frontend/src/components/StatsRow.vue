<template>
  <div class="stats-row">
    <div class="stat">
      <span class="s-icon">💨</span>
      <div class="s-info">
        <span class="s-val">{{ round(day.windspeed_max_kmh) }}<small>km/h</small></span>
        <span class="s-label">Wind</span>
      </div>
    </div>

    <div class="sep"></div>

    <div class="stat">
      <span class="s-icon">🌧️</span>
      <div class="s-info">
        <span class="s-val">{{ precipVal }}<small>%</small></span>
        <span class="s-label">Rain Chance</span>
      </div>
    </div>

    <div class="sep"></div>

    <div class="stat">
      <span class="s-icon">💦</span>
      <div class="s-info">
        <span class="s-val">{{ humidityVal }}<small v-if="day.humidity_pct">%</small><small v-else>hPa</small></span>
        <span class="s-label">{{ day.humidity_pct != null ? 'Humidity' : 'Pressure' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { round } from '../utils.js'

const props = defineProps({
  day: { type: Object, required: true },
})

const precipVal = computed(() => {
  const v = props.day.precipitation_probability_pct ?? props.day.precipitation_mm
  return v !== null && v !== undefined ? round(v) : '—'
})

const humidityVal = computed(() => {
  if (props.day.humidity_pct !== null && props.day.humidity_pct !== undefined)
    return props.day.humidity_pct
  if (props.day.pressure_hpa !== null && props.day.pressure_hpa !== undefined)
    return props.day.pressure_hpa
  return '—'
})
</script>

<style scoped>
.stats-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.6rem;
  padding: 0.7rem 0 1rem;
  border-top: 1px solid rgba(255,255,255,0.07);
  border-bottom: 1px solid rgba(255,255,255,0.07);
  margin: 0 0 1rem;
}

@media (max-width: 360px) {
  .stats-row { gap: 0.9rem; }
}

.stat {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.s-icon { font-size: 1.1rem; }

.s-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.05rem;
}

.s-val {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255,255,255,0.85);
  display: flex;
  align-items: baseline;
  gap: 0.12rem;
  line-height: 1.2;
}

.s-val small {
  font-size: 0.68rem;
  font-weight: 400;
  color: rgba(255,255,255,0.4);
}

.s-label {
  font-size: 0.65rem;
  font-weight: 500;
  color: rgba(255,255,255,0.3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sep {
  width: 1px;
  height: 20px;
  background: rgba(255,255,255,0.15);
}
</style>
