#!/usr/bin/env python3
"""RiskLens 一键验收模板：不依赖大模型，覆盖源码、页面和线上健康检查。"""

from __future__ import annotations

import argparse
import compileall
import html.parser
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote


APP_ROOT = Path(__file__).resolve().parents[1]
FRONTEND = APP_ROOT / "frontend"
BACKEND = APP_ROOT / "backend"


@dataclass
class Result:
    name: str
    status: str
    detail: str


class HtmlCheck(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in {"href", "src"} and value:
                self.refs.append(value)


def add(results: list[Result], name: str, ok: bool, detail: str, *, warning: bool = False) -> None:
    results.append(Result(name, "警告" if warning and not ok else "通过" if ok else "失败", detail))


def static_checks(results: list[Result]) -> None:
    required = [
        FRONTEND / "index.html",
        FRONTEND / "pages" / "login.html",
        FRONTEND / "pages" / "finance-precheck.html",
        FRONTEND / "pages" / "contract-review.html",
        FRONTEND / "pages" / "contract-workspace-preview.html",
        BACKEND / "app" / "main.py",
    ]
    missing = [str(path.relative_to(APP_ROOT)) for path in required if not path.is_file()]
    add(results, "核心文件存在", not missing, "全部存在" if not missing else "缺失：" + "、".join(missing))

    compiled = compileall.compile_dir(BACKEND / "app", quiet=1) and compileall.compile_dir(BACKEND / "tests", quiet=1)
    add(results, "后端语法编译", compiled, "backend/app 与 backend/tests 已通过编译" if compiled else "存在 Python 语法或编译错误")

    pages = list(FRONTEND.rglob("*.html"))
    parse_errors: list[str] = []
    missing_refs: list[str] = []
    for page in pages:
        parser = HtmlCheck()
        try:
            parser.feed(page.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive reporting
            parse_errors.append(f"{page.name}: {exc}")
            continue
        for ref in parser.refs:
            if ref.startswith(("#", "http:", "https:", "mailto:", "data:", "javascript:", "/api/")):
                continue
            local = ref.split("?", 1)[0].split("#", 1)[0]
            if not local:
                continue
            target = (page.parent / unquote(local)).resolve()
            if not target.exists():
                missing_refs.append(f"{page.relative_to(FRONTEND)} -> {ref}")
    add(results, "前端 HTML 解析", not parse_errors, "共检查 %d 个页面" % len(pages) if not parse_errors else "；".join(parse_errors))
    add(results, "前端本地资源引用", not missing_refs, "未发现断链" if not missing_refs else "；".join(missing_refs[:8]))


def request(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            return response.status, response.read(1_000_000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, str(exc)


def online_checks(results: list[Result], base_url: str) -> None:
    base = base_url.rstrip("/") + "/"
    routes = {
        "线上工作台": "",
        "融资材料预审页": "pages/finance-precheck.html",
        "合同模板与起草页": "pages/contract-workspace-preview.html",
        "健康检查接口": "api/health",
    }
    bodies: dict[str, str] = {}
    for name, route in routes.items():
        status, body = request(base + route)
        bodies[name] = body
        add(results, name, status == 200, f"HTTP {status}")

    try:
        health = json.loads(bodies["健康检查接口"])
        health_ok = health.get("status") == "ok" and bool(health.get("llm_configured"))
        add(results, "健康接口内容", health_ok, "status=%s, LLM=%s, 向量=%s" % (health.get("status"), health.get("llm_configured"), health.get("vector_count")))
    except json.JSONDecodeError:
        add(results, "健康接口内容", False, "返回不是 JSON")

    # 产品主入口必须直接引导到融资材料预审，防止旧法律产品导航误上线。
    home = bodies["线上工作台"]
    finance_nav = "finance-precheck.html" in home and "融资材料预审" in home
    add(results, "主入口金融场景一致性", finance_nav, "主入口包含融资材料预审入口" if finance_nav else "主入口仍未展示融资材料预审入口")
    finance = bodies["融资材料预审页"]
    finance_shell = "融资材料预审" in finance and "人工复核" in finance
    add(results, "预审页框架", finance_shell, "预审页与人工复核提示存在" if finance_shell else "预审页关键框架缺失")
    contract = bodies["合同模板与起草页"]
    contract_shell = "交易合同管理" in contract and "合同模板库" in contract and "/api/contracts/templates" in contract
    add(results, "合同模板页框架", contract_shell, "模板页与模板接口入口存在" if contract_shell else "模板页或模板接口入口缺失")


def optional_pytest(results: list[Result]) -> None:
    if not shutil.which("pytest") and not (Path(sys.executable).parent / "pytest").exists():
        add(results, "pytest 回归测试", False, "当前 Python 环境未安装 pytest；安装 requirements 后会自动执行", warning=True)
        return
    completed = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=BACKEND, text=True, capture_output=True, timeout=300)
    detail = (completed.stdout + completed.stderr).strip().splitlines()
    add(results, "pytest 回归测试", completed.returncode == 0, detail[-1] if detail else f"退出码 {completed.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="RiskLens 一键验收")
    parser.add_argument("--online", metavar="URL", help="线上根地址，例如 https://fangzhou.chat/risklens/")
    parser.add_argument("--skip-pytest", action="store_true", help="跳过可选 pytest 回归")
    parser.add_argument("--report", type=Path, help="把结果写入指定 JSON 文件")
    args = parser.parse_args()

    results: list[Result] = []
    static_checks(results)
    if args.online:
        online_checks(results, args.online)
    if not args.skip_pytest:
        optional_pytest(results)

    for item in results:
        print(f"[{item.status}] {item.name}：{item.detail}")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"结果已写入：{args.report}")
    return 1 if any(item.status == "失败" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
