<template>
  <div class="err-banner" role="alert">
    <span class="err-icon">⚠️</span>
    <span class="err-msg">{{ message }}</span>
    <button @click="$emit('dismiss')">✕</button>
  </div>
</template>

<script setup>
defineProps({ message: { type: String, required: true } })
defineEmits(['dismiss'])
</script>

<style scoped>
.err-banner {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  background: rgba(200,50,50,0.2);
  border: 1px solid rgba(255,90,90,0.3);
  border-radius: 14px;
  padding: 0.9rem 1rem;
  margin-bottom: 1rem;
  color: #fff;
  font-size: 0.88rem;
  animation: shake 0.3s ease;
}

.err-icon { font-size: 1.1rem; flex-shrink: 0; }
.err-msg  { flex: 1; line-height: 1.4; }

button {
  background: none; border: none;
  color: rgba(255,255,255,0.5);
  cursor: pointer; font-size: 0.9rem;
  padding: 0.2rem 0.4rem;
  border-radius: 6px;
  flex-shrink: 0;
}
button:hover { background: rgba(255,255,255,0.08); }

@keyframes shake {
  0%,100% { transform: translateX(0); }
  25%      { transform: translateX(-5px); }
  75%      { transform: translateX(5px); }
}
</style>
