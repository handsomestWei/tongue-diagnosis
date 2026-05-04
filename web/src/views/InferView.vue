<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { http } from '../lib/http'

const auth = useAuthStore()

type ImageKind = 'full_face_selfie' | 'tongue_closeup'

const mode = ref<'file' | 'id'>('file')
const imageKind = ref<ImageKind>('tongue_closeup')
const imageId = ref<number | null>(null)
const topk = ref(3)
const inferring = ref(false)

type ResultRow = {
  file: string
  kind: string
  pred: string
  conf: number
  demo?: boolean
  sam?: string
  predId?: number | null
}

const persistPred = ref(false)
const modelIdForPersist = ref<number | null>(null)

type InferResp = {
  topk: { class: string; score: number }[]
  demo: boolean
  message: string
  image_kind: string
  sam_called: boolean
  sam_failed: boolean
  prediction_id?: number | null
}

const results = ref<ResultRow[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)

async function runInfer() {
  inferring.value = true
  try {
    const fd = new FormData()
    fd.append('topk', String(topk.value))
    if (mode.value === 'id') {
      if (imageId.value == null || imageId.value < 1) {
        ElMessage.warning('请输入有效的 image_id')
        return
      }
      fd.append('image_id', String(imageId.value))
      if (persistPred.value) {
        fd.append('persist', 'true')
        if (modelIdForPersist.value != null && modelIdForPersist.value >= 1) {
          fd.append('model_id', String(modelIdForPersist.value))
        }
      }
    } else {
      const input = fileInputRef.value
      const file = input?.files?.[0]
      if (!file) {
        ElMessage.warning('请先选择一张图片')
        return
      }
      fd.append('image_kind', imageKind.value)
      fd.append('file', file)
    }
    const { data } = await http.post<InferResp>('/v1/infer', fd)

    const best = data.topk[0]
    const label =
      mode.value === 'id' ? `id=${imageId.value}` : fileInputRef.value?.files?.[0]?.name ?? 'file'
    results.value = [
      {
        file: label,
        kind: data.image_kind,
        pred: best?.class ?? '—',
        conf: best?.score ?? 0,
        demo: data.demo,
        sam: data.sam_called ? (data.sam_failed ? 'SAM 回退' : 'SAM') : '无',
        predId: data.prediction_id,
      },
      ...results.value,
    ].slice(0, 20)
    ElMessage.success(data.demo ? `演示：${data.message}` : data.message || '推理完成')
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
      <code>POST /api/v1/infer</code>：上传文件时需 <code>image_kind</code>；或仅传
      <code>image_id</code>（从库读取类型与文件）。配置
      <code>CLASSIFY_WEIGHTS_PATH</code> 后使用真实 YOLO；否则返回演示 top-k。
      全脸图会尝试子进程跑 TongueSAM（需权重与依赖）。
    </p>
    <div class="view-card">
      <el-form inline>
        <el-form-item label="来源">
          <el-radio-group v-model="mode">
            <el-radio-button label="file">上传文件</el-radio-button>
            <el-radio-button label="id">库内 image_id</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <template v-if="mode === 'file'">
          <el-form-item label="image_kind">
            <el-select v-model="imageKind" style="width: 220px">
              <el-option label="全脸自拍（需 SAM）" value="full_face_selfie" />
              <el-option label="舌部特写（免 SAM）" value="tongue_closeup" />
            </el-select>
          </el-form-item>
          <el-form-item label="文件">
            <input ref="fileInputRef" type="file" accept="image/*" />
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="image_id">
            <el-input-number v-model="imageId" :min="1" :step="1" />
          </el-form-item>
          <el-form-item label="落库预测">
            <el-switch v-model="persistPred" />
          </el-form-item>
          <el-form-item v-if="persistPred" label="model_id">
            <el-input-number v-model="modelIdForPersist" :min="1" :step="1" placeholder="可选，默认用默认模型" />
          </el-form-item>
        </template>
        <el-form-item label="Top-K">
          <el-input-number v-model="topk" :min="1" :max="10" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="inferring" @click="runInfer"> 推理 </el-button>
        </el-form-item>
      </el-form>
      <el-table :data="results" stripe class="mt">
        <el-table-column prop="file" label="标识" />
        <el-table-column label="image_kind" width="170">
          <template #default="{ row }">
            <el-tag v-if="row.kind === 'full_face_selfie'" type="warning" size="small">{{
              row.kind
            }}</el-tag>
            <el-tag v-else type="success" size="small">{{ row.kind }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sam" label="SAM" width="100" />
        <el-table-column prop="pred" label="预测类别" />
        <el-table-column prop="conf" label="置信度">
          <template #default="{ row }">
            {{ (row.conf * 100).toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column label="预测 ID" width="90">
          <template #default="{ row }">
            <span>{{ row.predId ?? '—' }}</span>
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
