from __future__ import annotations

import base64
import io
from pathlib import Path


def tensor_to_image_inputs(image_tensor, *, max_images: int, name_prefix: str) -> list[dict]:
    if image_tensor is None:
        return []

    import numpy as np
    from PIL import Image

    if hasattr(image_tensor, "detach"):
        array = image_tensor.detach().cpu().numpy()
    else:
        array = np.asarray(image_tensor)

    if array.ndim == 3:
        array = array[None, ...]
    if array.ndim != 4:
        raise ValueError("IMAGE 输入必须是 [B,H,W,C] 或 [H,W,C] 格式")
    if len(array) > max_images:
        raise ValueError(f"Too many reference images: received {len(array)}, maximum {max_images}.")

    out: list[dict] = []
    for idx, img in enumerate(array):
        img = np.clip(img, 0.0, 1.0)
        if img.shape[-1] == 1:
            img = np.repeat(img, 3, axis=-1)
        if img.shape[-1] > 3:
            img = img[..., :3]
        data = (img * 255.0).round().astype(np.uint8)
        pil = Image.fromarray(data, mode="RGB")
        buffer = io.BytesIO()
        pil.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        out.append({
            "name": f"{name_prefix}_{idx + 1}.png",
            "base64": f"data:image/png;base64,{encoded}",
        })
    return out


def image_paths_to_tensor(paths: list[Path]):
    import numpy as np
    import torch
    from PIL import Image

    if not paths:
        raise ValueError("CatsAPI 没有返回图片文件")

    arrays = []
    target_size: tuple[int, int] | None = None
    for path in paths:
        with Image.open(path) as img:
            img = img.convert("RGB")
            if target_size is None:
                target_size = img.size
            elif img.size != target_size:
                img = img.resize(target_size, Image.Resampling.LANCZOS)
            arrays.append(np.asarray(img).astype(np.float32) / 255.0)
    return torch.from_numpy(np.stack(arrays, axis=0))
