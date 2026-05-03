<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '../lib/http'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const form = ref({
  dataVersion: 'v20260201-default',
  model: 'yolov8n-cls.pt',
  epochs: 80,
  imgsz: 224,
  batch: 8,
})

type TrainListItem = { id: string; status: string; created_at: string; message?: string }

const jobs = ref<TrainListItem[]>([])
const loading = ref(false)

function progressForStatus(status: string): number {
  if (status === 'success') return 100
  if (status === 'running') return 50
  if (status === 'failed') return 0
  return 5
}

const tableRows = computed(() =>
  jobs.value.map((j) => ({
    id: j.id,
    status: j.status,
    progress: progressForStatus(j.status),
    kindMix: j.status === 'failed' ? '失败' : j.status === 'running' ? '导出/训练中…' : '—',
  })),
)

async function refresh() {
  loading.value = true
  try {
    const { data } = await http.get<TrainListItem[]>('/v1/train')
    jobs.value = data
  } catch {
    ElMessage.error('加载训练任务失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void refresh()
})

async function submitTrain() {
  if (!auth.canTrain) return
  try {
    await http.post('/v1/train', {
      data_version: form.value.dataVersion,
      model: form.value.model,
      epochs: form.value.epochs,
      imgsz: form.value.imgsz,
      batch: form.value.batch,
      val_ratio: 0.2,
      register_name: `cls-${Date.now()}`,
      set_as_default: false,
    })
    ElMessage.success('训练已在后台启动（导出+YOLO）；请稍后刷新任务列表')
    await refresh()
  } catch {
    ElMessage.error('提交失败或无权限（需已有人工标注图片）')
  }
}
</script>

<template>
  <div>
    <p class="view-muted">
      训练导出将按每张图的 <code>image_kind</code> 走统一预处理，生成规范舌图后再送入 YOLO classify（CPU）。
    </p>
    <el-row :gutter="16">
      <el-col :xs="24" :lg="10">
        <div class="view-card">
          <h3 class="view-heading">发起全量训练</h3>
          <el-form :model="form" label-width="100px">
            <el-form-item label="数据版本">
              <el-input v-model="form.dataVersion" />
            </el-form-item>
            <el-form-item label="预训练">
              <el-input v-model="form.model" />
            </el-form-item>
            <el-form-item label="epochs">
              <el-input-number v-model="form.epochs" :min="1" />
            </el-form-item>
            <el-form-item label="imgsz">
              <el-input-number v-model="form.imgsz" :min="32" :step="32" />
            </el-form-item>
            <el-form-item label="batch">
              <el-input-number v-model="form.batch" :min="1" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :disabled="!auth.canTrain" @click="submitTrain">
                提交训练任务
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
      <el-col :xs="24" :lg="14">
        <div class="view-card">
          <h3 class="view-heading">任务列表</h3>
          <el-button size="small" :loading="loading" @click="refresh">刷新</el-button>
          <el-table v-loading="loading" :data="tableRows" stripe class="mt">
            <el-table-column prop="id" label="任务 ID" width="280" />
            <el-table-column prop="kindMix" label="样本构成" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'running'" type="warning">训练中</el-tag>
                <el-tag v-else-if="row.status === 'pending'" type="info">待处理</el-tag>
                <el-tag v-else-if="row.status === 'failed'" type="danger">失败</el-tag>
                <el-tag v-else type="success">完成</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="进度" width="200">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.progress"
                  :status="row.status === 'success' ? 'success' : undefined"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="view-card">
          <h3 class="view-heading">说明</h3>
          <pre class="log-box">需要至少一张图含「人工标注」。任务在服务端线程中执行：导出 YOLO 目录 → Ultralytics 训练 → 注册 best.pt。日志路径见 GET /api/v1/train/{id}。</pre>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.log-box {
  margin: 0;
  padding: 12px;
  background: var(--td-surface-2, #111);
  border-radius: 8px;
  font-size: 12px;
  color: var(--td-muted, #aaa);
  max-height: 220px;
  overflow: auto;
}
.mt {
  margin-top: 12px;
}
</style>
