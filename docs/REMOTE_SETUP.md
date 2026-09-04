# 远程项目初始化

## GitHub

当前本地仓库已绑定：

```text
git@github.com:BruceZM/fakao-exam.git
```

在 GitHub 创建同名空仓库后，在项目根目录执行：

```bash
git push -u origin main
```

推送后检查：

```bash
git ls-remote origin HEAD
```

## ModelScope

创建 Docker 创空间：

```text
Brockzm/fakao-exam
```

复制 `deploy.txt.example` 为 `deploy.txt`，填写本地部署配置。Token 只保存在本机，不提交 Git：

```ini
MODELSCOPE_API_KEY=你的Token
MS_STUDIO=Brockzm/fakao-exam
ACCESS_CODE=法考项目访问口令
```

先检查配置：

```bash
python3 tools/deploy_ms.py --check
```

检查通过后部署：

```bash
python3 tools/deploy_ms.py
```

部署脚本会等待 `/api/health` 返回 `status=ok` 且线上题目数量大于 0，才报告部署成功。
