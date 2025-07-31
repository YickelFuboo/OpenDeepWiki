#!/bin/bash

# CodeWiki Frontend 启动脚本
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

# 检查Node.js版本
check_node() {
    log_step "检查Node.js环境..."
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装Node.js"
        exit 1
    fi
    
    node_version=$(node --version)
    log_info "Node.js版本: $node_version"
    
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装，请先安装npm"
        exit 1
    fi
    
    npm_version=$(npm --version)
    log_info "npm版本: $npm_version"
}

# 检查package.json
check_package_json() {
    log_step "检查项目配置..."
    if [ ! -f "package.json" ]; then
        log_error "package.json 文件不存在"
        exit 1
    fi
    log_info "项目配置文件已找到"
}

# 安装依赖
install_dependencies() {
    log_step "安装Node.js依赖..."
    if [ ! -d "node_modules" ]; then
        log_info "首次运行，安装依赖..."
        npm install
        log_info "依赖安装完成"
    else
        log_info "依赖已安装，跳过安装步骤"
    fi
}

# 检查环境变量
check_env() {
    log_step "检查环境变量..."
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            log_warn "未找到.env文件，从env.example复制..."
            cp env.example .env
            log_info "请编辑.env文件配置API地址等信息"
        else
            log_info "未找到环境变量文件，使用默认配置"
        fi
    else
        log_info "环境变量文件已存在"
    fi
}

# 构建项目（可选）
build_project() {
    log_step "检查是否需要构建..."
    read -p "是否构建生产版本? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "开始构建项目..."
        npm run build
        log_info "构建完成"
    fi
}

# 启动开发服务器
start_dev_server() {
    log_step "启动CodeWiki Frontend开发服务器..."
    log_info "应用将在 http://localhost:3000 启动"
    log_info "按 Ctrl+C 停止服务"
    
    npm run dev
}

# 启动预览服务器
start_preview_server() {
    log_step "启动CodeWiki Frontend预览服务器..."
    log_info "应用将在 http://localhost:4173 启动"
    log_info "按 Ctrl+C 停止服务"
    
    npm run preview
}

# 主函数
main() {
    echo "=========================================="
    echo "    CodeWiki Frontend 启动脚本"
    echo "=========================================="
    echo
    
    check_node
    check_package_json
    install_dependencies
    check_env
    
    echo
    echo "请选择启动模式:"
    echo "1) 开发模式 (推荐)"
    echo "2) 预览模式 (需要先构建)"
    echo "3) 构建并预览"
    read -p "请选择 (1-3): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            start_dev_server
            ;;
        2)
            start_preview_server
            ;;
        3)
            build_project
            start_preview_server
            ;;
        *)
            log_error "无效选择，默认启动开发模式"
            start_dev_server
            ;;
    esac
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 