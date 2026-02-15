<template>
  <div class="app-container">
    <div class="page-header">
      <h1>生成中...</h1>
      <p>生成过程约需3-8分钟，请勿关闭页面</p>
    </div>

    <el-card class="card-shadow" style="margin-bottom: 24px;">
      <StepIndicator :current-step="store.currentStep" :total-steps="store.totalSteps" />
    </el-card>

    <el-card class="card-shadow" style="margin-bottom: 24px;">
      <ProgressTracker
        :step-name="store.stepName"
        :progress="store.progress"
        :message="store.message"
        :status="store.status"
      />
    </el-card>

    <el-card class="card-shadow" style="margin-bottom: 24px;">
      <LogPanel :logs="store.logs" />
    </el-card>

    <div v-if="store.warnings.length" style="margin-bottom: 24px;">
      <el-alert
        v-for="(w, i) in store.warnings"
        :key="i"
        :title="w"
        type="warning"
        show-icon
        :closable="false"
        style="margin-bottom: 8px;"
      />
    </div>

    <div style="text-align: center;">
      <el-button
        v-if="store.status === 'processing' || store.status === 'pending'"
        type="danger"
        @click="handleCancel"
      >
        取消任务
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import StepIndicator from '../components/StepIndicator.vue'
import ProgressTracker from '../components/ProgressTracker.vue'
import LogPanel from '../components/LogPanel.vue'
import { createTaskStream, getTaskState, cancelTask } from '../api'
import { useGenerateStore } from '../stores/generate'

const props = defineProps({
  taskId: { type: String, required: true },
})

const router = useRouter()
const store = useGenerateStore()
let eventSource = null
let pollTimer = null

onMounted(() => {
  startSSE()
})

onUnmounted(() => {
  cleanup()
})

// 任务完成时跳转结果页
watch(() => store.status, (val) => {
  if (val === 'completed') {
    cleanup()
    setTimeout(() => {
      router.push({ name: 'Result', params: { taskId: props.taskId } })
    }, 1000)
  }
  if (val === 'failed') {
    cleanup()
    ElMessage.error(store.message || '生成失败')
  }
})

function startSSE() {
  eventSource = createTaskStream(
    props.taskId,
    (data) => store.updateProgress(data),
    () => startPolling(),
  )
}

function startPolling() {
  pollTimer = setInterval(async () => {
    try {
      const { data } = await getTaskState(props.taskId)
      store.updateProgress(data)
      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(pollTimer)
      }
    } catch {
      // 忽略轮询错误
    }
  }, 2000)
}

async function handleCancel() {
  try {
    await cancelTask(props.taskId)
    ElMessage.info('任务已取消')
    router.push({ name: 'Home' })
  } catch {
    ElMessage.error('取消失败')
  }
}

function cleanup() {
  if (eventSource) eventSource.close()
  if (pollTimer) clearInterval(pollTimer)
}
</script>
