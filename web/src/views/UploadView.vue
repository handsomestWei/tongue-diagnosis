<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { UploadRequestOptions } from 'element-plus'
import { http } from '../lib/http'

type ImageKind = 'full_face_selfie' | 'tongue_closeup'

type ImageRow = {
  id: number
  original_filename: string
  image_kind: string
  storage_path: string
}

const defaultKind = ref<ImageKind>('full_face_selfie')
const rows = ref<ImageRow[]>([])
const loading = ref(false)

async function refresh() {
  loading.value = true
  try {
    const { data } = await http.get<ImageRow[]>('/v1/images', { params: { limit: 50 } })
    rows.value = data
  } catch (e) {
    console.error(e)
    ElMessage.error('加载图片列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void refresh()
})

async function customUpload(req: UploadRequestOptions) {
  const fd = new FormData()
  fd.append('file', req.file as File)
  fd.append('image_kind', defaultKind.value)
  try {
    await http.post('/v1/images/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success('上传成功')
    await refresh()
    req.onSuccess?.({})
  } catch {
    ElMessage.error('上传失败')
  }
}
</script>

<template>
  <div>
    <p class="view-muted">
      每张图必须指定 <strong>image_kind</strong>。批量中可混合「全脸」与「特写」（逐文件重选类型后上传）。
    </p>
    <div class="view-card">
      <h3 class="view-heading">选择默认输入类型（新文件）</h3>
      <el-radio-group v-model="defaultKind" class="kind-group">
        <el-radio-button label="full_face_selfie">全脸自拍（需 SAM）</el-radio-button>
        <el-radio-button label="tongue_closeup">舌部特写（免 SAM）</el-radio-button>
      </el-radio-group>
    </div>
    <div class="view-card">
      <h3 class="view-heading">拖拽上传</h3>
      <el-upload class="upload-area" drag :http-request="customUpload" :show-file-list="false" multiple>
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或 <em>点击选择</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 jpg / png；调用 <code>POST /api/v1/images/upload</code></div>
        </template>
      </el-upload>
    </div>
    <div class="view-card">
      <h3 class="view-heading">最近上传（数据库）</h3>
      <el-button size="small" :loading="loading" @click="refresh">刷新</el-button>
      <el-table v-loading="loading" :data="rows" size="small" stripe class="mt">
        <el-table-column prop="id" label="ID" width="64" />
        <el-table-column prop="original_filename" label="文件名" />
        <el-table-column label="image_kind" width="200">
          <template #default="{ row }">
            <el-tag v-if="row.image_kind === 'full_face_selfie'" type="warning" size="small">{{
              row.image_kind
            }}</el-tag>
            <el-tag v-else type="success" size="small">{{ row.image_kind }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="storage_path" label="相对路径" show-overflow-tooltip />
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
.mt {
  margin-top: 12px;
}
</style>
