# 舌象诊断平台 · Web 前端（Vue 3）

依据 `docs/开发计划-舌象诊断系统服务化-Vue-20260426.md` 搭建的 **MVP 界面骨架**：侧栏导航、各功能页静态演示数据；后端 API 对接可在后续里程碑接入。

## 命令

```bash
cd web
npm install
npm run dev      # 开发：http://localhost:5173
npm run build
npm run preview  # 预览生产构建
```

## 生成 UI 截图（输出到仓库 `docs/ui-screenshots/`）

```bash
cd web
npm run capture-ui
```

依赖 Playwright（已列入 `devDependencies`）；首次会自动下载 Chromium。

## 技术栈

- Vue 3 + TypeScript + Vite  
- Vue Router 4、Pinia  
- Element Plus + `@element-plus/icons-vue`
