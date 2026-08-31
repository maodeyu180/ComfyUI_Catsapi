# ComfyUI CatsAPI

[中文](README.md) | English

ComfyUI custom nodes for [CatsAPI / 猫影工坊](https://catsapi.com).

This version exposes **one public node per supported model**, so each node only shows the parameters that model actually accepts. Shared code handles API auth, task submission, polling, result downloading, and image tensor conversion.

## Example

The image nodes return ComfyUI `IMAGE` tensors, so they can be connected directly to `Preview Image`.

![ComfyUI CatsAPI image example](assets/comfyui-image-example.png)

In the example above:

- `CatsAPI GPT Image 2` uses `size` / `quality`.
- `CatsAPI GrokImage` uses `aspect_ratio`.
- Both nodes can share a prompt from a `Text String` node.
- `api_key_override` is optional and can be left empty for local usage.

## Nodes

There are 8 image nodes and 4 video nodes. Existing node keys and output contracts are preserved.

### Image Nodes

| Node | Inputs |
|---|---|
| `CatsAPI GPT Image 2` | `prompt`, `size`, `quality`, `num_images`, `max_coins`, optional `reference_image`, optional `api_key_override` |
| `CatsAPI Nano Banana 2` | `prompt`, `resolution`, `aspect_ratio`, `num_images`, `max_coins`, optional `reference_image`, optional `api_key_override`, optional `enable_web_search` |
| `CatsAPI Nano Banana Pro` | `prompt`, `resolution`, `aspect_ratio`, `num_images`, `max_coins`, optional `reference_image`, optional `api_key_override`, optional `enable_web_search` |
| `CatsAPI FLUX.2 Pro` | `prompt`, `aspect_ratio`, `max_coins`, optional `reference_image`, optional `api_key_override` |
| `CatsAPI GrokImage` | `prompt`, `aspect_ratio`, `num_images`, `max_coins`, optional `reference_image`, optional `api_key_override` |
| `CatsAPI Seedream 5 Lite` | `prompt`, `image_size`, `num_images`, `max_coins`, optional `reference_image`, optional `seed`, optional `api_key_override` |
| `CatsAPI Seedream 5 Pro` | `prompt`, `image_size`, `num_images`, `max_coins`, optional `reference_image`, optional `seed`, optional `api_key_override` |
| `CatsAPI Grok Imagine Image 2` | `prompt`, `aspect_ratio`, `num_images`, `max_coins`, optional `reference_image`, optional `api_key_override` |

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
| `CatsAPI Seedance 2.0 Mini` | `prompt`, `resolution`, `duration`, `aspect_ratio`, `max_coins`, optional `start_image`, optional `end_image`, optional `reference_images`, optional `api_key_override` |
| `CatsAPI Gemini Omni Flash` | `prompt`, `duration`, `aspect_ratio`, `max_coins`, optional `start_image`, optional `api_key_override` |

Video nodes save generated `.mp4` files into ComfyUI's output directory under `catsapi/` and return:

- `video_path`
- `cost_coins`
- `task_id`
- `metadata`

## Current Parameters and Compatibility

- GPT Image 2 offers 20 sizes and up to 16 reference images; Nano Banana 2 accepts 14, Nano Banana Pro 4, FLUX.2 Pro 3, and GrokImage 1. Oversized reference batches raise an error instead of being silently truncated.
- Nano Banana 2 / Pro have an optional `enable_web_search` input, enabled by default. Existing workflows still run without this input. Both models default to `1K`.
- Seedream 5 Lite / Pro use `image_size` (API field `imageSize`), defaulting to `square`, with portrait/landscape 4:3 and 16:9 options and up to 4 references. `seed=-1` omits the seed; non-negative values are forwarded. There are no independent resolution or quality controls.
- Grok Imagine Image 2 is a separate new node, with 1–4 output images, one reference image, and a default aspect ratio of `1:1`.
- Seedance 2.0 / Mini default to `480p` / 8 seconds and always use `inputMode=reference`. 2.0 uses `mode=fast`; Mini sends no `mode`. Grok video defaults to `720p` / 8 seconds. Valid settings explicitly saved in existing workflows remain usable.
- Both Seedance models preserve `start_image`, `end_image`, and `reference_images`, merging them as start → references → end. These act as references and do not guarantee strict first/last-frame control.
- Both Seedance models accept at most 4 images in total. The main-site schema lists 9, but its worker still keeps only 4, so the nodes enforce the effective limit. Video/audio reference inputs are not exposed by these nodes.
- Gemini Omni Flash supports 5–10 seconds and 16:9 / 9:16, defaulting to 5 seconds / 16:9, with an optional single start image. It neither exposes nor sends `resolution` / `mode`.

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

Every submission checks a cost preview and balance; malformed previews block submission. `max_coins=0` means no spending cap, while a positive value blocks tasks exceeding the cap. This is a pre-submit check, not an atomic server-side price lock.

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

## Offline Validation

Run `python -m unittest discover -s tests -v` in a project Python environment. Tests use the standard library and mocked media / APIs, without a full ComfyUI installation or paid requests. They do not replace live ComfyUI UI and tensor integration checks.

## Related Projects

- [CatsAPI main site](https://catsapi.com)
- [CatsAPI Agent Skill](https://github.com/maodeyu180/CatsAPI-Agent-Skill)
