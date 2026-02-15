<template>
  <div class="progress-tracker">
    <div class="progress-header">
      <span class="step-name">{{ stepName || '等待中...' }}</span>
      <span class="status-tag">
        <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
      </span>
    </div>
    <el-progress
      :percentage="progress"
      :status="progressStatus"
      :stroke-width="20"
      striped
      striped-flow
      style="margin: 16px 0;"
    />
    <p class="message">{{ message }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  stepName: { type: String, default: '' },
  progress: { type: Number, default: 0 },
  message: { type: String, default: '' },
  status: { type: String, default: 'pending' },
})

const statusType = computed(() => {
  const map = { pending: 'info', processing: '', completed: 'success', failed: 'danger' }
  return map[props.status] || 'info'
})

const statusText = computed(() => {
  const map = { pending: '等待中', processing: '处理中', completed: '已完成', failed: '失败' }
  return map[props.status] || props.status
})

const progressStatus = computed(() => {
  if (props.status === 'failed') return 'exception'
  if (props.progress >= 100) return 'success'
  return ''
})
</script>

<style scoped>
.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.step-name {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}
.message {
  color: #606266;
  font-size: 13px;
  margin: 0;
}
</style>
