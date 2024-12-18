#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# 检查Python是否安装
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装，请先安装 Python3"
        exit 1
    fi
    print_message "检测到 Python3 已安装"
}

# 检查pip是否安装
check_pip() {
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 未安装，请先安装 pip3"
        exit 1
    fi
    print_message "检测到 pip3 已安装"
}

# 创建虚拟环境
create_venv() {
    print_message "创建虚拟环境..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    print_message "虚拟环境创建完成"
}

# 激活虚拟环境
activate_venv() {
    print_message "激活虚拟环境..."
    source venv/bin/activate
}

# 安装依赖
install_dependencies() {
    print_message "安装项目依赖..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        print_error "依赖安装失败"
        exit 1
    fi
    print_message "依赖安装完成"
}

# 创建必要的目录
create_directories() {
    print_message "创建必要的目录..."
    mkdir -p app/static/uploads
    print_message "目录创建完成"
}

# 运行测试
run_tests() {
    print_message "运行测试..."
    PYTHONPATH=$PYTHONPATH:./app pytest tests/
    if [ $? -ne 0 ]; then
        print_error "测试失败"
        exit 1
    fi
    print_message "测试通过"
}

# 启动服务
start_service() {
    print_message "启动服务..."
    cd app
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}

# 主函数
main() {
    print_message "开始部署图片处理服务..."
    
    check_python
    check_pip
    create_venv
    activate_venv
    install_dependencies
    create_directories
    run_tests
    start_service
}

# 运行主函数
main
