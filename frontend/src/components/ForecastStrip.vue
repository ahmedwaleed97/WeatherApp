<template>
  <div class="forecast-section">
    <div class="section-header">
      <span class="hdr-icon">📅</span>
      <span class="hdr-title">What's Coming</span>
    </div>

    <div class="cards-scroll">
      <div
        class="fc-card"
        v-for="day in days"
        :key="day.date"
        :class="{ active: day.date === todayStr }"
      >
        <div class="fc-emoji">{{ weatherEmoji(day.weather_description) }}</div>
        <div class="fc-day">{{ formatDay(day.date) }}</div>
        <div class="fc-temp">{{ round(day.temp_max) }}<span class="deg">°</span></div>
        <div class="fc-low">{{ round(day.temp_min) }}°</div>
        <div class="fc-rain" v-if="day.precipitation_probability_pct != null">
          💧{{ day.precipitation_probability_pct }}%
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { weatherEmoji, formatDay, round } from '../utils.js'

defineProps({ days: { type: Array, required: true } })

const todayStr = new Date().toISOString().slice(0, 10)
</script>

<style scoped>
.forecast-section { padding: 0 0 1rem; }

.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  color: rgba(255,255,255,0.55);
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.cards-scroll {
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
  scrollbar-width: none;
}
.cards-scroll::-webkit-scrollbar { display: none; }

.fc-card {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 0.7rem 0.9rem;
  min-width: 74px;
  transition: background 0.2s;
  cursor: default;
}

.fc-card.active {
  background: rgba(255,255,255,0.13);
  border-color: rgba(255,255,255,0.18);
}

.fc-card:hover { background: rgba(255,255,255,0.1); }

.fc-emoji { font-size: 1.5rem; line-height: 1; }

.fc-day {
  font-size: 0.72rem;
  color: rgba(255,255,255,0.5);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.fc-temp {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
}

.deg { font-weight: 300; font-size: 0.9rem; }

.fc-low {
  font-size: 0.78rem;
  color: rgba(255,255,255,0.35);
}

.fc-rain {
  font-size: 0.65rem;
  color: #7ec8e3;
  margin-top: 0.1rem;
}
</style>
