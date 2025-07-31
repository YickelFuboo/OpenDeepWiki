#!/bin/bash

# CodeWiki Backend 启动脚本
# 作者: CodeWiki Team
# 版本: 1.0.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查Python版本
check_python() {
    log_step "检查Python环境..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装Python3"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    log_info "Python版本: $python_version"
}

# 检查虚拟环境
check_venv() {
    log_step "检查虚拟环境..."
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_warn "未检测到虚拟环境，建议使用虚拟环境"
        read -p "是否创建虚拟环境? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python3 -m venv venv
            source venv/bin/activate
            log_info "虚拟环境已创建并激活"
        fi
    else
        log_info "虚拟环境已激活: $VIRTUAL_ENV"
    fi
}

# 安装依赖
install_dependencies() {
    log_step "安装Python依赖..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_info "依赖安装完成"
    else
        log_error "requirements.txt 文件不存在"
        exit 1
    fi
}

# 检查环境变量
check_env() {
    log_step "检查环境变量..."
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            log_warn "未找到.env文件，从env.example复制..."
            cp env.example .env
            log_info "请编辑.env文件配置数据库连接等信息"
        else
            log_error "未找到.env或env.example文件"
            exit 1
        fi
    else
        log_info "环境变量文件已存在"
    fi
}

# 数据库迁移
run_migrations() {
    log_step "运行数据库迁移..."
    if command -v alembic &> /dev/null; then
        alembic upgrade head
        log_info "数据库迁移完成"
    else
        log_warn "Alembic未安装，跳过数据库迁移"
    fi
}

# 启动应用
start_app() {
    log_step "启动CodeWiki Backend..."
    log_info "应用将在 http://localhost:8000 启动"
    log_info "API文档地址: http://localhost:8000/docs"
    log_info "按 Ctrl+C 停止服务"
    
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}

# 主函数
main() {
    echo "=========================================="
    echo "    CodeWiki Backend 启动脚本"
    echo "=========================================="
    echo
    
    check_python
    check_venv
    install_dependencies
    check_env
    run_migrations
    start_app
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 