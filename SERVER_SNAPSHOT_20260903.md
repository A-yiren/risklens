# 当前运行源码快照说明

## 来源与完整性

- 快照日期：2026-09-03
- 来源：线上 RiskLens 当前发布目录
- 发布标识：`20260901-p0-contract-evidence`
- 导出归档：`risklens-source-20260903.tar.gz`
- SHA-256：`3c941c469b901aa26e7190f96caa19c598a678c941b7d582bffb2fd673c7cf8c`
- `application/`：由上述归档安全解包得到的源码快照

## 已排除内容

为避免泄露凭据、隐私或线上运行状态，归档和 GitHub 提交均排除：

- `.env`、私钥和证书文件
- 运行数据库、缓存、模型权重与日志
- 用户上传文件、运行输出、截图验证产物
- Python/Node 依赖目录与测试缓存

`.env.example`、示例知识数据、测试、评测数据、部署说明和合规文档均保留，便于本地复现。

## 提交前安全检查

对 `application/` 执行的静态检查未命中以下常见真实凭据模式：OpenAI/通用 `sk-` token、GitHub token、AWS access key、PEM 私钥块；也未发现 `.env`、`.pem` 或 `.key` 文件。该检查不替代部署方的密钥轮换、依赖审计或渗透测试。
