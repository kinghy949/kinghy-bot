<template>
  <div class="app-container">
    <div class="page-header">
      <h1>生成完成</h1>
      <p>软著材料已生成，请下载查看</p>
    </div>

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

    <el-row :gutter="20" style="margin-bottom: 32px;">
      <el-col :span="8" v-for="doc in documents" :key="doc.type">
        <DocumentCard
          :title="doc.title"
          :description="doc.description"
          :icon="doc.icon"
          :download-url="getDownloadUrl(taskId, doc.type)"
          :disabled="!store.outputFiles[doc.type]"
        />
      </el-col>
    </el-row>

    <div style="text-align: center;">
      <el-button type="primary" size="large" @click="downloadAll">
        <el-icon style="margin-right: 6px;"><Download /></el-icon>
        一键下载ZIP包
      </el-button>
      <el-button size="large" @click="router.push({ name: 'Home' })">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Download } from '@element-plus/icons-vue'
import DocumentCard from '../components/DocumentCard.vue'
import { getTaskState, getDownloadUrl } from '../api'
import { useGenerateStore } from '../stores/generate'

const props = defineProps({
  taskId: { type: String, required: true },
})

const router = useRouter()
const store = useGenerateStore()

const documents = [
  {
    type: 'source',
    title: '源程序文档',
    description: '格式化的源代码文档，含行号、页眉页脚',
    icon: '📄',
  },
  {
    type: 'manual',
    title: '操作手册',
    description: '含目录、截图和操作说明的用户手册',
    icon: '📘',
  },
  {
    type: 'application',
    title: '申请表',
    description: '部分字段需手动补充，已用黄色高亮标记',
    icon: '📋',
  },
]

onMounted(async () => {
  // 如果store中没有数据（页面刷新），从后端获取
  if (!store.status || store.taskId !== props.taskId) {
    try {
      const { data } = await getTaskState(props.taskId)
      store.updateProgress(data)
    } catch {
      router.push({ name: 'Home' })
    }
  }
})

function downloadAll() {
  window.open(getDownloadUrl(props.taskId, 'all'), '_blank')
}
</script>
