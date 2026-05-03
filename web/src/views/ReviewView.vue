<script setup lang="ts">
const rows = [
  { pred: '淡红舌', truth: '红舌', conf: 0.52, include: true },
  { pred: '紫舌', truth: '紫舌', conf: 0.88, include: false },
]
</script>

<template>
  <div>
    <p class="view-muted">筛选低置信度或与人工不一致的预测，提交纠正并可选纳入下一次训练。</p>
    <div class="view-card">
      <el-form inline>
        <el-form-item label="置信度 &lt; ">
          <el-input-number :model-value="0.6" :step="0.05" :max="1" disabled />
        </el-form-item>
        <el-form-item>
          <el-button type="primary">筛选</el-button>
        </el-form-item>
      </el-form>
      <el-table :data="rows" stripe style="margin-top: 12px">
        <el-table-column prop="pred" label="模型预测" />
        <el-table-column prop="truth" label="纠正为" />
        <el-table-column prop="conf" label="置信度" />
        <el-table-column label="加入再训练">
          <template #default="{ row }">
            <el-checkbox :model-value="row.include" disabled />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default>
            <el-button type="primary" size="small">提交纠正</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>
