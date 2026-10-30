<template>
  <header class="status-bar">
    <div class="logo">
      <span class="ghost">👻</span>
      <span class="name">GhostWatch</span>
    </div>

    <div class="pills" v-if="status">
      <span class="pill">
        <span class="dot" :class="status.ollama_available ? 'green' : 'red'"></span>
        Ollama {{ status.ollama_available ? 'ready' : 'offline' }}
      </span>
      <span class="pill">
        <span class="dot" :class="{ yellow: status.sample_mode, green: !status.sample_mode }"></span>
        {{ status.sample_mode ? 'Sample mode' : status.platform }}
      </span>
      <span class="pill">
        <span class="dot green"></span>
        {{ status.ollama_model }}
      </span>
    </div>

    <div class="pills" v-else>
      <span class="pill"><span class="dot"></span>Connecting…</span>
    </div>
  </header>
</template>

<script setup>
defineProps({ status: Object })
</script>

<style scoped>
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 24px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ghost { font-size: 20px; }
.name {
  font-weight: 700;
  font-size: 16px;
  letter-spacing: -0.02em;
  color: var(--text);
}
.pills { display: flex; gap: 8px; flex-wrap: wrap; }
</style>
