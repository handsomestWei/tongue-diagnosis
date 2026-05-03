<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { http } from '../lib/http'

const auth = useAuthStore()

type PredRow = {
  id: number
  image_id: number
  model_id: number
  pred_class: string | null
  confidence: number | null
  demo: boolean
}

type RowForm = { correctClass: string; remark: string; includeTrain: boolean }

const rows = ref<PredRow[]>([])
const rowForms = reactive<Record<number, RowForm>>({})
const loading = ref(false)

function formFor(id: number): RowForm {
  if (!rowForms[id]) {
    rowForms[id] = { correctClass: '', remark: '', includeTrain: true }
  }
  return rowForms[id]
}

async function refresh() {
  loading.value = true
  try {
    const { data } = await http.get<PredRow[]>('/v1/predictions', { params: { limit: 100 } })
    rows.value = data
    for (const r of data) {
      const f = formFor(r.id)
      if (!f.correctClass.trim() && r.pred_class) {
        f.correctClass = r.pred_class
      }
    }
  } catch {
    ElMessage.error('加载预测列表失败')
  } finally {
    loading.value = false
  }
}

async function submitCorrection(row: PredRow) {
  const f = formFor(row.id)
  if (!f.correctClass.trim()) {
    ElMessage.warning('请填写该行纠正类别')
    return
  }
  try {
    await http.post(`/v1/predictions/${row.id}/correct`, {
      correct_class: f.correctClass.trim(),
      remark: f.remark.trim() || undefined,
      include_in_next_train: f.includeTrain,
    })
    ElMessage.success('已提交纠错并更新人工标签')
    f.remark = ''
    await refresh()
  } catch {
    ElMessage.error('提交失败')
  }
}

onMounted(() => {
  void refresh()
})
</script>

<template>
  <div>
    <p class="view-muted">
      每行独立填写纠正类别与「纳入再训练」；纠错写入 <code>corrections</code> 并同步人工标签；勾选纳入增量导出筛选（见
      <code>POST /train/incremental</code> 的 <code>selection</code>）。
    </p>
    <div class="view-card">
      <div class="mb">
        <el-button :loading="loading" @click="refresh">刷新</el-button>
      </div>
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="id" label="预测 ID" width="90" />
        <el-table-column prop="image_id" label="图片 ID" width="90" />
        <el-table-column prop="pred_class" label="模型预测" width="100" />
        <el-table-column label="置信度" width="100">
          <template #default="{ row }">
            <span v-if="row.confidence != null">{{ (row.confidence * 100).toFixed(1) }}%</span>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="演示" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.demo" size="small" type="info">demo</el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="纠正为" min-width="140">
          <template #default="{ row }">
            <el-input v-model="formFor(row.id).correctClass" placeholder="类别" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="120">
          <template #default="{ row }">
            <el-input v-model="formFor(row.id).remark" placeholder="可选" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="纳入再训练" width="110" align="center">
          <template #default="{ row }">
            <el-checkbox v-model="formFor(row.id).includeTrain" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :disabled="!auth.canMutateReview"
              @click="submitCorrection(row)"
            >
              提交
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.mb {
  margin-bottom: 12px;
}
</style>
