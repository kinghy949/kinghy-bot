<template>
  <div class="app-container">
    <div class="page-header">
      <h1>软著材料自动生成系统</h1>
      <p>输入软著信息，自动生成源代码文档、操作手册和申请表</p>
    </div>
    <ProjectForm @submit="handleSubmit" />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ProjectForm from '../components/ProjectForm.vue'
import { submitGenerate } from '../api'
import { useGenerateStore } from '../stores/generate'

const router = useRouter()
const store = useGenerateStore()

async function handleSubmit(formData) {
  try {
    store.reset()
    const { data } = await submitGenerate(formData)
    store.taskId = data.task_id
    router.push({ name: 'Progress', params: { taskId: data.task_id } })
  } catch (err) {
    const msg = err.response?.data?.error || '提交失败，请重试'
    ElMessage.error(msg)
  }
}
</script>
