<template>
  <el-card class="document-card card-shadow" :class="{ disabled }">
    <div class="doc-icon">{{ icon }}</div>
    <h3 class="doc-title">{{ title }}</h3>
    <p class="doc-desc">{{ description }}</p>
    <el-button
      type="primary"
      :disabled="disabled"
      @click="handleDownload"
      style="width: 100%;"
    >
      <el-icon style="margin-right: 4px;"><Download /></el-icon>
      下载
    </el-button>
  </el-card>
</template>

<script setup>
import { Download } from '@element-plus/icons-vue'

const props = defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  icon: { type: String, default: '📄' },
  downloadUrl: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

function handleDownload() {
  if (props.downloadUrl && !props.disabled) {
    window.open(props.downloadUrl, '_blank')
  }
}
</script>

<style scoped>
.document-card {
  text-align: center;
  padding: 20px;
  transition: transform 0.2s;
}
.document-card:hover:not(.disabled) {
  transform: translateY(-4px);
}
.document-card.disabled {
  opacity: 0.5;
}
.doc-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.doc-title {
  font-size: 16px;
  color: #303133;
  margin: 0 0 8px;
}
.doc-desc {
  font-size: 13px;
  color: #909399;
  margin: 0 0 16px;
  min-height: 36px;
}
</style>
