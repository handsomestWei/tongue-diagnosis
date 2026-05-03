<script setup lang="ts">
import { onMounted, ref } from 'vue'
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

const rows = ref<PredRow[]>([])
const loading = ref(false)
const correctClass = ref('')
const includeTrain = ref(true)
const remark = ref('')

async function refresh() {
  loading.value = true
  try {
    const { data } = await http.get<PredRow[]>('/v1/predictions', { params: { limit: 100 } })
    rows.value = data
  } catch {
    ElMessage.error('加载预测列表失败')
  } finally {
    loading.value = false
  }
}

async function submitCorrection(row: PredRow) {
  if (!correctClass.value.trim()) {
    ElMessage.warning('请填写纠正类别')
    return
  }
  try {
    await http.post(`/v1/predictions/${row.id}/correct`, {
      correct_class: correctClass.value.trim(),
      remark: remark.value || undefined,
      include_in_next_train: includeTrain.value,
    })
    ElMessage.success('已提交纠错并更新人工标签')
    correctClass.value = ''
    remark.value = ''
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
      人工纠正会写入 <code>corrections</code> 并同步 <code>Patch /images/{id}/labels</code>；勾选纳入增量数据供后续训练筛选。
    </p>
    <div class="view-card">
      <el-form inline class="mb">
        <el-form-item label="默认纠正为">
          <el-input v-model="correctClass" placeholder="如 红舌" style="width: 160px" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="remark" placeholder="可选" style="width: 200px" />
        </el-form-item>
        <el-form-item label="纳入再训练">
          <el-checkbox v-model="includeTrain" />
        </el-form-item>
        <el-form-item>
          <el-button :loading="loading" @click="refresh">刷新</el-button>
        </el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="id" label="预测 ID" width="90" />
        <el-table-column prop="image_id" label="图片 ID" width="90" />
        <el-table-column prop="pred_class" label="模型预测" />
        <el-table-column label="置信度">
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
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :disabled="!auth.canMutateReview"
              @click="submitCorrection(row)"
            >
              用上方类别纠正
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
