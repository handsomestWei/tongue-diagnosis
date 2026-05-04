<script setup lang="ts">
import { ref } from 'vue'

const dbUrl = ref('sqlite:///./data/app.db')
const storage = ref('/workspace/storage')
const threads = ref(4)
</script>

<template>
  <div>
    <p class="view-muted">开发与生产通过环境变量切换；此处为表单示意。</p>
    <div class="view-card" style="max-width: 720px">
      <h3 class="view-heading">环境与存储</h3>
      <el-form label-width="140px">
        <el-form-item label="DATABASE_URL">
          <el-input v-model="dbUrl" />
        </el-form-item>
        <el-form-item label="STORAGE_ROOT">
          <el-input v-model="storage" />
        </el-form-item>
        <el-form-item label="TORCH_NUM_THREADS">
          <el-input-number v-model="threads" :min="1" :max="32" />
        </el-form-item>
        <el-form-item label="CORS（开发）">
          <el-input placeholder="http://localhost:5173" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary">保存（演示）</el-button>
        </el-form-item>
      </el-form>
    </div>
    <div class="view-card" style="max-width: 720px">
      <h3 class="view-heading">API 访问</h3>
      <p class="view-muted">内测可使用 <code>X-API-Key</code>；生产请改用 JWT 或网关鉴权。</p>
      <el-input type="password" show-password placeholder="••••••••" />
    </div>
  </div>
</template>
