IMAGE_SIZES_GPT2 = [
    "1024x1024",
    "1280x1024",
    "1024x1280",
    "1536x1024",
    "1024x1536",
    "2048x2048",
    "2048x1152",
    "1152x2048",
    "2048x1536",
    "1536x2048",
    "2560x1440",
    "1440x2560",
    "3840x2160",
    "2160x3840",
    "3824x2144",
    "2144x3824",
    "3840x1280",
    "1280x3840",
    "2688x1152",
    "1152x2688",
]

NANO_BANANA2_ASPECT_RATIOS = [
    "1:1",
    "1:4",
    "1:8",
    "2:3",
    "3:2",
    "3:4",
    "4:1",
    "4:3",
    "4:5",
    "5:4",
    "8:1",
    "9:16",
    "16:9",
    "21:9",
]

NANO_BANANA_PRO_ASPECT_RATIOS = [
    "1:1",
    "21:9",
    "16:9",
    "3:2",
    "4:3",
    "5:4",
    "4:5",
    "3:4",
    "2:3",
    "9:16",
]

FLUX2_PRO_ASPECT_RATIOS = [
    "square",
    "portrait_4_3",
    "portrait_16_9",
    "landscape_4_3",
    "landscape_16_9",
]

GROK_IMAGE_ASPECT_RATIOS = [
    "1:1",
    "2:1",
    "20:9",
    "16:9",
    "4:3",
    "3:2",
    "2:3",
    "3:4",
    "9:16",
    "9:20",
    "1:2",
]

SEEDANCE20_ASPECT_RATIOS = ["16:9", "9:16", "4:3", "3:4", "1:1", "21:9"]
GROK_VIDEO_ASPECT_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"]

IMAGE_RESOLUTIONS_NANO2 = ["512px", "1K", "2K", "4K"]
IMAGE_RESOLUTIONS_NANO_PRO = ["1K", "2K", "4K"]
VIDEO_RESOLUTIONS = ["480p", "720p"]

GPT2_QUALITY = ["auto", "low", "medium", "high"]

SEEDANCE20_DURATIONS = [str(item) for item in range(4, 16)]
GROK_VIDEO_DURATIONS = [str(item) for item in range(5, 16)]

# Main-site worker limit for start + references + end, despite schema maxFiles=9.
SEEDANCE20_REFERENCE_IMAGE_LIMIT = 4

SEEDANCE_MODELS = {"seedance20", "seedance20Mini"}
SEEDREAM5_IMAGE_SIZES = ["square", "portrait_4_3", "landscape_4_3", "portrait_16_9", "landscape_16_9"]
GEMINI_OMNI_ASPECT_RATIOS = ["16:9", "9:16"]
GEMINI_OMNI_DURATIONS = [str(item) for item in range(5, 11)]
