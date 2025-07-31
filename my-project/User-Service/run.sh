#!/bin/bash

# User-Service 启动脚本
# 支持开发环境和生产环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  User-Service 启动脚本${NC}"
    echo -e "${BLUE}================================${NC}"
}

# 检查环境变量文件
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning "未找到 .env 文件，正在从 env.example 复制..."
        if [ -f "env.example" ]; then
            cp env.example .env
            print_message "已创建 .env 文件，请根据需要修改配置"
        else
            print_error "未找到 env.example 文件"
            exit 1
        fi
    fi
}

# 检查Python环境
check_python_env() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 未安装"
        exit 1
    fi
}

# 安装依赖
install_dependencies() {
    print_message "安装Python依赖..."
    pip3 install -r requirements.txt
}

# 检查数据库连接
check_database() {
    print_message "检查数据库连接..."
    python3 -c "
import os
import sys
sys.path.append('.')
from app.db.database.factory import get_db
from app.Conf.settings import get_settings

try:
    settings = get_settings()
    print(f'数据库配置: {settings.DATABASE_URL}')
    db = get_db()
    print('数据库连接成功')
except Exception as e:
    print(f'数据库连接失败: {e}')
    sys.exit(1)
"
}

# 运行数据库迁移
run_migrations() {
    print_message "运行数据库迁移..."
    python3 -c "
import os
import sys
sys.path.append('.')
from app.db.database.models.base import Base
from app.db.database.factory import get_db
from sqlalchemy import create_engine
from app.Conf.settings import get_settings

try:
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print('数据库迁移完成')
except Exception as e:
    print(f'数据库迁移失败: {e}')
    sys.exit(1)
"
}

# 启动开发服务器
start_dev_server() {
    print_message "启动开发服务器..."
    uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
}

# 启动生产服务器
start_prod_server() {
    print_message "启动生产服务器..."
    uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
}

# 运行测试
run_tests() {
    print_message "运行测试..."
    python3 -m pytest tests/ -v
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  dev         启动开发服务器"
    echo "  prod        启动生产服务器"
    echo "  install     安装依赖"
    echo "  check       检查环境"
    echo "  migrate     运行数据库迁移"
    echo "  test        运行测试"
    echo "  docker      使用Docker启动"
    echo "  help        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 dev       # 启动开发服务器"
    echo "  $0 install   # 安装依赖"
    echo "  $0 check     # 检查环境"
}

# 主函数
main() {
    print_header
    
    case "${1:-dev}" in
        "dev")
            check_env_file
            check_python_env
            install_dependencies
            check_database
            run_migrations
            start_dev_server
            ;;
        "prod")
            check_env_file
            check_python_env
            install_dependencies
            check_database
            run_migrations
            start_prod_server
            ;;
        "install")
            check_python_env
            install_dependencies
            ;;
        "check")
            check_env_file
            check_python_env
            check_database
            ;;
        "migrate")
            check_env_file
            check_python_env
            run_migrations
            ;;
        "test")
            check_python_env
            install_dependencies
            run_tests
            ;;
        "docker")
            print_message "使用Docker启动..."
            docker-compose up -d user-service
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 