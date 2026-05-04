<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '../lib/http'

type ImageRow = {
  id: number
  image_kind: string
  original_filename: string
  storage_path: string
  derived_tongue_path?: string | null
}

type LabelRow = { id: number; class_name: string; source: string }

type ImageDetail = ImageRow & { labels: LabelRow[] }

const rows = ref<ImageRow[]>([])
const selectedId = ref<number | null>(null)
const detail = ref<ImageDetail | null>(null)
const loading = ref(false)
const saving = ref(false)

const selectedKind = ref<string>('full_face_selfie')
const labelValue = ref<string>('')

const classes = ['淡红舌', '红舌', '淡白舌', '紫舌']

const objectUrls = ref<string[]>([])

function revokeAll() {
  objectUrls.value.forEach(URL.revokeObjectURL)
  objectUrls.value = []
}

const previewUrl = ref<string | null>(null)

async function loadPreview(row?: ImageRow) {
  revokeAll()
  previewUrl.value = null
  if (!row) return
  try {
    const params: Record<string, string> = {}
    if (row.derived_tongue_path) {
      params.rel = row.derived_tongue_path
    }
    const res = await http.get(`/v1/images/${row.id}/file`, {
      params: Object.keys(params).length ? params : undefined,
      responseType: 'blob',
    })
    const url = URL.createObjectURL(res.data)
    objectUrls.value.push(url)
    previewUrl.value = url
  } catch {
    previewUrl.value = null
  }
}

onUnmounted(() => {
  revokeAll()
})

async function refreshList() {
  loading.value = true
  try {
    const { data } = await http.get<ImageRow[]>('/v1/images', { params: { limit: 200 } })
    rows.value = data
    if (!selectedId.value && data.length) selectedId.value = data[0].id
  } catch {
    ElMessage.error('加载图片列表失败')
  } finally {
    loading.value = false
  }
}

async function openImage(id: number) {
  selectedId.value = id
  try {
    const { data } = await http.get<ImageDetail>(`/v1/images/${id}`)
    detail.value = data
    selectedKind.value = data.image_kind
    const manual = data.labels.filter((l) => l.source === 'manual').pop()
    labelValue.value = manual?.class_name ?? ''
    const row = rows.value.find((r) => r.id === id)
    await loadPreview(row ?? { ...data, storage_path: data.storage_path })
  } catch {
    ElMessage.error('加载详情失败')
  }
}

async function saveCurrent() {
  if (!detail.value) return
  saving.value = true
  try {
    await http.patch(`/v1/images/${detail.value.id}`, {
      image_kind: selectedKind.value,
    })
    if (labelValue.value) {
      await http.patch(`/v1/images/${detail.value.id}/labels`, {
        class_name: labelValue.value,
      })
    }
    ElMessage.success('已保存')
    await refreshList()
    await openImage(detail.value.id)
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  void refreshList().then(() => {
    if (selectedId.value) void openImage(selectedId.value)
  })
})
</script>

<template>
  <div>
    <p class="view-muted">
      从库中打开图片，更正 <strong>image_kind</strong> 与人工标签；与训练导出共用同一预处理逻辑。
    </p>
    <el-row :gutter="16">
      <el-col :xs="24" :md="10">
        <div class="view-card">
          <h3 class="view-heading">当前图片</h3>
          <div v-if="detail" class="thumb-box">
            <img v-if="previewUrl" :src="previewUrl" alt="preview" class="thumb-img" />
            <div v-else class="ph-inner">加载预览中…</div>
            <small class="meta">#{{ detail.id }} · {{ detail.original_filename }}</small>
          </div>
          <div v-else class="ph-thumb">
            <span>请选择左侧列表中的图片</span>
          </div>
          <el-form label-position="top" class="mini-form">
            <el-form-item label="image_kind">
              <el-select v-model="selectedKind" style="width: 100%">
                <el-option label="full_face_selfie（全脸）" value="full_face_selfie" />
                <el-option label="tongue_closeup（特写）" value="tongue_closeup" />
              </el-select>
            </el-form-item>
            <el-form-item label="分类标签（人工）">
              <el-select v-model="labelValue" placeholder="选择舌象类别" style="width: 100%" filterable allow-create>
                <el-option v-for="c in classes" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
            <el-button type="primary" :loading="saving" :disabled="!detail" @click="saveCurrent">
              保存
            </el-button>
            <el-button @click="refreshList" :loading="loading">刷新列表</el-button>
          </el-form>
        </div>
      </el-col>
      <el-col :xs="24" :md="14">
        <div class="view-card">
          <h3 class="view-heading">图片列表</h3>
          <el-table
            v-loading="loading"
            :data="rows"
            size="small"
            stripe
            highlight-current-row
            @row-click="(r: ImageRow) => openImage(r.id)"
          >
            <el-table-column prop="id" label="ID" width="72" />
            <el-table-column prop="original_filename" label="文件名" show-overflow-tooltip />
            <el-table-column label="类型" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.image_kind === 'full_face_selfie'" type="warning" size="small">全脸</el-tag>
                <el-tag v-else type="success" size="small">特写</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click.stop="openImage(row.id)">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.ph-thumb {
  height: 200px;
  border-radius: 10px;
  background: linear-gradient(135deg, #e0f0f0 0%, #c8e0e0 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--td-muted);
  margin-bottom: 16px;
}
.thumb-box {
  margin-bottom: 16px;
  text-align: center;
}
.thumb-img {
  max-width: 100%;
  max-height: 220px;
  border-radius: 10px;
  object-fit: contain;
  background: #111;
}
.ph-inner {
  padding: 48px;
  color: var(--td-muted);
}
.meta {
  display: block;
  margin-top: 8px;
  opacity: 0.85;
  font-size: 12px;
}
.mini-form {
  max-width: 100%;
}
</style>
