# 运行验证记录（2026-09-03）

本记录对应 `application/` 的线上发布快照，仅记录当日可重复观察到的事实。

## 线上服务

- 服务状态：`risklens` 为 `active`
- 监听地址：`127.0.0.1:8767`
- 健康接口：`GET /api/health` 返回 `HTTP 200`
- 应用版本：`0.2.0`
- 向量库：状态 `ok`，本地模式；健康响应报告 1,840 个向量、101 份文档
- LLM：健康响应显示已配置；本记录不包含任何密钥、端点凭据或用户数据。

## 源码验证

已在当前线上发布目录执行：

```bash
python3 -m compileall -q backend/app backend/tests backend/evals
```

结果：成功（无语法编译错误）。

## 自动化测试复现

仓库保留测试文件于 `application/backend/tests/`，依赖在 `application/backend/requirements.txt` 中锁定。生产系统 Python 未安装 `pytest`，为避免在生产环境临时安装依赖，未直接执行完整测试集。评审或本地环境可按下列方式复现：

```bash
cd application
python -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
pytest -q
```

该记录不将语法编译或健康检查表述为业务准确性、授信审批或专业结论验证。
