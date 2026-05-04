<script setup lang="ts">
const projects = [
  { name: '默认项目', images: 1280, labeled: 76, jobs: 3 },
]
const stats = [
  { label: '已上传图片', value: '1,280', hint: '含全脸 / 特写' },
  { label: '已标注比例', value: '76%', hint: '按 class 计数' },
  { label: '训练中任务', value: '1', hint: 'CPU 队列' },
  { label: '当前默认模型', value: 'v0.2-cls', hint: 'YOLO classify' },
]
</script>

<template>
  <div>
    <p class="view-muted">
      平台支持两种输入：<el-tag size="small" type="warning">全脸自拍</el-tag> 将经 TongueSAM
      抠舌；<el-tag size="small" type="success">舌部特写</el-tag> 跳过 SAM，直接进入分类管线。
    </p>
    <el-row :gutter="16">
      <el-col v-for="s in stats" :key="s.label" :xs="24" :sm="12" :md="6">
        <div class="view-card stat-card">
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-hint">{{ s.hint }}</div>
        </div>
      </el-col>
    </el-row>
    <div class="view-card">
      <h3 class="view-heading">项目概览</h3>
      <el-table :data="projects" stripe>
        <el-table-column prop="name" label="项目" />
        <el-table-column prop="images" label="图片数" />
        <el-table-column prop="labeled" label="已标注 %" />
        <el-table-column prop="jobs" label="活跃任务" />
        <el-table-column label="操作" width="160">
          <template #default>
            <el-button link type="primary" size="small">进入</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="view-card">
      <h3 class="view-heading">最近活动（演示数据）</h3>
      <el-timeline>
        <el-timeline-item timestamp="今天 09:12" type="primary">
          训练任务 <code>train-20260201-a</code> 已完成，模型已注册
        </el-timeline-item>
        <el-timeline-item timestamp="昨天 18:40" type="success">
          批量上传 120 张，含 40 张全脸、80 张特写
        </el-timeline-item>
        <el-timeline-item timestamp="昨天 11:05">
          纠错审核：12 条已并入增量训练候选集
        </el-timeline-item>
      </el-timeline>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  min-height: 108px;
}
.stat-label {
  font-size: 13px;
  color: var(--td-muted);
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--td-accent);
  margin: 8px 0 4px;
}
.stat-hint {
  font-size: 12px;
  color: var(--td-muted);
}
</style>
