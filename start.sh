#!/bin/bash
# 启动US GAAP Web Service

# 激活虚拟环境
source venv/bin/activate

# 启动服务
echo "启动US GAAP 2025 Web Service..."
echo "访问地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "Web界面: http://localhost:8000/index.html"
echo "按Ctrl+C停止服务"

python -m uvicorn main:app --host 0.0.0.0 --port 8000