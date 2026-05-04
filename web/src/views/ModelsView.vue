<script setup lang="ts">
const models = [
  { id: 'm1', name: 'v0.2-cls', path: '/storage/models/v0.2/best.pt', default: true, metrics: 'top1 0.83' },
  { id: 'm2', name: 'v0.1-cls', path: '/storage/models/v0.1/best.pt', default: false, metrics: 'top1 0.78' },
]
</script>

<template>
  <div>
    <p class="view-muted">注册训练产物，设置默认推理模型；对接 ModelRegistry 表。</p>
    <div class="view-card">
      <el-button type="primary" style="margin-bottom: 12px">从最新训练任务注册</el-button>
      <el-table :data="models" stripe>
        <el-table-column prop="name" label="名称" width="120" />
        <el-table-column prop="path" label="权重路径" />
        <el-table-column prop="metrics" label="指标" width="120" />
        <el-table-column label="默认" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.default" type="success" size="small">当前</el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button v-if="!row.default" link type="primary" size="small">设为默认</el-button>
            <el-button link type="danger" size="small">下线</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>
