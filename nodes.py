from __future__ import annotations

import json
import time
from pathlib import Path

from .catsapi_client import (
    CatsAPIError,
    default_output_dir,
    download_file,
    poll_task,
    preview_cost,
    submit_task,
)
from .image_utils import image_paths_to_tensor, tensor_to_image_inputs
from .model_specs import (
    FLUX2_PRO_ASPECT_RATIOS,
    GPT2_QUALITY,
    GROK_IMAGE_ASPECT_RATIOS,
    GROK_VIDEO_ASPECT_RATIOS,
    GROK_VIDEO_DURATIONS,
    IMAGE_RESOLUTIONS_NANO2,
    IMAGE_RESOLUTIONS_NANO_PRO,
    IMAGE_SIZES_GPT2,
    NANO_BANANA2_ASPECT_RATIOS,
    NANO_BANANA_PRO_ASPECT_RATIOS,
    SEEDANCE20_ASPECT_RATIOS,
    SEEDANCE20_DURATIONS,
    VIDEO_RESOLUTIONS,
)


CATEGORY_IMAGE = "CatsAPI/Image"
CATEGORY_VIDEO = "CatsAPI/Video"


def _prompt_input(default: str = ""):
    return ("STRING", {"multiline": True, "default": default})


def _max_coins_input():
    return ("INT", {"default": 0, "min": 0, "max": 100000, "step": 1})


def _api_key_override_input():
    return ("STRING", {"default": "", "multiline": False})


def _metadata(task: dict, paths: list[Path], model: str, params: dict) -> tuple[int, str, str]:
    cost = int(task.get("cost") or 0)
    task_id = str(task.get("id") or "")
    data = {
        "task_id": task_id,
        "model": model,
        "cost": cost,
        "params": params,
        "paths": [str(path) for path in paths],
    }
    return cost, task_id, json.dumps(data, ensure_ascii=False)


def _check_max_coins(cost_data: dict, max_coins: int) -> None:
    total = int(cost_data.get("total_cost") or 0)
    if max_coins and total > max_coins:
        raise CatsAPIError(f"费用预览为 {total} 猫币,超过 max_coins={max_coins},已取消提交。")
    if cost_data.get("sufficient") is False:
        balance = int(cost_data.get("balance") or 0)
        raise CatsAPIError(f"猫币余额不足: 预计需要 {total} 猫币,当前余额 {balance} 猫币。")


def _output_path(model: str, ext: str) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return default_output_dir() / f"{model}_{stamp}_{int(time.time() * 1000) % 1000:03d}.{ext}"


def _result_image_urls(detail: dict) -> list[str]:
    urls: list[str] = []
    for item in detail.get("result_images") or []:
        if isinstance(item, dict):
            url = item.get("url")
        else:
            url = item
        if url:
            urls.append(url)
    return urls


def _result_video_url(detail: dict) -> str:
    video = detail.get("result_video") or {}
    return video.get("url") or video.get("videoUrl") or video.get("video_url") or ""


def _generate_image(
    *,
    model: str,
    prompt: str,
    params: dict,
    num_images: int,
    max_coins: int,
    reference_image=None,
    max_reference_images: int = 0,
    cost_resolution: str | None = None,
    cost_mode: str | None = None,
    api_key_override: str = "",
):
    images = tensor_to_image_inputs(
        reference_image,
        max_images=max_reference_images,
        name_prefix=f"{model}_reference",
    ) if reference_image is not None and max_reference_images else []
    cost_data = preview_cost(
        model=model,
        task_type="image",
        num_images=num_images,
        has_image_input=bool(images),
        resolution=cost_resolution,
        mode=cost_mode,
        rewrite_prompt=bool(params.get("rewritePrompt")),
        api_key_override=api_key_override,
    )
    _check_max_coins(cost_data, max_coins)

    task = submit_task(
        model=model,
        task_type="image",
        prompt=prompt,
        params=params,
        num_images=num_images,
        images=images,
        api_key_override=api_key_override,
    )
    task_id = task.get("id")
    if not task_id:
        raise CatsAPIError(f"任务提交失败: {task}")
    detail = poll_task(str(task_id), api_key_override=api_key_override)
    urls = _result_image_urls(detail)
    if not urls:
        raise CatsAPIError("图片任务完成但未返回图片 URL。")

    paths: list[Path] = []
    base = _output_path(model, "png")
    for idx, url in enumerate(urls):
        target = base if len(urls) == 1 else base.with_name(f"{base.stem}_{idx + 1}{base.suffix}")
        paths.append(download_file(url, target))
    image_tensor = image_paths_to_tensor(paths)
    cost, task_id_text, metadata = _metadata(detail, paths, model, params)
    return image_tensor, json.dumps([str(path) for path in paths], ensure_ascii=False), cost, task_id_text, metadata


def _generate_video(
    *,
    model: str,
    prompt: str,
    params: dict,
    max_coins: int,
    start_image=None,
    end_image=None,
    reference_images=None,
    cost_resolution: str | None = None,
    cost_duration: str | None = None,
    cost_mode: str | None = None,
    api_key_override: str = "",
):
    files: dict = {}
    start_inputs = tensor_to_image_inputs(start_image, max_images=1, name_prefix=f"{model}_start")
    if start_inputs:
        files["startFrame"] = start_inputs[0]
    end_inputs = tensor_to_image_inputs(end_image, max_images=1, name_prefix=f"{model}_end")
    if end_inputs:
        files["endFrame"] = end_inputs[0]
    reference_inputs = tensor_to_image_inputs(
        reference_images,
        max_images=4,
        name_prefix=f"{model}_reference",
    )
    if reference_inputs:
        files["referenceImages"] = reference_inputs

    cost_data = preview_cost(
        model=model,
        task_type="video",
        num_images=1,
        has_image_input=bool(files),
        resolution=cost_resolution,
        duration=cost_duration,
        mode=cost_mode,
        rewrite_prompt=bool(params.get("rewritePrompt")),
        api_key_override=api_key_override,
    )
    _check_max_coins(cost_data, max_coins)

    task = submit_task(
        model=model,
        task_type="video",
        prompt=prompt,
        params=params,
        num_images=1,
        files=files or None,
        api_key_override=api_key_override,
    )
    task_id = task.get("id")
    if not task_id:
        raise CatsAPIError(f"任务提交失败: {task}")
    detail = poll_task(str(task_id), api_key_override=api_key_override)
    url = _result_video_url(detail)
    if not url:
        raise CatsAPIError("视频任务完成但未返回视频 URL。")
    path = download_file(url, _output_path(model, "mp4"))
    cost, task_id_text, metadata = _metadata(detail, [path], model, params)
    return str(path), cost, task_id_text, metadata


class CatsAPIGPTImage2:
    CATEGORY = CATEGORY_IMAGE
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = ("images", "file_paths", "cost_coins", "task_id", "metadata")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": _prompt_input(),
                "size": (IMAGE_SIZES_GPT2, {"default": "1024x1024"}),
                "quality": (GPT2_QUALITY, {"default": "auto"}),
                "num_images": ("INT", {"default": 1, "min": 1, "max": 4, "step": 1}),
                "max_coins": _max_coins_input(),
            },
            "optional": {
                "reference_image": ("IMAGE",),
                "api_key_override": _api_key_override_input(),
            },
        }

    def generate(
        self,
        prompt,
        size,
        quality,
        num_images,
        max_coins,
        reference_image=None,
        api_key_override="",
    ):
        params = {"size": size, "quality": quality, "rewritePrompt": False}
        return _generate_image(
            model="gptImage2",
            prompt=prompt,
            params=params,
            num_images=num_images,
            max_coins=max_coins,
            reference_image=reference_image,
            max_reference_images=4,
            cost_resolution=size,
            cost_mode=quality,
            api_key_override=api_key_override,
        )


class CatsAPINanoBanana2:
    CATEGORY = CATEGORY_IMAGE
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = ("images", "file_paths", "cost_coins", "task_id", "metadata")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": _prompt_input(),
                "resolution": (IMAGE_RESOLUTIONS_NANO2, {"default": "1K"}),
                "aspect_ratio": (NANO_BANANA2_ASPECT_RATIOS, {"default": "1:1"}),
                "num_images": ("INT", {"default": 1, "min": 1, "max": 4, "step": 1}),
                "max_coins": _max_coins_input(),
            },
            "optional": {
                "reference_image": ("IMAGE",),
                "api_key_override": _api_key_override_input(),
            },
        }

    def generate(
        self,
        prompt,
        resolution,
        aspect_ratio,
        num_images,
        max_coins,
        reference_image=None,
        api_key_override="",
    ):
        params = {"resolution": resolution, "aspectRatio": aspect_ratio, "rewritePrompt": False}
        return _generate_image(
            model="nanoBanana2",
            prompt=prompt,
            params=params,
            num_images=num_images,
            max_coins=max_coins,
            reference_image=reference_image,
            max_reference_images=4,
            cost_resolution=resolution,
            api_key_override=api_key_override,
        )


class CatsAPINanoBananaPro:
    CATEGORY = CATEGORY_IMAGE
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = ("images", "file_paths", "cost_coins", "task_id", "metadata")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": _prompt_input(),
                "resolution": (IMAGE_RESOLUTIONS_NANO_PRO, {"default": "2K"}),
                "aspect_ratio": (NANO_BANANA_PRO_ASPECT_RATIOS, {"default": "1:1"}),
                "num_images": ("INT", {"default": 1, "min": 1, "max": 4, "step": 1}),
                "max_coins": _max_coins_input(),
            },
            "optional": {
                "reference_image": ("IMAGE",),
                "api_key_override": _api_key_override_input(),
            },
        }

    def generate(
        self,
        prompt,
        resolution,
        aspect_ratio,
        num_images,
        max_coins,
        reference_image=None,
        api_key_override="",
    ):
        params = {"resolution": resolution, "aspectRatio": aspect_ratio, "rewritePrompt": False}
        return _generate_image(
            model="nanoBananaPro",
            prompt=prompt,
            params=params,
            num_images=num_images,
            max_coins=max_coins,
            reference_image=reference_image,
            max_reference_images=4,
            cost_resolution=resolution,
            api_key_override=api_key_override,
        )


class CatsAPIFLUX2Pro:
    CATEGORY = CATEGORY_IMAGE
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = ("images", "file_paths", "cost_coins", "task_id", "metadata")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": _prompt_input(),
                "aspect_ratio": (FLUX2_PRO_ASPECT_RATIOS, {"default": "square"}),
                "max_coins": _max_coins_input(),
            },
            "optional": {
                "reference_image": ("IMAGE",),
                "api_key_override": _api_key_override_input(),
            },
        }

    def generate(self, prompt, aspect_ratio, max_coins, reference_image=None, api_key_override=""):
        params = {"aspectRatio": aspect_ratio, "rewritePrompt": False}
        return _generate_image(
            model="flux2Pro",
            prompt=prompt,
            params=params,
            num_images=1,
            max_coins=max_coins,
            reference_image=reference_image,
            max_reference_images=3,
            api_key_override=api_key_override,
        )


class CatsAPIGrokImage:
    CATEGORY = CATEGORY_IMAGE
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = ("images", "file_paths", "cost_coins", "task_id", "metadata")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": _prompt_input(),
                "aspect_ratio": (GROK_IMAGE_ASPECT_RATIOS, {"default": "1:1"}),
                "num_images": ("INT", {"default": 1, "min": 1, "max": 4, "step": 1}),
                "max_coins": _max_coins_input(),
            },
            "optional": {
                "reference_image": ("IMAGE",),
                "api_key_override": _api_key_override_input(),
            },
        }

    def generate(
        self,
        prompt,
        aspect_ratio,
        num_images,
        max_coins,
        reference_image=None,
        api_key_override="",
    ):
        params = {"aspectRatio": aspect_ratio, "rewritePrompt": False}
        return _generate_image(
            model="grokImagineImage",
            prompt=prompt,
            params=params,
            num_images=num_images,
            max_coins=max_coins,
            reference_image=reference_image,
            max_reference_images=1,
            api_key_override=api_key_override,
        )


class CatsAPISeedance20:
    CATEGORY = CATEGORY_VIDEO
    FUNCTION = "generate"
    RETURN_TYPES = ("STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = ("video_path", "cost_coins", "task_id", "metadata")
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": _prompt_input(),
                "resolution": (VIDEO_RESOLUTIONS, {"default": "720p"}),
                "duration": (SEEDANCE20_DURATIONS, {"default": "5"}),
                "aspect_ratio": (SEEDANCE20_ASPECT_RATIOS, {"default": "16:9"}),
                "max_coins": _max_coins_input(),
            },
            "optional": {
                "start_image": ("IMAGE",),
                "end_image": ("IMAGE",),
                "reference_images": ("IMAGE",),
                "api_key_override": _api_key_override_input(),
            },
        }

    def generate(
        self,
        prompt,
        resolution,
        duration,
        aspect_ratio,
        max_coins,
        start_image=None,
        end_image=None,
        reference_images=None,
        api_key_override="",
    ):
        params = {
            "inputMode": "standard",
            "resolution": resolution,
            "duration": duration,
            "aspectRatio": aspect_ratio,
            "mode": "fast",
            "rewritePrompt": False,
        }
        return _generate_video(
            model="seedance20",
            prompt=prompt,
            params=params,
            max_coins=max_coins,
            start_image=start_image,
            end_image=end_image,
            reference_images=reference_images,
            cost_resolution=resolution,
            cost_duration=duration,
            cost_mode="fast",
            api_key_override=api_key_override,
        )


class CatsAPIGrokImageVideo:
    CATEGORY = CATEGORY_VIDEO
    FUNCTION = "generate"
    RETURN_TYPES = ("STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = ("video_path", "cost_coins", "task_id", "metadata")
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": _prompt_input(),
                "resolution": (VIDEO_RESOLUTIONS, {"default": "480p"}),
                "duration": (GROK_VIDEO_DURATIONS, {"default": "5"}),
                "aspect_ratio": (GROK_VIDEO_ASPECT_RATIOS, {"default": "1:1"}),
                "max_coins": _max_coins_input(),
            },
            "optional": {
                "start_image": ("IMAGE",),
                "api_key_override": _api_key_override_input(),
            },
        }

    def generate(
        self,
        prompt,
        resolution,
        duration,
        aspect_ratio,
        max_coins,
        start_image=None,
        api_key_override="",
    ):
        params = {
            "resolution": resolution,
            "duration": duration,
            "aspectRatio": aspect_ratio,
            "rewritePrompt": False,
        }
        return _generate_video(
            model="grokImagineVideo",
            prompt=prompt,
            params=params,
            max_coins=max_coins,
            start_image=start_image,
            cost_resolution=resolution,
            cost_duration=duration,
            api_key_override=api_key_override,
        )
