<template>
  <div class="hero">
    <!-- Location -->
    <div class="location">
      <span class="city">{{ loc.city }}</span>
      <span class="country" v-if="loc.country">, {{ loc.country }}</span>
    </div>
    <div class="date-line">{{ fullDate }}</div>

    <!-- Weather icon with glow -->
    <div class="icon-wrap">
      <div class="icon-glow" :style="{ background: glowColor }"></div>
      <span class="icon">{{ emoji }}</span>
    </div>

    <!-- Temperature -->
    <div class="temp-row">
      <span class="temp">{{ round(day.temp_mean) }}</span>
      <span class="unit">°C</span>
    </div>

    <!-- Description -->
    <p class="desc">{{ friendlyDesc }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { weatherEmoji, iconGlow, humanDescription, splitLocation, formatFullDate, round } from '../utils.js'

const props = defineProps({
  day:      { type: Object, required: true },
  location: { type: String, required: true },
})

const loc       = computed(() => splitLocation(props.location))
const emoji     = computed(() => weatherEmoji(props.day.weather_description))
const glowColor = computed(() => `radial-gradient(circle, ${iconGlow(props.day.weather_description)} 0%, transparent 70%)`)
const fullDate  = computed(() => formatFullDate(props.day.date))
const friendlyDesc = computed(() => humanDescription(props.day.weather_description))
</script>

<style scoped>
.hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.2rem 0 0.6rem;
  color: #fff;
}

.location {
  font-size: 1.1rem;
  margin-bottom: 0.1rem;
  letter-spacing: 0.3px;
}
.city    { font-weight: 700; }
.country { font-weight: 400; color: rgba(255,255,255,0.7); }

.date-line {
  font-size: 0.75rem;
  color: rgba(255,255,255,0.4);
  margin-bottom: 0.9rem;
  font-weight: 400;
}

.icon-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.6rem;
}

.icon-glow {
  position: absolute;
  width: 130px;
  height: 130px;
  border-radius: 50%;
  filter: blur(24px);
  pointer-events: none;
}

.icon {
  font-size: 5.5rem;
  line-height: 1;
  position: relative;
  z-index: 1;
  filter: drop-shadow(0 6px 18px rgba(0,0,0,0.5));
  animation: float 4s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50%       { transform: translateY(-8px); }
}

.temp-row {
  display: flex;
  align-items: flex-start;
  gap: 0.15rem;
  margin-bottom: 0.3rem;
}

.temp {
  font-size: 4.5rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -2px;
}

.unit {
  font-size: 1.5rem;
  font-weight: 300;
  padding-top: 0.45rem;
  color: rgba(255,255,255,0.8);
}

.desc {
  font-size: 0.88rem;
  color: rgba(255,255,255,0.6);
  font-weight: 400;
  text-align: center;
}
</style>
