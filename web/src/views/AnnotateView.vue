<script setup lang="ts">
import { ref } from 'vue'

const rows = ref([
  {
    id: 'img-001',
    thumb: '',
    kind: 'full_face_selfie' as const,
    cls: '淡红舌',
    sam: true,
  },
  {
    id: 'img-002',
    kind: 'tongue_closeup' as const,
    cls: '未标注',
    sam: false,
  },
])

const classes = ['淡红舌', '红舌', '淡白舌', '紫舌']
const selectedKind = ref<string>('full_face_selfie')
</script>

<template>
  <div>
    <p class="view-muted">
      可在此更正「输入类型」与分类标签；全脸图可勾选「显示 ROI 预览」（对接 SAM 后生效）。
    </p>
    <el-row :gutter="16">
      <el-col :xs="24" :md="10">
        <div class="view-card">
          <h3 class="view-heading">当前图片</h3>
          <div class="ph-thumb">
            <span>缩略图占位</span>
            <small>{{ rows[0].id }}</small>
          </div>
          <el-form label-position="top" class="mini-form">
            <el-form-item label="image_kind">
              <el-select v-model="selectedKind" style="width: 100%">
                <el-option label="full_face_selfie（全脸）" value="full_face_selfie" />
                <el-option label="tongue_closeup（特写）" value="tongue_closeup" />
              </el-select>
            </el-form-item>
            <el-form-item label="分类标签">
              <el-select placeholder="选择舌象类别" style="width: 100%">
                <el-option v-for="c in classes" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
            <el-button type="primary">保存并下一张</el-button>
            <el-button>跳过</el-button>
          </el-form>
        </div>
      </el-col>
      <el-col :xs="24" :md="14">
        <div class="view-card">
          <h3 class="view-heading">待标注队列</h3>
          <el-table :data="rows" size="small" stripe>
            <el-table-column prop="id" label="ID" width="100" />
            <el-table-column label="类型" width="160">
              <template #default="{ row }">
                <el-tag v-if="row.kind === 'full_face_selfie'" type="warning" size="small"
                  >全脸</el-tag
                >
                <el-tag v-else type="success" size="small">特写</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="SAM">
              <template #default="{ row }">
                {{ row.sam ? '是' : '否' }}
              </template>
            </el-table-column>
            <el-table-column prop="cls" label="当前标签" />
            <el-table-column label="操作" width="100">
              <template #default>
                <el-button link type="primary" size="small">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.ph-thumb {
  height: 200px;
  border-radius: 10px;
  background: linear-gradient(135deg, #e0f0f0 0%, #c8e0e0 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--td-muted);
  margin-bottom: 16px;
}
.ph-thumb small {
  margin-top: 8px;
  opacity: 0.8;
}
.mini-form {
  max-width: 100%;
}
</style>
