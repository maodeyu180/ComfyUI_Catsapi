from .nodes import (
    CatsAPIFLUX2Pro,
    CatsAPIGPTImage2,
    CatsAPIGeminiOmniFlash,
    CatsAPIGrokImage,
    CatsAPIGrokImage2,
    CatsAPIGrokImageVideo,
    CatsAPINanoBanana2,
    CatsAPINanoBananaPro,
    CatsAPISeedance20,
    CatsAPISeedance20Mini,
    CatsAPISeedream5Lite,
    CatsAPISeedream5Pro,
)

NODE_CLASS_MAPPINGS = {
    "CatsAPIGPTImage2": CatsAPIGPTImage2,
    "CatsAPINanoBanana2": CatsAPINanoBanana2,
    "CatsAPINanoBananaPro": CatsAPINanoBananaPro,
    "CatsAPIFLUX2Pro": CatsAPIFLUX2Pro,
    "CatsAPIGrokImage": CatsAPIGrokImage,
    "CatsAPISeedance20": CatsAPISeedance20,
    "CatsAPIGrokImageVideo": CatsAPIGrokImageVideo,
    "CatsAPISeedream5Lite": CatsAPISeedream5Lite,
    "CatsAPISeedream5Pro": CatsAPISeedream5Pro,
    "CatsAPIGrokImage2": CatsAPIGrokImage2,
    "CatsAPISeedance20Mini": CatsAPISeedance20Mini,
    "CatsAPIGeminiOmniFlash": CatsAPIGeminiOmniFlash,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CatsAPIGPTImage2": "CatsAPI GPT Image 2",
    "CatsAPINanoBanana2": "CatsAPI Nano Banana 2",
    "CatsAPINanoBananaPro": "CatsAPI Nano Banana Pro",
    "CatsAPIFLUX2Pro": "CatsAPI FLUX.2 Pro",
    "CatsAPIGrokImage": "CatsAPI GrokImage",
    "CatsAPISeedance20": "CatsAPI Seedance 2.0",
    "CatsAPIGrokImageVideo": "CatsAPI GrokImageVideo",
    "CatsAPISeedream5Lite": "CatsAPI Seedream 5 Lite",
    "CatsAPISeedream5Pro": "CatsAPI Seedream 5 Pro",
    "CatsAPIGrokImage2": "CatsAPI Grok Imagine Image 2",
    "CatsAPISeedance20Mini": "CatsAPI Seedance 2.0 Mini",
    "CatsAPIGeminiOmniFlash": "CatsAPI Gemini Omni Flash",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
