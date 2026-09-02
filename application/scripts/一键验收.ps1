param(
    [string]$线上地址 = "https://fangzhou.chat/risklens/",
    [switch]$跳过Pytest
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$脚本目录 = Split-Path -Parent $MyInvocation.MyCommand.Path
$参数 = @("$脚本目录\one_click_acceptance.py", "--online", $线上地址)
if ($跳过Pytest) { $参数 += "--skip-pytest" }

python @参数
exit $LASTEXITCODE
