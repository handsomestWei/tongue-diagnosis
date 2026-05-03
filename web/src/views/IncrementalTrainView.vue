<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '../lib/http'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

type ModelRow = { id: number; name: string; path: string }

const models = ref<ModelRow[]>([])
const parentId = ref<number | null>(null)
const epochs = ref(5)
const batch = ref(4)
const submitting = ref(false)

const selection = ref<'corrections_merged' | 'corrections_only' | 'all_manual'>('corrections_merged')

async function loadModels() {
  try {
    const { data } = await http.get<ModelRow[]>('/v1/models')
    models.value = data.filter((m) => m.path !== '_demo_placeholder_' && !m.path.includes('demo'))
    if (!parentId.value && models.value.length) parentId.value = models.value[0].id
  } catch {
    ElMessage.error('加载模型列表失败')
  }
}

async function submitIncremental() {
  if (!auth.canTrain) return
  if (parentId.value == null) {
    ElMessage.warning('请选择父模型（需磁盘上可读的 .pt）')
    return
  }
  submitting.value = true
  try {
    await http.post('/v1/train/incremental', {
      parent_model_id: parentId.value,
      epochs: epochs.value,
      batch: batch.value,
      selection: selection.value,
    })
    ElMessage.success('已提交增量训练，请到「模型训练」页刷新任务列表')
  } catch {
    ElMessage.error('提交失败（父模型路径可能无效）')
  } finally {
    submitting.value = false
  }
}

onMounted(() => void loadModels())
</script>

<template>
  <div>
    <p class="view-muted">
      <code>POST /api/v1/train/incremental</code>：按下方 <strong>数据选择策略</strong> 导出子集，在父模型权重上继续训练。默认
      <strong>纠错合并</strong>：全量 manual + 勾选「纳入再训练」的纠错覆盖类别。
    </p>
    <div class="view-card" style="max-width: 640px">
      <h3 class="view-heading">增量训练</h3>
      <el-form label-width="120px">
        <el-form-item label="父模型">
          <el-select v-model="parentId" placeholder="从模型库选择" filterable style="width: 100%">
            <el-option
              v-for="m in models"
              :key="m.id"
              :label="`${m.name} (id=${m.id})`"
              :value="m.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数据策略">
          <el-select v-model="selection" style="width: 100%">
            <el-option label="纠错合并（推荐）" value="corrections_merged" />
            <el-option label="仅纠错勾选样本" value="corrections_only" />
            <el-option label="全量 manual（等同全量训练导出）" value="all_manual" />
          </el-select>
        </el-form-item>
        <el-form-item label="epochs">
          <el-input-number v-model="epochs" :min="1" :max="200" />
        </el-form-item>
        <el-form-item label="batch">
          <el-input-number v-model="batch" :min="1" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" :disabled="!auth.canTrain" @click="submitIncremental">
            提交增量训练
          </el-button>
          <el-button @click="loadModels">刷新模型列表</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>
