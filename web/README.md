# 舌象诊断平台 · Web 前端（Vue 3）

依据 `docs/开发计划-舌象诊断系统服务化-Vue-20260426.md` 搭建的 **MVP 界面**：侧栏导航、各功能页演示数据、**登录与 RBAC**（与 FastAPI JWT 对接）。

## 命令

```bash
# 终端 1：仓库根目录
pip install -e ".[api]"
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

# 终端 2
cd web
npm install
npm run dev      # http://localhost:5173 ，/api 代理到 8000
npm run build
npm run preview  # 预览生产构建（同样代理 /api）
```

## 演示账号（后端内存用户，见 `api/config.py`）

| 用户名 | 默认密码 | 角色 | 说明 |
|--------|----------|------|------|
| admin | admin123 | 管理员 | 全功能含模型/设置 |
| annotator | anno123 | 标注员 | 上传、标注、训练、推理；无模型/设置 |
| viewer | view123 | 只读 | 仪表盘、推理、纠错列表；纠错提交按钮禁用 |

生产环境请设置环境变量 `JWT_SECRET_KEY` 并改为 **数据库存储用户**。

## 生成 UI 截图（输出到 `docs/ui-screenshots/`）

需仓库根已安装 `[api]`，脚本会同时启动 **uvicorn** 与 **vite preview**：

```bash
cd web
npm run capture-ui
```

## 技术栈

- Vue 3 + TypeScript + Vite  
- Vue Router 4（全局守卫 + `meta.roles`）、Pinia  
- Element Plus、Axios（Bearer 拦截）  
- Playwright（截图）
