<template>
  <nav class="bottom-nav">
    <button
      v-for="item in items"
      :key="item.id"
      class="nav-btn"
      :class="{ active: active === item.id }"
      @click="$emit('change', item.id)"
      :title="item.label"
    >
      <span class="nav-icon" v-html="item.icon"></span>
    </button>
  </nav>
</template>

<script setup>
defineProps({ active: { type: String, default: 'home' } })
defineEmits(['change'])

const items = [
  {
    id: 'home', label: 'Home',
    icon: `<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
      <path d="M3 12L12 3l9 9"/><path d="M9 21V12h6v9"/>
    </svg>`,
  },
  {
    id: 'search', label: 'Search',
    icon: `<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>`,
  },
  {
    id: 'saved', label: 'Saved',
    icon: `<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
    </svg>`,
  },
  {
    id: 'map', label: 'Map',
    icon: `<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
      <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>
      <line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/>
    </svg>`,
  },
]
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: rgba(22, 18, 12, 0.95);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255,255,255,0.07);
  padding: 0.8rem 1rem calc(0.8rem + env(safe-area-inset-bottom));
  z-index: 100;
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border: none;
  background: transparent;
  border-radius: 14px;
  color: rgba(255,255,255,0.35);
  cursor: pointer;
  transition: color 0.2s, background 0.2s;
}

.nav-btn.active {
  color: #fff;
  background: rgba(255,255,255,0.1);
}

.nav-btn:hover:not(.active) {
  color: rgba(255,255,255,0.65);
}

.nav-icon { display: flex; align-items: center; justify-content: center; }
</style>
