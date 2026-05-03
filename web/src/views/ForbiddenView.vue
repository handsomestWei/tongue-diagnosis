<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="wrap">
    <el-result icon="warning" title="无权访问" sub-title="您的角色无法打开该页面，请联系管理员。">
      <template #extra>
        <el-button type="primary" @click="router.push('/')">返回首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<style scoped>
.wrap {
  padding: 48px 24px;
}
</style>
