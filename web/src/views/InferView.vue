<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const model = ref('v0.2-cls')
const results = ref([
  { file: 'a_01.jpg', kind: 'full_face_selfie', pred: '淡红舌', conf: 0.91 },
  { file: 'b_02.jpg', kind: 'tongue_closeup', pred: '红舌', conf: 0.72 },
  { file: 'c_03.jpg', kind: 'tongue_closeup', pred: '紫舌', conf: 0.58 },
])
</script>

<template>
  <div>
    <p class="view-muted">推理请求须携带 <code>image_kind</code> 或由 <code>image_id</code> 从库中解析；下方为演示结果。</p>
    <div class="view-card">
      <el-form inline>
        <el-form-item label="模型">
          <el-select v-model="model" style="width: 200px">
            <el-option label="v0.2-cls" value="v0.2-cls" />
            <el-option label="v0.1-cls" value="v0.1-cls" />
          </el-select>
        </el-form-item>
        <el-form-item label="Top-K">
          <el-input-number :model-value="3" :min="1" :max="10" disabled />
        </el-form-item>
        <el-form-item>
          <el-button type="primary">对选中图片推理</el-button>
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
