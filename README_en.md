# ComfyUI CatsAPI

[中文](README.md) | English

ComfyUI custom nodes for [CatsAPI / 猫影工坊](https://catsapi.com).

This first version exposes **one public node per supported model**, so each node only shows the parameters that model actually accepts. Shared code handles API auth, task submission, polling, result downloading, and image tensor conversion.

## Example

The image nodes return ComfyUI `IMAGE` tensors, so they can be connected directly to `Preview Image`.

![ComfyUI CatsAPI image example](assets/comfyui-image-example.png)

In the example above:

- `CatsAPI GPT Image 2` uses `size` / `quality`.
- `CatsAPI GrokImage` uses `aspect_ratio`.
- Both nodes can share a prompt from a `Text String` node.
- `api_key_override` is optional and can be left empty for local usage.

## Nodes

### Image Nodes

| Node | Inputs |
|---|---|
| `CatsAPI GPT Image 2` | `prompt`, `size`, `quality`, `num_images`, `max_coins`, optional `reference_image`, optional `api_key_override` |
| `CatsAPI Nano Banana 2` | `prompt`, `resolution`, `aspect_ratio`, `num_images`, `max_coins`, optional `reference_image`, optional `api_key_override` |
| `CatsAPI Nano Banana Pro` | `prompt`, `resolution`, `aspect_ratio`, `num_images`, `max_coins`, optional `reference_image`, optional `api_key_override` |
| `CatsAPI FLUX.2 Pro` | `prompt`, `aspect_ratio`, `max_coins`, optional `reference_image`, optional `api_key_override` |
| `CatsAPI GrokImage` | `prompt`, `aspect_ratio`, `num_images`, `max_coins`, optional `reference_image`, optional `api_key_override` |

Image nodes return:

- `images`: ComfyUI `IMAGE` tensor
- `file_paths`: JSON list of downloaded local files
- `cost_coins`: consumed cat coins
- `task_id`
- `metadata`: JSON object

### Video Nodes

| Node | Inputs |
|---|---|
| `CatsAPI Seedance 2.0` | `prompt`, `resolution`, `duration`, `aspect_ratio`, `max_coins`, optional `start_image`, optional `end_image`, optional `reference_images`, optional `api_key_override` |
| `CatsAPI GrokImageVideo` | `prompt`, `resolution`, `duration`, `aspect_ratio`, `max_coins`, optional `start_image`, optional `api_key_override` |

Video nodes save generated `.mp4` files into ComfyUI's output directory under `catsapi/` and return:

- `video_path`
- `cost_coins`
- `task_id`
- `metadata`

## API Key

There are two supported ways to configure a CatsAPI key.

### Method 1: Global Key For Local ComfyUI

Recommended for your own machine or a private ComfyUI server.

Set an environment variable before starting ComfyUI:

```bash
export CATSAPI_API_KEY=cats-your-key
python main.py
```

If ComfyUI does not inherit shell environment variables, the nodes also statically read:

- this custom node folder's `.env`
- ComfyUI current working directory `.env`
- `~/.catsapi.env`
- `~/.zshrc`
- `~/.bashrc`
- `~/.profile`
- `~/.bash_profile`

Supported config file formats:

```bash
CATSAPI_API_KEY=cats-your-key
export CATSAPI_API_KEY="cats-your-key"
```

Optional custom backend:

```bash
export CATSAPI_BASE=https://catsapi.com
```

### Method 2: Runtime Key Override For Hosted Platforms

Recommended for public or hosted ComfyUI platforms such as RunningHub, where users may not control server environment variables.

Every node has an optional `api_key_override` input:

- Leave it empty for local/private ComfyUI usage.
- Fill it only when the platform cannot provide secrets through environment variables.
- The override is used only for the current node execution.
- The override is never written to `metadata`.
- Truncated keys containing `...` or `…` are rejected before any request is sent.

Important: ComfyUI workflow JSON may save widget values. Do not publish or share workflows with `api_key_override` filled in.

## Spending Guard

`max_coins=0` means no spending cap. Any positive value previews cost first and cancels if the task would exceed it.

## Result Handling

- Image results are downloaded locally and converted into ComfyUI `IMAGE` tensors.
- Video results are downloaded locally and returned as a `video_path`.
- Internal CatsAPI result URLs are not returned as user-facing outputs.
- The downloader uses browser-like headers and a `curl` fallback to avoid CDN bot-check issues where possible.

## Installation

Clone this repository into ComfyUI's `custom_nodes` directory:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/maodeyu180/ComfyUI_Catsapi.git
```

Restart ComfyUI after installation or updates.
