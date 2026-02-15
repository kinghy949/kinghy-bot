<template>
  <div class="step-indicator">
    <el-steps :active="currentStep - 1" finish-status="success" align-center>
      <el-step v-for="step in steps" :key="step.num" :title="step.title" />
    </el-steps>
  </div>
</template>

<script setup>
defineProps({
  currentStep: { type: Number, default: 0 },
  totalSteps: { type: Number, default: 6 },
})

const steps = [
  { num: 1, title: '功能清单' },
  { num: 2, title: '生成代码' },
  { num: 3, title: 'HTML页面' },
  { num: 4, title: '页面截图' },
  { num: 5, title: '生成文档' },
  { num: 6, title: '打包下载' },
]
</script>

<style scoped>
.step-indicator {
  padding: 10px 0;
}
</style>
