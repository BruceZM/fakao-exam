# -*- coding: utf-8 -*-
"""安全、跨平台地部署当前项目到 ModelScope 创空间。

流程：
1. 从 deploy.txt / 环境变量读取配置；
2. 通过临时 Git 仓库同步生产文件，不把 Token 写入 remote URL；
3. 通过 ModelScope OpenAPI 配置密文和变量；
4. 触发 Docker 创空间部署并等待新版健康检查通过；
5. 可选执行一次真实 AI 批改验证。

用法：
    python tools/deploy_ms.py --check
    python tools/deploy_ms.py
    python tools/deploy_ms.py --verify-ai
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx


ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "deploy.txt"
DEFAULT_API_ENDPOINT = "https://modelscope.cn/openapi/v1"
DEPLOY_FILES = (
    "Dockerfile", "requirements.txt", "server/main.py",
    "server/static/index.html", "server/static/app.js", "server/static/app.css",
    "app/data/questions.json",
)
LEGACY_DEPLOY_FILES = ()


class DeployError(RuntimeError):
    pass


def load_env_file(path: pathlib.Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


@dataclass
class Config:
    token: str
    studio: str
    llm_provider: str
    llm_api_key: str
    llm_url: str
    llm_model: str
    glm_api_key: str
    glm_url: str
    glm_model: str
    default_grader_model: str
    admin_code: str
    access_code: str
    access_users: str
    analytics_reset_id: str
    api_endpoint: str
    app_url: str

    @property
    def owner(self) -> str:
        return self.studio.split("/", 1)[0]

    @property
    def repo(self) -> str:
        return self.studio.split("/", 1)[1]

    @property
    def studio_api_path(self) -> str:
        return "/studios/%s/%s" % (quote(self.owner, safe=""), quote(self.repo, safe=""))


def load_config() -> Config:
    values = load_env_file(CONFIG_PATH)
    for key in (
        "MODELSCOPE_API_KEY", "MS_TOKEN", "MS_STUDIO", "LLM_PROVIDER",
        "LLM_API_KEY", "LLM_URL", "LLM_MODEL", "GLM_API_KEY", "GLM_URL",
        "GLM_MODEL", "DEFAULT_GRADER_MODEL", "ADMIN_CODE", "ACCESS_CODE", "ACCESS_USERS", "ANALYTICS_RESET_ID",
        "MODELSCOPE_ENDPOINT", "MS_APP_URL",
    ):
        if os.getenv(key):
            values[key] = os.environ[key]

    endpoint = values.get("MODELSCOPE_ENDPOINT", DEFAULT_API_ENDPOINT).rstrip("/")
    if not endpoint.endswith("/openapi/v1"):
        endpoint += "/openapi/v1"
    studio = values.get("MS_STUDIO", "").strip().strip("/")
    app_url = values.get("MS_APP_URL", "").strip().rstrip("/")
    if not app_url and "/" in studio:
        owner, repo = studio.lower().split("/", 1)
        app_url = "https://%s-%s.ms.show" % (owner, repo.replace("_", "-"))

    token = (values.get("MODELSCOPE_API_KEY") or values.get("MS_TOKEN") or "").strip()
    llm_provider = values.get("LLM_PROVIDER", "modelscope").strip().lower() or "modelscope"
    llm_api_key = values.get("LLM_API_KEY", "").strip()
    if llm_provider == "modelscope" and not llm_api_key:
        llm_api_key = token
    llm_url = (
        values.get("LLM_URL")
        or "https://api-inference.modelscope.cn/v1/chat/completions"
    ).strip()
    llm_model = (values.get("LLM_MODEL") or "Qwen/Qwen3-8B").strip()

    return Config(
        token=token,
        studio=studio,
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        llm_url=llm_url,
        llm_model=llm_model,
        glm_api_key=values.get("GLM_API_KEY", "").strip(),
        glm_url=(values.get("GLM_URL") or "https://open.bigmodel.cn/api/paas/v4/chat/completions").strip(),
        glm_model=(values.get("GLM_MODEL") or "glm-5.3-flash").strip(),
        default_grader_model=(values.get("DEFAULT_GRADER_MODEL") or "qwen").strip().lower(),
        admin_code=values.get("ADMIN_CODE", "").strip(),
        access_code=values.get("ACCESS_CODE", "").strip(),
        access_users=values.get("ACCESS_USERS", "").strip(),
        analytics_reset_id=values.get("ANALYTICS_RESET_ID", "").strip(),
        api_endpoint=endpoint,
        app_url=app_url,
    )


def validate_config(config: Config) -> list[str]:
    missing = []
    if not config.token: missing.append("MODELSCOPE_API_KEY")
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", config.studio): missing.append("MS_STUDIO（格式应为 owner/repo）")
    if not config.access_code: missing.append("ACCESS_CODE")
    for rel in DEPLOY_FILES:
        if not (ROOT / rel).is_file(): missing.append("部署文件：" + rel)
    if shutil.which("git") is None: missing.append("git 命令")
    return missing


def print_check(config: Config, missing: list[str]) -> None:
    print("配置文件:", "已找到" if CONFIG_PATH.exists() else "未找到")
    print("ModelScope Token:", "已配置" if config.token else "未配置")
    print("创空间:", config.studio or "未配置")
    print("大模型提供方:", config.llm_provider)
    print("大模型 API Key:", "已配置" if config.llm_api_key else "未配置")
    print("大模型接口:", config.llm_url)
    print("大模型:", config.llm_model)
    print("GLM API Key:", "已配置" if config.glm_api_key else "未配置（后台不显示 GLM）")
    print("GLM 接口:", config.glm_url)
    print("GLM 模型:", config.glm_model)
    print("默认批改模型:", config.default_grader_model)
    print("后台管理员口令:", "已配置" if config.admin_code else "未配置")
    print("访问口令:", "已配置" if config.access_code else "未配置")
    print("多用户口令:", "已配置" if config.access_users not in ("", "{}", "[]") else "未配置（可选）")
    print("统计重置标记:", "已配置（同一标记只清空一次）" if config.analytics_reset_id else "未配置")
    print("OpenAPI:", config.api_endpoint)
    if missing:
        print("\n尚缺少：")
        for item in missing:
            print("  -", item)
    else:
        print("\n部署前检查通过。")


def redact(text: str, config: Config) -> str:
    for secret in (config.token, config.llm_api_key, config.glm_api_key, config.admin_code, config.access_code):
        if secret:
            text = text.replace(secret, "<REDACTED>")
    return text


def run_git(args: list[str], *, cwd: pathlib.Path | None, env: dict[str, str], config: Config,
            check: bool = True) -> subprocess.CompletedProcess[str]:
    shown = " ".join(args[:3]) + (" …" if len(args) > 3 else "")
    print("$ git", shown)
    result = subprocess.run(
        ["git", *args], cwd=str(cwd) if cwd else None, env=env,
        text=True, capture_output=True, shell=False,
    )
    if check and result.returncode != 0:
        output = redact(((result.stdout or "") + (result.stderr or ""))[-1200:], config)
        raise DeployError("Git 命令失败（%s）：\n%s" % (shown, output.strip()))
    return result


def source_fingerprint() -> str:
    digest = hashlib.sha256()
    for rel in DEPLOY_FILES:
        digest.update(rel.encode("utf-8"))
        digest.update((ROOT / rel).read_bytes())
    return digest.hexdigest()[:12]


def sync_code(config: Config) -> str:
    """在临时目录中同步代码，避免 Token 或部署缓存残留在项目里。"""
    repo_url = "https://www.modelscope.cn/studios/%s.git" % config.studio
    with tempfile.TemporaryDirectory(prefix="fakao-ms-deploy-") as tmp:
        temp_root = pathlib.Path(tmp)
        askpass = temp_root / "git-askpass.sh"
        askpass.write_text(
            "#!/bin/sh\n"
            "case \"$1\" in\n"
            "  *Username*) printf '%s\\n' oauth2 ;;\n"
            "  *Password*) printf '%s\\n' \"$MODELSCOPE_GIT_TOKEN\" ;;\n"
            "  *) printf '\\n' ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        askpass.chmod(0o700)
        git_env = os.environ.copy()
        git_env.update({
            "GIT_ASKPASS": str(askpass),
            "GIT_TERMINAL_PROMPT": "0",
            "MODELSCOPE_GIT_TOKEN": config.token,
        })
        repo_dir = temp_root / "studio"
        run_git(["clone", "--branch", "master", "--single-branch", repo_url, str(repo_dir)],
                cwd=None, env=git_env, config=config)
        run_git(["config", "user.email", "deploy-bot@local"], cwd=repo_dir, env=git_env, config=config)
        run_git(["config", "user.name", "kemu2-deploy"], cwd=repo_dir, env=git_env, config=config)

        for rel in DEPLOY_FILES:
            destination = repo_dir / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, destination)
        for rel in LEGACY_DEPLOY_FILES:
            (repo_dir / rel).unlink(missing_ok=True)
        app_files = [rel for rel in DEPLOY_FILES if not rel.startswith("data/")]
        run_git(["add", "--", *app_files], cwd=repo_dir, env=git_env, config=config)
        run_git(["add", "-A", "--", "data"], cwd=repo_dir, env=git_env, config=config)
        changed = run_git(["diff", "--cached", "--quiet"], cwd=repo_dir, env=git_env,
                          config=config, check=False).returncode == 1
        if changed:
            message = "deploy: sync app %s" % source_fingerprint()
            run_git(["commit", "-m", message], cwd=repo_dir, env=git_env, config=config)
            run_git(["push", "origin", "HEAD:master"], cwd=repo_dir, env=git_env, config=config)
            print("代码已推送到 ModelScope。")
        else:
            print("线上仓库代码已是最新，无需重复提交。")
        revision = run_git(["rev-parse", "HEAD"], cwd=repo_dir, env=git_env, config=config).stdout.strip()
    return revision


def collect_named_values(payload: Any, field: str) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        value = payload.get(field)
        if isinstance(value, str):
            found.add(value)
        for nested in payload.values():
            found.update(collect_named_values(nested, field))
    elif isinstance(payload, list):
        for nested in payload:
            found.update(collect_named_values(nested, field))
    return found


def find_status(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("deploy_status", "runtime_status", "status", "state"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        for nested in payload.values():
            status = find_status(nested)
            if status:
                return status
    elif isinstance(payload, list):
        for nested in payload:
            status = find_status(nested)
            if status:
                return status
    return ""


class ModelScopeClient:
    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.Client(
            base_url=config.api_endpoint,
            headers={"Authorization": "Bearer " + config.token, "Accept": "application/json"},
            timeout=30,
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def request(self, method: str, path: str, *, body: dict[str, str] | None = None,
                sensitive: bool = False) -> Any:
        response = self.client.request(method, path, json=body)
        if response.status_code >= 400:
            detail = ""
            if not sensitive:
                detail = redact(response.text[:800], self.config)
            raise DeployError(
                "ModelScope OpenAPI %s %s 失败：HTTP %s%s" % (
                    method, path, response.status_code, ("\n" + detail) if detail else "",
                )
            )
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            return {"data": response.text}

    def verify_access(self) -> None:
        user = self.request("GET", "/users/me")
        names = collect_named_values(user, "username") | collect_named_values(user, "name")
        print("ModelScope 身份验证通过%s。" % (("：" + sorted(names)[0]) if names else ""))
        try:
            self.request("GET", self.config.studio_api_path)
        except DeployError as original_error:
            # OpenAPI 的 owner 大小写敏感，而网页域名和旧配置通常全部小写。
            corrected_owners = sorted(name for name in names if name.lower() == self.config.owner.lower())
            if not corrected_owners:
                raise original_error
            self.config.studio = corrected_owners[0] + "/" + self.config.repo
            try:
                self.request("GET", self.config.studio_api_path)
            except DeployError:
                raise original_error
            print("已自动修正创空间 ID 的大小写：", self.config.studio)
        print("已找到创空间：", self.config.studio)

    def upsert(self, kind: str, key: str, value: str) -> None:
        path = self.config.studio_api_path + "/" + kind
        current = self.request("GET", path)
        keys = collect_named_values(current, "key")
        methods = ["PUT", "POST"] if key in keys else ["POST", "PUT"]
        last_error: DeployError | None = None
        for method in methods:
            try:
                self.request(method, path, body={"key": key, "value": value}, sensitive=True)
                label = "密文" if kind == "secrets" else "变量"
                print("已%s%s：%s" % ("更新" if method == "PUT" else "添加", label, key))
                return
            except DeployError as exc:
                last_error = exc
        assert last_error is not None
        raise last_error

    def deploy(self) -> Any:
        result = self.request("POST", self.config.studio_api_path + "/deploy")
        print("已触发 ModelScope Docker 部署。")
        return result

    def studio_info(self) -> Any:
        return self.request("GET", self.config.studio_api_path)

    def logs(self, log_type: str) -> str:
        try:
            data = self.request("GET", self.config.studio_api_path + "/logs/" + log_type)
            if isinstance(data, str):
                return data
            return json.dumps(data, ensure_ascii=False, indent=2)
        except DeployError as exc:
            return str(exc)


def candidate_app_urls(config: Config) -> list[str]:
    owner = config.owner.lower()
    repo = config.repo.lower().replace("_", "-")
    candidates = [
        "https://studio-%s-%s.api-inference.modelscope.net" % (owner, repo),
        config.app_url,
    ]
    return list(dict.fromkeys(url.rstrip("/") for url in candidates if url))


def request_app(config: Config, method: str, path: str, *, body: dict[str, Any] | None = None,
                timeout: float = 20, extra_headers: dict[str, str] | None = None) -> httpx.Response | None:
    headers = {
        "Authorization": "Bearer " + config.token,
        "X-Access-Code": config.access_code,
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    if extra_headers:
        headers.update(extra_headers)
    for base in candidate_app_urls(config):
        try:
            response = httpx.request(method, base + path, headers=headers, json=body,
                                     timeout=timeout, follow_redirects=True)
            if response.status_code == 200:
                return response
        except httpx.HTTPError:
            continue
    return None


def verify_llm_access(config: Config) -> None:
    """部署前验证所有已配置模型，避免切换后才发现密钥或模型不可用。"""
    models = [(config.llm_provider, config.llm_api_key, config.llm_url, config.llm_model)]
    if config.glm_api_key:
        models.append(("glm", config.glm_api_key, config.glm_url, config.glm_model))
    for provider, api_key, url, model in models:
        payload = {
            "model": model,
            "temperature": 0.1,
            "max_tokens": 32,
            "messages": [{"role": "user", "content": "只回复OK"}],
        }
        if provider == "modelscope" or "api-inference.modelscope" in url:
            payload.update({
                "enable_thinking": False,
                "chat_template_kwargs": {"enable_thinking": False},
            })
        elif provider in ("zhipu", "glm"):
            if model.lower().startswith("glm-5.3"):
                payload["thinking"] = {"type": "enabled"}
                payload["reasoning_effort"] = "low"
            elif re.match(r"glm-(?:4\.[5-9]|[5-9])", model.lower()):
                payload["thinking"] = {"type": "disabled"}
        try:
            response = httpx.post(
                url,
                headers={"Authorization": "Bearer " + api_key},
                json=payload,
                timeout=30,
            )
        except httpx.HTTPError as exc:
            raise DeployError("%s 模型接口连接失败：%s" % (provider, type(exc).__name__)) from exc
        if response.status_code != 200:
            message = ""
            try:
                error = response.json().get("error", {})
                message = str(error.get("message", ""))[:300]
            except ValueError:
                pass
            raise DeployError("%s 的 API Key、URL 或模型验证失败：HTTP %s%s" % (
                provider, response.status_code, ("，" + message) if message else "",
            ))
        print("大模型接口验证通过：%s / %s" % (provider, model))


def wait_for_revision(client: ModelScopeClient, config: Config, revision: str, timeout_seconds: int) -> None:
    deadline=time.monotonic()+timeout_seconds; short=revision[:12]; print("等待线上版本生效：",short)
    while time.monotonic()<deadline:
        response=request_app(config,"GET","/api/health",timeout=12)
        if response is not None:
            try: health=response.json()
            except ValueError: health={}
            if health.get("status")=="ok" and int(health.get("questions",0))>0:
                print("线上健康检查通过：研究版题目 %s 条。" % health.get("questions")); return
        try: status=find_status(client.studio_info())
        except DeployError: status=""
        if str(status).lower() in {"failed","error","deployfailed","buildfailed"}: break
        time.sleep(8)
    print(redact(client.logs("build")[-3000:],config)); raise DeployError("部署未在 %s 秒内通过线上健康检查。"%timeout_seconds)


def verify_ai_grading(config: Config) -> None:
    payload = {
        "question_id": "C20",
        "answer": "学习动机是激发并维持学习，使行为指向学习目标的内部动力，由学习需要和学习期待构成；具有启动作用、定向作用、维持作用和调节作用。",
        "skipped": False,
    }
    response = request_app(
        config, "POST", "/api/grade", body=payload, timeout=90,
        extra_headers={"X-Admin-Code": config.admin_code},
    )
    if response is None:
        raise DeployError("线上 AI 批改验证请求失败。")
    result = response.json()
    if result.get("grader") != "ai":
        raise DeployError("线上批改仍未调用大模型，grader=%s。" % result.get("grader"))
    points = result.get("points") or []
    if result.get("rubric_version") != 1 or len(points) != 5:
        raise DeployError("线上批改没有使用新版语义评分规则。")
    if [point.get("status") for point in points] != ["hit"] * 5:
        raise DeployError("线上同义表达回归验证失败：%s" % [point.get("status") for point in points])
    if any(not point.get("evidence") for point in points):
        raise DeployError("线上批改没有返回完整的学生原文依据。")
    print("线上 AI 批改验证通过：5/5 语义规则命中，证据完整，得分=%s。" % result.get("total"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="部署法考备考研究版到 ModelScope 创空间")
    parser.add_argument("--check", action="store_true", help="只检查本地配置，不访问云端")
    parser.add_argument("--no-wait", action="store_true", help="触发部署后不等待构建完成")
    parser.add_argument("--verify-ai", action="store_true", help="部署后执行一次真实 AI 批改验证")
    parser.add_argument("--timeout", type=int, default=600, help="等待部署完成的最长秒数，默认 600")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()
    missing = validate_config(config)
    print_check(config, missing)
    if args.check:
        return 1 if missing else 0
    if missing:
        raise DeployError("配置尚未完成，请填写 deploy.txt 后重试。")

    client = ModelScopeClient(config)
    try:
        client.verify_access()
        revision = sync_code(config)
        client.upsert("secrets", "LLM_PROVIDER", config.llm_provider)
        client.upsert("secrets", "LLM_API_KEY", config.llm_api_key)
        client.upsert("secrets", "LLM_URL", config.llm_url)
        client.upsert("secrets", "LLM_MODEL", config.llm_model)
        if config.glm_api_key:
            client.upsert("secrets", "GLM_API_KEY", config.glm_api_key)
            client.upsert("secrets", "GLM_URL", config.glm_url)
            client.upsert("secrets", "GLM_MODEL", config.glm_model)
        client.upsert("secrets", "DEFAULT_GRADER_MODEL", config.default_grader_model)
        client.upsert("secrets", "ADMIN_CODE", config.admin_code)
        client.upsert("secrets", "ACCESS_CODE", config.access_code)
        client.upsert("secrets", "ACCESS_USERS", config.access_users)
        if config.analytics_reset_id:
            client.upsert("secrets", "ANALYTICS_RESET_ID", config.analytics_reset_id)
        # 部分旧版 Docker 创空间虽能读取 variables，却不支持新增/更新，
        # 因此非敏感配置也统一通过兼容性更好的 secrets 接口注入。
        client.upsert("secrets", "DEPLOY_REVISION", revision)
        client.deploy()
        if not args.no_wait:
            wait_for_revision(client, config, revision, max(30, args.timeout))
        print("\n部署完成：", config.app_url)
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DeployError as exc:
        print("\n部署失败：", exc, file=sys.stderr)
        raise SystemExit(1)
