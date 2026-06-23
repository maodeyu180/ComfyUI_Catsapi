from .nodes import (
    CatsAPIFLUX2Pro,
    CatsAPIGPTImage2,
    CatsAPIGrokImage,
    CatsAPIGrokImageVideo,
    CatsAPINanoBanana2,
    CatsAPINanoBananaPro,
    CatsAPISeedance20,
)

NODE_CLASS_MAPPINGS = {
    "CatsAPIGPTImage2": CatsAPIGPTImage2,
    "CatsAPINanoBanana2": CatsAPINanoBanana2,
    "CatsAPINanoBananaPro": CatsAPINanoBananaPro,
    "CatsAPIFLUX2Pro": CatsAPIFLUX2Pro,
    "CatsAPIGrokImage": CatsAPIGrokImage,
    "CatsAPISeedance20": CatsAPISeedance20,
    "CatsAPIGrokImageVideo": CatsAPIGrokImageVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CatsAPIGPTImage2": "CatsAPI GPT Image 2",
    "CatsAPINanoBanana2": "CatsAPI Nano Banana 2",
    "CatsAPINanoBananaPro": "CatsAPI Nano Banana Pro",
    "CatsAPIFLUX2Pro": "CatsAPI FLUX.2 Pro",
    "CatsAPIGrokImage": "CatsAPI GrokImage",
    "CatsAPISeedance20": "CatsAPI Seedance 2.0",
    "CatsAPIGrokImageVideo": "CatsAPI GrokImageVideo",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
