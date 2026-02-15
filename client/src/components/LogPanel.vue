<template>
  <div class="log-panel">
    <div class="log-header">
      <span>实时日志</span>
      <el-tag size="small" type="info">{{ logs.length }} 条</el-tag>
    </div>
    <div ref="logContainer" class="log-container">
      <div v-if="!logs.length" class="log-empty">等待日志输出...</div>
      <div v-for="(log, i) in logs" :key="i" class="log-line">
        <span class="log-time">{{ log.time }}</span>
        <span class="log-msg">{{ log.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  logs: { type: Array, default: () => [] },
})

const logContainer = ref(null)

// 自动滚动到底部
watch(() => props.logs.length, async () => {
  await nextTick()
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
})
</script>

<style scoped>
.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}
.log-container {
  background: #1e1e1e;
  border-radius: 6px;
  padding: 12px;
  max-height: 240px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
.log-empty {
  color: #666;
  text-align: center;
  padding: 20px;
}
.log-line {
  line-height: 1.8;
  color: #d4d4d4;
}
.log-time {
  color: #6a9955;
  margin-right: 8px;
}
.log-msg {
  color: #d4d4d4;
}
</style>
