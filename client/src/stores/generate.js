import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useGenerateStore = defineStore('generate', () => {
  // 任务状态
  const taskId = ref('')
  const status = ref('')  // pending / processing / completed / failed
  const currentStep = ref(0)
  const totalSteps = ref(6)
  const stepName = ref('')
  const progress = ref(0)
  const message = ref('')
  const warnings = ref([])
  const logs = ref([])
  const outputFiles = ref({})

  function updateProgress(data) {
    if (data.task_id) taskId.value = data.task_id
    if (data.status) status.value = data.status
    if (data.current_step !== undefined) currentStep.value = data.current_step
    if (data.total_steps !== undefined) totalSteps.value = data.total_steps
    if (data.step_name) stepName.value = data.step_name
    if (data.progress !== undefined) progress.value = data.progress
    if (data.message) message.value = data.message
    if (data.warnings) warnings.value = data.warnings
    if (data.logs) logs.value = data.logs
    if (data.output_files) outputFiles.value = data.output_files
  }

  function reset() {
    taskId.value = ''
    status.value = ''
    currentStep.value = 0
    stepName.value = ''
    progress.value = 0
    message.value = ''
    warnings.value = []
    logs.value = []
    outputFiles.value = {}
  }

  return {
    taskId, status, currentStep, totalSteps, stepName,
    progress, message, warnings, logs, outputFiles,
    updateProgress, reset,
  }
})
