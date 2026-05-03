<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { http } from '../lib/http'

const auth = useAuthStore()

type ImageKind = 'full_face_selfie' | 'tongue_closeup'

const imageKind = ref<ImageKind>('tongue_closeup')
const topk = ref(3)
const inferring = ref(false)

type ResultRow = { file: string; kind: string; pred: string; conf: number }

const results = ref<ResultRow[]>([
  { file: 'a_01.jpg', kind: 'full_face_selfie', pred: '淡红舌', conf: 0.91 },
  { file: 'b_02.jpg', kind: 'tongue_closeup', pred: '红舌', conf: 0.72 },
])

const fileInputRef = ref<HTMLInputElement | null>(null)

async function runDemoInfer() {
  const input = fileInputRef.value
  const file = input?.files?.[0]
  if (!file) {
    ElMessage.warning('请先选择一张图片')
    return
  }
  inferring.value = true
  try {
    const fd = new FormData()
    fd.append('image_kind', imageKind.value)
    fd.append('topk', String(topk.value))
    fd.append('file', file)
    const { data } = await http.post<{ topk: { class: string; score: number }[]; demo: boolean }>(
      '/v1/infer',
      fd,
    )
    const best = data.topk[0]
    results.value = [
      {
        file: file.name,
        kind: imageKind.value,
        pred: best?.class ?? '—',
        conf: best?.score ?? 0,
      },
      ...results.value,
    ].slice(0, 20)
    ElMessage.success(data.demo ? '演示推理完成（未加载真实权重）' : '推理完成')
  } catch {
    ElMessage.error('推理失败或未登录')
  } finally {
    inferring.value = false
  }
}
</script>

<template>
  <div>
    <p class="view-muted">
      推理请求须携带 <code>image_kind</code>。下方可先调用占位接口 <code>POST /api/v1/infer</code>（返回固定 top-k）。
    </p>
    <div class="view-card">
      <el-form inline>
        <el-form-item label="image_kind">
          <el-select v-model="imageKind" style="width: 220px">
            <el-option label="全脸自拍（需 SAM）" value="full_face_selfie" />
            <el-option label="舌部特写（免 SAM）" value="tongue_closeup" />
          </el-select>
        </el-form-item>
        <el-form-item label="Top-K">
          <el-input-number v-model="topk" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="文件">
          <input ref="fileInputRef" type="file" accept="image/*" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="inferring" @click="runDemoInfer">
            演示推理
          </el-button>
        </el-form-item>
      </el-form>
      <el-table :data="results" stripe class="mt">
        <el-table-column prop="file" label="文件" />
        <el-table-column label="image_kind" width="170">
          <template #default="{ row }">
            <el-tag v-if="row.kind === 'full_face_selfie'" type="warning" size="small">{{
              row.kind
            }}</el-tag>
            <el-tag v-else type="success" size="small">{{ row.kind }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="pred" label="预测类别" />
        <el-table-column prop="conf" label="置信度">
          <template #default="{ row }">
            {{ (row.conf * 100).toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default>
            <el-button link type="primary" size="small" :disabled="!auth.canMutateReview"
              >纠错</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.mt {
  margin-top: 16px;
}
</style>
