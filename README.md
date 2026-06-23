# ComfyUI CatsAPI

中文 | [English](README_en.md)

适用于 [CatsAPI / 猫影工坊](https://catsapi.com) 的 ComfyUI 自定义节点。

当前版本采用 **一个模型一个公开节点** 的设计，所以每个节点只显示该模型真实支持的参数，避免把 `size`、`resolution`、`quality` 等不同模型参数混在一起。底层共享同一套 API 鉴权、任务提交、轮询、结果下载和图片 tensor 转换逻辑。

## 示例

图片节点会返回 ComfyUI 的 `IMAGE` tensor，可以直接连接到 `Preview Image`。

![ComfyUI CatsAPI 图片示例](assets/comfyui-image-example.png)

上图示例中：

- `CatsAPI GPT Image 2` 使用 `size` / `quality`。
- `CatsAPI GrokImage` 使用 `aspect_ratio`。
- 两个节点可以共用一个 `Text String` 文本提示词节点。
- `api_key_override` 是可选输入，本地使用时通常留空。

## 节点列表

### 图片节点

| 节点 | 输入 |
|---|---|
| `CatsAPI GPT Image 2` | `prompt`、`size`、`quality`、`num_images`、`max_coins`、可选 `reference_image`、可选 `api_key_override` |
| `CatsAPI Nano Banana 2` | `prompt`、`resolution`、`aspect_ratio`、`num_images`、`max_coins`、可选 `reference_image`、可选 `api_key_override` |
| `CatsAPI Nano Banana Pro` | `prompt`、`resolution`、`aspect_ratio`、`num_images`、`max_coins`、可选 `reference_image`、可选 `api_key_override` |
| `CatsAPI FLUX.2 Pro` | `prompt`、`aspect_ratio`、`max_coins`、可选 `reference_image`、可选 `api_key_override` |
| `CatsAPI GrokImage` | `prompt`、`aspect_ratio`、`num_images`、`max_coins`、可选 `reference_image`、可选 `api_key_override` |

图片节点输出：

- `images`：ComfyUI `IMAGE` tensor
- `file_paths`：本地下载文件路径 JSON 列表
- `cost_coins`：本次消耗猫币
- `task_id`
- `metadata`：JSON 元信息

### 视频节点

| 节点 | 输入 |
|---|---|
| `CatsAPI Seedance 2.0` | `prompt`、`resolution`、`duration`、`aspect_ratio`、`max_coins`、可选 `start_image`、可选 `end_image`、可选 `reference_images`、可选 `api_key_override` |
| `CatsAPI GrokImageVideo` | `prompt`、`resolution`、`duration`、`aspect_ratio`、`max_coins`、可选 `start_image`、可选 `api_key_override` |

视频节点会把生成的 `.mp4` 保存到 ComfyUI 输出目录的 `catsapi/` 子目录，并返回：

- `video_path`
- `cost_coins`
- `task_id`
- `metadata`

## API Key 配置

支持两种配置方式。

### 方式一：本地 / 私有 ComfyUI 使用全局 Key

适合自己的电脑或私有 ComfyUI 服务器。

启动 ComfyUI 前设置环境变量：

```bash
export CATSAPI_API_KEY=cats-your-key
python main.py
```

如果 ComfyUI 没有继承 shell 环境变量，节点还会静态读取：

- 本自定义节点目录下的 `.env`
- ComfyUI 启动目录下的 `.env`
- `~/.catsapi.env`
- `~/.zshrc`
- `~/.bashrc`
- `~/.profile`
- `~/.bash_profile`

配置文件支持下面两种写法：

```bash
CATSAPI_API_KEY=cats-your-key
export CATSAPI_API_KEY="cats-your-key"
```

可选自建后端：

```bash
export CATSAPI_BASE=https://catsapi.com
```

### 方式二：RunningHub 等公共平台使用运行时覆盖

适合 RunningHub 这类用户无法控制服务器环境变量的公共 / 托管 ComfyUI 平台。

每个节点都有可选输入 `api_key_override`：

- 本地或私有 ComfyUI 使用时留空即可。
- 只有平台无法通过环境变量提供密钥时才填写。
- 该值只用于当前节点执行。
- 该值不会写入 `metadata`。
- 包含 `...` 或 `…` 的截断 Key 会在发请求前被拒绝。

注意：ComfyUI workflow JSON 可能保存 widget 值。不要发布或分享填了 `api_key_override` 的工作流。

## 花费保护

`max_coins=0` 表示不限制花费。设置为正数时，节点会先预估花费；如果超过上限，会取消提交任务。

## 结果处理

- 图片结果会先下载到本地，再转换为 ComfyUI `IMAGE` tensor。
- 视频结果会下载到本地，并以 `video_path` 返回。
- 不把 CatsAPI 内部结果 URL 作为用户可见输出。
- 下载器使用浏览器类 headers，并带 `curl` fallback，尽量避开 CDN 机器人检测导致的下载失败。

## 安装

克隆到 ComfyUI 的 `custom_nodes` 目录：

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/maodeyu180/ComfyUI_Catsapi.git
```

安装或更新后重启 ComfyUI。
