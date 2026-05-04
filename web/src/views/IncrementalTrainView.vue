<script setup lang="ts">
import { ref } from 'vue'

const form = ref({
  parentModel: 'v0.2-cls',
  includeCorrections: true,
  newSince: '2026-01-15',
})
</script>

<template>
  <div>
    <p class="view-muted">
      增量训练在父模型基础上合并新增已标注样本与（可选）纠错样本；预处理规则与全量训练一致。
    </p>
    <div class="view-card" style="max-width: 640px">
      <h3 class="view-heading">增量训练向导</h3>
      <el-form :model="form" label-width="120px">
        <el-form-item label="父模型">
          <el-select v-model="form.parentModel" style="width: 100%">
            <el-option label="v0.2-cls (当前线上)" value="v0.2-cls" />
            <el-option label="v0.1-cls" value="v0.1-cls" />
          </el-select>
        </el-form-item>
        <el-form-item label="新样本自">
          <el-date-picker v-model="form.newSince" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="纠错样本">
          <el-switch v-model="form.includeCorrections" active-text="并入训练集" />
        </el-form-item>
        <el-alert title="将统计各 image_kind 数量写入 TrainJob.params" type="info" show-icon :closable="false" style="margin-bottom: 16px" />
        <el-form-item>
          <el-button type="primary">创建增量训练</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>
