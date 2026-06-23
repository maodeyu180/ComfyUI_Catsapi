from __future__ import annotations

import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


DEFAULT_BASE = "https://catsapi.com"
API_KEY_ENV = "CATSAPI_API_KEY"
POLL_INTERVAL = 3
POLL_TIMEOUT = 900
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
DOWNLOAD_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,video/*,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://catsapi.com/",
}


class CatsAPIError(RuntimeError):
    pass


def _looks_truncated_key(key: str) -> bool:
    return "..." in key or "…" in key


def _unquote_shell_value(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    try:
        parts = shlex.split(value, comments=True, posix=True)
    except ValueError:
        parts = []
    if parts:
        return parts[0].strip()
    if value[0] not in {"'", '"'} and " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value.strip()


def _read_key_assignment(path: pathlib.Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    pattern = re.compile(rf"^\s*(?:export\s+)?{API_KEY_ENV}\s*=\s*(.+?)\s*$")
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = pattern.match(line)
        if match:
            return _unquote_shell_value(match.group(1))
    return ""


def _candidate_key_files() -> list[pathlib.Path]:
    package_dir = pathlib.Path(__file__).resolve().parent
    cwd = pathlib.Path.cwd()
    home = pathlib.Path.home()
    paths = [
        package_dir / ".env",
        cwd / ".env",
        home / ".catsapi.env",
        home / ".zshrc",
        home / ".bashrc",
        home / ".profile",
        home / ".bash_profile",
    ]
    seen: set[pathlib.Path] = set()
    unique: list[pathlib.Path] = []
    for path in paths:
        try:
            resolved = path.expanduser().resolve()
        except OSError:
            resolved = path.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def find_configured_api_key() -> str:
    env_key = os.environ.get(API_KEY_ENV, "").strip()
    if env_key:
        return env_key
    for path in _candidate_key_files():
        key = _read_key_assignment(path).strip()
        if key:
            return key
    return ""


def get_api_key(api_key_override: str | None = None) -> str:
    key = (api_key_override or "").strip() or find_configured_api_key()
    if not key:
        raise CatsAPIError(
            "未找到有效 CATSAPI_API_KEY。请在 catsapi.com 创建完整 Key 后配置到环境变量、.env 或 ~/.catsapi.env。"
        )
    if _looks_truncated_key(key):
        raise CatsAPIError("CATSAPI_API_KEY 看起来像被省略或截断的占位符,请重新复制完整 Key。")
    if not key.startswith("cats-"):
        raise CatsAPIError("CATSAPI_API_KEY 格式不正确,应以 cats- 开头。")
    return key


def base_url() -> str:
    return os.environ.get("CATSAPI_BASE", DEFAULT_BASE).rstrip("/")


def request_json(
    method: str,
    path: str,
    body: dict | None = None,
    timeout: int = 60,
    api_key_override: str | None = None,
) -> dict:
    url = f"{base_url()}{path}"
    headers = {
        "Authorization": f"Bearer {get_api_key(api_key_override)}",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    data: bytes | None = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw).get("detail", raw)
        except Exception:
            detail = raw
        raise CatsAPIError(f"HTTP {exc.code} {method} {path}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise CatsAPIError(f"网络错误 {method} {url}: {exc.reason}") from exc

    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CatsAPIError(f"无法解析 CatsAPI 响应: {raw[:300]}") from exc


def post_json(
    path: str,
    body: dict,
    timeout: int = 60,
    api_key_override: str | None = None,
) -> dict:
    return request_json("POST", path, body, timeout=timeout, api_key_override=api_key_override)


def get_json(path: str, timeout: int = 60, api_key_override: str | None = None) -> dict:
    return request_json("GET", path, timeout=timeout, api_key_override=api_key_override)


def preview_cost(
    *,
    model: str,
    task_type: str,
    num_images: int = 1,
    has_image_input: bool = False,
    resolution: str | None = None,
    duration: str | None = None,
    mode: str | None = None,
    rewrite_prompt: bool = False,
    api_key_override: str | None = None,
) -> dict:
    body: dict[str, Any] = {
        "model": model,
        "task_type": task_type,
        "num_images": num_images,
        "has_image_input": has_image_input,
        "rewrite_prompt": rewrite_prompt,
    }
    if resolution:
        body["resolution"] = resolution
    if duration:
        body["duration"] = duration
    if mode:
        body["mode"] = mode
    return post_json("/api/tasks/cost-preview", body, api_key_override=api_key_override)


def submit_task(
    *,
    model: str,
    task_type: str,
    prompt: str,
    params: dict,
    num_images: int = 1,
    images: list[dict] | None = None,
    files: dict | None = None,
    api_key_override: str | None = None,
) -> dict:
    body: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "task_type": task_type,
        "params": params,
        "num_images": num_images,
    }
    if images:
        body["images"] = images
    if files:
        body["files"] = files
    return post_json("/api/tasks", body, api_key_override=api_key_override)


def poll_task(
    task_id: str,
    *,
    poll_interval: int = POLL_INTERVAL,
    timeout: int = POLL_TIMEOUT,
    api_key_override: str | None = None,
) -> dict:
    started = time.time()
    while True:
        time.sleep(poll_interval)
        detail = get_json(
            f"/api/tasks/{urllib.parse.quote(str(task_id))}",
            timeout=60,
            api_key_override=api_key_override,
        )
        status = detail.get("status", "")
        if status == "completed":
            return detail
        if status == "failed":
            raise CatsAPIError(f"任务失败: {detail.get('error_message', '未知错误')}")
        if time.time() - started > timeout:
            raise CatsAPIError(f"轮询超时,任务仍在 {status}。task_id={task_id}")


def _looks_like_challenge(path: pathlib.Path, content_type: str = "") -> bool:
    if "text/html" in (content_type or "").lower():
        return True
    try:
        head = path.read_bytes()[:512].lstrip().lower()
    except OSError:
        return False
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


def _download_with_urllib(url: str, out_path: pathlib.Path) -> pathlib.Path:
    req = urllib.request.Request(url, headers=DOWNLOAD_HEADERS)
    with urllib.request.urlopen(req, timeout=300) as resp, out_path.open("wb") as f:
        content_type = resp.headers.get("content-type", "")
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
    if _looks_like_challenge(out_path, content_type):
        raise CatsAPIError("下载结果像是 HTML 验证页,不是媒体文件。")
    return out_path


def _download_with_curl(url: str, out_path: pathlib.Path) -> pathlib.Path:
    curl = shutil.which("curl")
    if not curl:
        raise CatsAPIError("urllib 下载失败,且系统未找到 curl 作为备用下载器。")
    tmp_path = out_path.with_suffix(out_path.suffix + ".download")
    cmd = [
        curl,
        "--fail",
        "--location",
        "--silent",
        "--show-error",
        "--retry",
        "2",
        "--connect-timeout",
        "20",
        "--max-time",
        "300",
        "--output",
        str(tmp_path),
    ]
    for key, value in DOWNLOAD_HEADERS.items():
        cmd.extend(["-H", f"{key}: {value}"])
    cmd.append(url)
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        message = (exc.stderr or exc.stdout or "").strip()
        raise CatsAPIError(f"curl 备用下载失败: {message[:300]}") from exc
    if _looks_like_challenge(tmp_path):
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise CatsAPIError("curl 下载结果像是 HTML 验证页,不是媒体文件。")
    tmp_path.replace(out_path)
    return out_path


def download_file(url: str, out_path: pathlib.Path) -> pathlib.Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        return _download_with_urllib(url, out_path)
    except Exception as first_exc:
        try:
            return _download_with_curl(url, out_path)
        except Exception as second_exc:
            raise CatsAPIError(f"下载结果失败: {first_exc}; curl fallback: {second_exc}") from second_exc


def default_output_dir() -> pathlib.Path:
    try:
        import folder_paths

        return pathlib.Path(folder_paths.get_output_directory()) / "catsapi"
    except Exception:
        return pathlib.Path("/tmp/comfyui-catsapi-output")
