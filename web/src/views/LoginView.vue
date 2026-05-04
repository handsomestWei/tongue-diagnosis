<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const username = ref('')
const password = ref('')

async function onSubmit() {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  try {
    await auth.login(username.value, password.value)
    const redir = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redir || '/')
    ElMessage.success('登录成功')
  } catch {
    ElMessage.error('用户名或密码错误')
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="title">舌象诊断平台</h1>
      <p class="subtitle">账号登录 · 角色权限由后端 JWT 校验</p>
      <el-form @submit.prevent="onSubmit" label-position="top" class="form">
        <el-form-item label="用户名">
          <el-input v-model="username" autocomplete="username" placeholder="admin / annotator / viewer" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" autocomplete="current-password" show-password />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="auth.loading" style="width: 100%">
          登录
        </el-button>
      </el-form>
      <el-collapse class="hint">
        <el-collapse-item title="演示账号（默认口令见 web README）" name="1">
          <ul class="accounts">
            <li><strong>admin</strong> — 管理员（全功能）</li>
            <li><strong>annotator</strong> — 上传/标注/训练/推理</li>
            <li><strong>viewer</strong> — 仅查看仪表盘、推理与纠错列表（无提交）</li>
          </ul>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #0d4f4f 0%, #1a3d3d 45%, #f0f5f5 45%);
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 16px;
  padding: 32px 28px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.12);
}

.title {
  margin: 0 0 8px;
  font-size: 22px;
  color: var(--td-text);
}

.subtitle {
  margin: 0 0 24px;
  font-size: 13px;
  color: var(--td-muted);
}

.form {
  margin-bottom: 16px;
}

.hint {
  margin-top: 8px;
  border: none;
}

.accounts {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: var(--td-muted);
  line-height: 1.7;
}
</style>
