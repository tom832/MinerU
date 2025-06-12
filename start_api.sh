#!/bin/bash

# MinerU API 服务启动脚本 v2.0

echo "=========================================="
echo "       MinerU API 服务 v2.0"
echo "=========================================="
echo "端口: 8766"
echo "服务地址: http://localhost:8766"
echo "API 文档: http://localhost:8766/docs"
echo "ReDoc 文档: http://localhost:8766/redoc"
echo "健康检查: http://localhost:8766/health"
echo ""
echo "功能:"
echo "  - PDF 处理: POST /process/pdf"
echo "  - 图片处理: POST /process/image"
echo ""
echo "认证: Bearer Token (配置在 .env 文件中)"
echo "默认 Token: your-secret-token-here"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，使用默认配置"
    echo "   建议: cp env_example .env 并编辑 API_TOKEN"
    echo ""
else
    echo "✅ 已找到 .env 配置文件"
    echo ""
fi

# 启动服务
nvtop