<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '../lib/http'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

type ModelRow = { id: number; name: string; path: string; is_default: boolean; status: string }

const models = ref<ModelRow[]>([])
const loading = ref(false)
const reg = ref({ name: '', path: '', set_default: false })

async function refresh() {
  loading.value = true
  try {
    const { data } = await http.get<ModelRow[]>('/v1/models')
    models.value = data
  } catch {
    ElMessage.error('加载模型列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void refresh()
})

async function register() {
  if (!auth.canManageModels) return
  if (!reg.value.name || !reg.value.path) {
    ElMessage.warning('请填写名称与路径')
    return
  }
  try {
    await http.post('/v1/models', {
      name: reg.value.name,
      path: reg.value.path,
      set_default: reg.value.set_default,
    })
    ElMessage.success('已注册')
    reg.value = { name: '', path: '', set_default: false }
    await refresh()
  } catch {
    ElMessage.error('注册失败（需 admin）')
  }
}
</script>

<template>
  <div>
    <p class="view-muted">
      注册训练产物，设置默认推理模型；数据来自 <code>model_registry</code> 表。
    </p>
    <div v-if="auth.canManageModels" class="view-card">
      <h3 class="view-heading">注册模型</h3>
      <el-form inline label-width="72px">
        <el-form-item label="名称">
          <el-input v-model="reg.name" placeholder="如 v0.2-cls" style="width: 160px" />
        </el-form-item>
        <el-form-item label="路径">
          <el-input v-model="reg.path" placeholder="/path/to/best.pt" style="width: 260px" />
        </el-form-item>
        <el-form-item label="默认">
          <el-switch v-model="reg.set_default" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="register">注册</el-button>
        </el-form-item>
      </el-form>
    </div>
    <div class="view-card">
      <el-button size="small" :loading="loading" @click="refresh">刷新</el-button>
      <el-table v-loading="loading" :data="models" stripe class="mt">
        <el-table-column prop="name" label="名称" width="140" />
        <el-table-column prop="path" label="权重路径" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="默认" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success" size="small">当前</el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.mt {
  margin-top: 12px;
}
</style>
