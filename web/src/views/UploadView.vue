<script setup lang="ts">
import { ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'

const defaultKind = ref<'full_face_selfie' | 'tongue_closeup'>('full_face_selfie')
const fileList = ref<{ name: string; size: string; kind: string }[]>([
  { name: 'sample_face_01.jpg', size: '1.2 MB', kind: 'full_face_selfie' },
  { name: 'tongue_only_02.png', size: '640 KB', kind: 'tongue_closeup' },
])

function handleMockAdd() {
  fileList.value.push({
    name: `upload_${Date.now()}.jpg`,
    size: '980 KB',
    kind: defaultKind.value,
  })
}
</script>

<template>
  <div>
    <p class="view-muted">
      每张图必须指定 <strong>image_kind</strong>。批量中可混合「全脸」与「特写」。后端对接后此处将调用真实上传 API。
    </p>
    <div class="view-card">
      <h3 class="view-heading">选择默认输入类型（新文件）</h3>
      <el-radio-group v-model="defaultKind" class="kind-group">
        <el-radio-button label="full_face_selfie">全脸自拍（需 SAM）</el-radio-button>
        <el-radio-button label="tongue_closeup">舌部特写（免 SAM）</el-radio-button>
      </el-radio-group>
    </div>
    <div class="view-card">
      <h3 class="view-heading">拖拽上传区</h3>
      <el-upload class="upload-area" drag action="#" :auto-upload="false" multiple>
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或 <em>点击选择</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 jpg / png；单文件建议 &lt; 20MB</div>
        </template>
      </el-upload>
      <el-button type="primary" style="margin-top: 12px" @click="handleMockAdd">
        演示：添加一条占位记录
      </el-button>
    </div>
    <div class="view-card">
      <h3 class="view-heading">待上传队列（演示）</h3>
      <el-table :data="fileList" size="small" stripe>
        <el-table-column prop="name" label="文件名" />
        <el-table-column prop="size" label="大小" width="100" />
        <el-table-column label="image_kind" width="220">
          <template #default="{ row }">
            <el-tag v-if="row.kind === 'full_face_selfie'" type="warning" size="small"
              >full_face_selfie</el-tag
            >
            <el-tag v-else type="success" size="small">tongue_closeup</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.upload-icon {
  font-size: 48px;
  color: var(--td-accent);
}
.kind-group {
  margin-top: 8px;
}
</style>
