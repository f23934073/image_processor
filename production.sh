#!/bin/bash

# 设置生产环境变量
export APP_DEBUG=false
export APP_PORT=8000

# 安装生产环境所需的额外依赖
pip install gunicorn

# 使用 gunicorn 启动服务
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app \
    --bind 0.0.0.0:$APP_PORT \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --daemon
