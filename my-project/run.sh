#!/bin/bash

# Pando 项目一键启动脚本
# 作者: Pando Team
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

# 检查Docker
check_docker() {
    log_step "检查Docker环境..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装Docker Compose"
        exit 1
    fi
    
    docker_version=$(docker --version)
    compose_version=$(docker-compose --version)
    log_info "Docker版本: $docker_version"
    log_info "Docker Compose版本: $compose_version"
}

# 检查环境变量
check_env() {
    log_step "检查环境变量..."
    if [ ! -f ".env" ]; then
        log_warn "未找到.env文件，创建默认环境变量文件..."
        cat > .env << EOF
# Pando 环境变量配置
# 数据库配置
POSTGRES_DB=pando
POSTGRES_USER=pando
POSTGRES_PASSWORD=pando123

# Redis配置
REDIS_URL=redis://redis:6379

# API密钥（请替换为真实的API密钥）
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# JWT配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF
        log_info "已创建.env文件，请编辑配置您的API密钥"
    else
        log_info "环境变量文件已存在"
    fi
}

# 构建镜像
build_images() {
    log_step "构建Docker镜像..."
    docker-compose build
    log_info "镜像构建完成"
}

# 启动服务
start_services() {
    log_step "启动OpenDeepWiki服务..."
    docker-compose up -d
    
    log_info "服务启动中，请稍候..."
    sleep 10
    
    # 检查服务状态
    docker-compose ps
    
    log_info "=========================================="
    log_info "Pando 服务已启动！"
    log_info "=========================================="
    log_info "前端地址: http://localhost"
    log_info "后端API: http://localhost/api"
    log_info "API文档: http://localhost/api/docs"
    log_info "数据库: localhost:5432"
    log_info "Redis: localhost:6379"
    log_info "=========================================="
}

# 停止服务
stop_services() {
    log_step "停止OpenDeepWiki服务..."
    docker-compose down
    log_info "服务已停止"
}

# 重启服务
restart_services() {
    log_step "重启OpenDeepWiki服务..."
    docker-compose restart
    log_info "服务已重启"
}

# 查看日志
show_logs() {
    log_step "显示服务日志..."
    docker-compose logs -f
}

# 清理服务
clean_services() {
    log_step "清理OpenDeepWiki服务..."
    docker-compose down -v
    docker system prune -f
    log_info "服务已清理"
}

# 显示帮助
show_help() {
    echo "=========================================="
    echo "    Pando 项目管理脚本"
    echo "=========================================="
    echo
    echo "可用命令:"
    echo "  start     启动所有服务"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  logs      查看服务日志"
    echo "  clean     清理所有服务"
    echo "  build     构建Docker镜像"
    echo "  help      显示此帮助信息"
    echo
    echo "示例:"
    echo "  ./run.sh start    # 启动服务"
    echo "  ./run.sh logs     # 查看日志"
    echo "  ./run.sh stop     # 停止服务"
    echo
}

# 主函数
main() {
    case "${1:-start}" in
        start)
            check_docker
            check_env
            build_images
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs
            ;;
        clean)
            clean_services
            ;;
        build)
            check_docker
            build_images
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 