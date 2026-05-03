<script setup lang="ts">
import { ref } from 'vue'

const form = ref({
  dataVersion: 'v20260201-default',
  model: 'yolov8n-cls.pt',
  epochs: 80,
  imgsz: 224,
  batch: 8,
})

const jobs = ref([
  {
    id: 'train-01',
    status: 'running',
    progress: 62,
    kindMix: '全脸 320 / 特写 410',
  },
  {
    id: 'train-00',
    status: 'success',
    progress: 100,
    kindMix: '全脸 300 / 特写 350',
  },
])
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
              <el-button type="primary">提交训练任务</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
      <el-col :xs="24" :lg="14">
        <div class="view-card">
          <h3 class="view-heading">任务列表</h3>
          <el-table :data="jobs" stripe>
            <el-table-column prop="id" label="任务 ID" width="120" />
            <el-table-column prop="kindMix" label="样本构成" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'running'" type="warning">训练中</el-tag>
                <el-tag v-else type="success">完成</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="进度" width="200">
              <template #default="{ row }">
                <el-progress :percentage="row.progress" :status="row.status === 'success' ? 'success' : undefined" />
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="view-card">
          <h3 class="view-heading">日志（演示）</h3>
          <pre class="log-box">Epoch 48/80 · train loss 0.42 · device cpu
Validating · top1 0.81 · top5 0.96</pre>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.log-box {
  margin: 0;
  background: #0d1117;
  color: #7ee787;
  padding: 14px;
  border-radius: 8px;
  font-size: 12px;
  overflow-x: auto;
}
</style>
