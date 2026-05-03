<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Box,
  CircleCheck,
  Cpu,
  EditPen,
  Odometer,
  Picture,
  Setting,
  UploadFilled,
} from '@element-plus/icons-vue'

const route = useRoute()
const currentTitle = computed(() => route.meta.title as string)
</script>

<template>
  <el-container class="layout-root">
    <el-aside width="232px" class="aside">
      <div class="brand">
        <span class="brand-mark">舌</span>
        <div class="brand-text">
          <div class="brand-title">Tongue Diagnosis</div>
          <div class="brand-sub">舌象诊断平台</div>
        </div>
      </div>
      <el-menu
        :router="true"
        :default-active="route.path"
        class="side-menu"
      >
        <el-menu-item index="/">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/upload">
          <el-icon><UploadFilled /></el-icon>
          <span>批量上传</span>
        </el-menu-item>
        <el-menu-item index="/annotate">
          <el-icon><EditPen /></el-icon>
          <span>标注工作台</span>
        </el-menu-item>
        <el-sub-menu index="train-group">
          <template #title>
            <el-icon><Cpu /></el-icon>
            <span>训练</span>
          </template>
          <el-menu-item index="/train">全量训练</el-menu-item>
          <el-menu-item index="/train/incremental">增量训练</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/infer">
          <el-icon><Picture /></el-icon>
          <span>批量推理</span>
        </el-menu-item>
        <el-menu-item index="/review">
          <el-icon><CircleCheck /></el-icon>
          <span>纠错审核</span>
        </el-menu-item>
        <el-menu-item index="/models">
          <el-icon><Box /></el-icon>
          <span>模型管理</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container class="main-wrap">
      <el-header class="header">
        <div class="breadcrumb-area">
          <el-tag type="info" size="small" effect="plain">CPU · Vue 3</el-tag>
          <span class="page-title">{{ currentTitle }}</span>
        </div>
        <div class="header-actions">
          <el-button size="small" type="primary" plain>帮助文档</el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout-root {
  min-height: 100vh;
  background: var(--td-bg);
}

.aside {
  background: linear-gradient(180deg, #0d4f4f 0%, #0a3d3d 100%);
  color: #e8f5f4;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
}

.brand-title {
  font-weight: 600;
  font-size: 14px;
  letter-spacing: 0.02em;
}

.brand-sub {
  font-size: 12px;
  opacity: 0.75;
  margin-top: 2px;
}

.side-menu {
  border-right: none;
  background: transparent;
  --el-menu-text-color: rgba(255, 255, 255, 0.85);
  --el-menu-hover-text-color: #fff;
  --el-menu-hover-bg-color: rgba(255, 255, 255, 0.08);
  --el-menu-active-color: #fff;
  padding: 8px 0;
}

.side-menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.12) !important;
  border-radius: 8px;
  margin: 2px 8px;
  width: auto;
}

.side-menu :deep(.el-menu-item),
.side-menu :deep(.el-sub-menu__title) {
  border-radius: 8px;
  margin: 2px 8px;
  width: auto;
}

.side-menu :deep(.el-sub-menu .el-menu-item) {
  margin-left: 8px;
  padding-left: 40px !important;
}

.main-wrap {
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid var(--td-border);
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.03);
}

.breadcrumb-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--td-text);
}

.main {
  padding: 24px;
  background: var(--td-bg);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
