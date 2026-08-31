# ComfyUI CatsAPI 维护说明

本仓库是 CatsAPI 主站的独立 ComfyUI 自定义节点项目，不是主站部署代码，也不是主站 submodule。

## 关联项目

- 主站：`/Users/yu/Developers/github_personal/personal_projects/ldc_gen_image`。
- 本仓库：`/Users/yu/Developers/github_personal/catsapi_relation/ComfyUI_Catsapi`；远端 `git@github.com:maodeyu180/ComfyUI_Catsapi.git`。
- 同级 Agent Skill：`/Users/yu/Developers/github_personal/catsapi_relation/OpenClaw_Catsapi_Skill`。
- 本地联合维护规则见上一层 `AGENTS.md`；涉及主站文件时先阅读主站 `AGENTS.md`。

## 同步入口

- `model_specs.py`：模型支持的枚举值、分辨率、比例、时长和质量选项。
- `nodes.py`：每个模型的节点输入、参数映射、费用上限、参考文件及输出。
- `catsapi_client.py`：鉴权、请求、费用预览、任务提交、轮询与下载。
- `image_utils.py`：ComfyUI 图片 tensor 与上传 / 下载媒体之间的转换。
- `__init__.py`：公开节点映射；已有 class key、输入名和输出顺序会被工作流依赖，不随意重命名或移除。
- `README.md`、`README_en.md`、`assets/`：双语安装 / 使用说明及工作流示例。

模型 schema 对应主站 `backend/app/image_models.json` / `backend/app/abacus_video_models.json`；启用名单和价格以 `backend/update_prices.py` 为准；请求和响应检查主站 `backend/app/schemas.py`、`backend/app/routers/tasks.py` 及 `backend/app/main.py` 中的 `/api/models`。执行限制还要核对 `backend/app/services/task_worker.py`：当前 Seedance schema 写 9 张参考图，但 worker 合并后最多保留 4 张，客户端按 4 张总上限处理。Skill 是同级消费者，不是 schema 权威来源。

保留“一个模型一个公开节点”的设计。主站新增模型不自动意味着节点支持；扩展时同时检查输入 schema、参考文件、默认值、参数校验、节点注册和双语文档。

## 开发与验证

- 不全局安装依赖，不为静态校验安装完整 ComfyUI。优先使用项目内环境；标准库语法 / mock 检查可显式借用现有主站 `backend/venv/bin/python`，但不要向主站环境添加依赖。
- 修改后至少做 Python 语法检查；参数变化需离线对比主站 schema，检查默认值属于合法选项。
- 节点行为变更应 mock API，验证请求参数、费用超限、失败 / 超时、下载结果和节点映射兼容性；依赖不可用时明确说明没有做真实 ComfyUI UI 验证。
- 现有 `max_coins` 提交前保护、全局 Key 与 `api_key_override` 优先级、图片 tensor / 视频路径输出契约必须保留。
- 不把 Key 放入 metadata、日志或示例工作流；提醒用户 workflow JSON 可能保存 `api_key_override`。
- 默认不调用生产生成接口、不消耗猫币、不自动重启 ComfyUI。未经用户明确要求，不 commit、push、发布或操作主站生产环境。
