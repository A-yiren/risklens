# RiskLens 新电脑交接与启动说明

本文件随源码交接包提供，帮助在另一台电脑继续开发。更新日期：2026-08-27。

## 包内内容

- 完整源码、前端页面、合同工作台 UI 原型；
- 合同审查 V2、合同生成第一阶段、测试和评测文件；
- 部署脚本、评测报告、完整工作交接文档；
- `SOURCE-MANIFEST.json`：源码文件和 SHA-256 清单。

源码包不含 API Key、JWT Secret、SSH 私钥、`.env`、虚拟环境、缓存或真实运行数据。

## 新电脑准备

1. 安装 Git 与 Python 3.12（Python 3.10+ 也可尝试）。
2. 解压源码包后进入项目根目录。
3. 创建并启用虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

4. 从 `.env.example` 复制为 `.env`，通过安全渠道填入 `LLM_API_KEY` 和至少 32 字符的 `JWT_SECRET`。不要把 `.env` 发到聊天、Git 或普通压缩包。
5. 如果没有单独迁移运行数据，运行 `backend/scripts/local_full_ingest.py` 重建种子知识库。
6. 启动：

```powershell
Set-Location backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8765
```

7. 测试：

```powershell
Set-Location backend
python -m pytest -q
```

## 运行数据迁移

真实 SQLite、Qdrant 向量库和用户上传文件不与普通源码包混放。若要继续使用当前本地数据，请使用单独的 `RiskLens-本地运行数据备份-20260827.zip`，把其中的 `storage` 目录复制到新电脑的项目根目录。

复制前先备份新电脑上已有的 `storage` 目录；不要将旧数据直接覆盖到生产服务器。数据备份不包含 `.env` 和任何密钥。

## 当前状态

- 本地最后一次测试：`42 passed`；
- 合同审查 V2 已在云端仅管理员预览，普通用户主开关关闭；
- 合同生成 V1 仍为需求整理后端与 UI 原型，尚未接入 LLM 生成合同；
- 当前服务器仍运行 release `20260827-11fcc2a`，本地最新 UI 与合同生成第一阶段尚未上传。

详细情况请优先阅读 `outputs/RiskLens-完整工作汇报与项目交接-20260827.md`。
