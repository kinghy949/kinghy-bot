<template>
  <el-card class="card-shadow">
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      label-position="top"
      size="large"
    >
      <el-form-item label="软著名称" prop="software_name">
        <el-input
          v-model="form.software_name"
          placeholder="例如：基于SpringBoot的智能仓储管理系统"
          maxlength="60"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="项目描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="一句话描述项目功能，例如：一个用于企业仓库进出库管理、库存盘点和数据统计的Web管理系统"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="技术栈" prop="tech_stack">
        <el-select v-model="form.tech_stack" placeholder="请选择技术栈" style="width: 100%;">
          <el-option
            v-for="stack in techStacks"
            :key="stack.id"
            :label="stack.name"
            :value="stack.id"
          >
            <span>{{ stack.name }}</span>
            <span style="color: #909399; font-size: 12px; margin-left: 8px;">{{ stack.description }}</span>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="目标代码行数">
        <el-slider
          v-model="form.target_lines"
          :min="3000"
          :max="8000"
          :step="500"
          :marks="lineMarks"
          show-input
        />
      </el-form-item>

      <el-form-item label="开发完成日期" prop="completion_date">
        <el-date-picker
          v-model="form.completion_date"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 100%;"
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" size="large" @click="handleSubmit" :loading="submitting" style="width: 100%;">
          开始生成
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getTechStacks } from '../api'

const emit = defineEmits(['submit'])

const formRef = ref(null)
const submitting = ref(false)
const techStacks = ref([])

const today = new Date().toISOString().split('T')[0]

const form = reactive({
  software_name: '',
  description: '',
  tech_stack: 'springboot_vue',
  target_lines: 5000,
  completion_date: today,
})

const lineMarks = {
  3000: '3000',
  5000: '5000',
  8000: '8000',
}

const rules = {
  software_name: [
    { required: true, message: '请输入软著名称', trigger: 'blur' },
    { min: 4, max: 60, message: '长度在4到60个字符', trigger: 'blur' },
  ],
  description: [
    { required: true, message: '请输入项目描述', trigger: 'blur' },
  ],
  tech_stack: [
    { required: true, message: '请选择技术栈', trigger: 'change' },
  ],
  completion_date: [
    { required: true, message: '请选择开发完成日期', trigger: 'change' },
  ],
}

onMounted(async () => {
  try {
    const { data } = await getTechStacks()
    techStacks.value = data
  } catch {
    // 降级使用默认选项
    techStacks.value = [
      { id: 'springboot_vue', name: 'SpringBoot + Vue3', description: 'Java系企业管理系统' },
      { id: 'flask_vue', name: 'Flask + Vue3', description: 'Python系Web应用' },
      { id: 'django_vue', name: 'Django + Vue3', description: 'Python系中大型项目' },
    ]
  }
})

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    emit('submit', { ...form })
  } finally {
    submitting.value = false
  }
}
</script>
