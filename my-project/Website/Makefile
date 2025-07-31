# OpenDeepWiki Frontend Makefile

.PHONY: help install dev build preview lint test clean docker-build docker-run

# 默认目标
help:
	@echo "OpenDeepWiki Frontend 构建工具"
	@echo ""
	@echo "可用命令:"
	@echo "  install     安装依赖"
	@echo "  dev         启动开发服务器"
	@echo "  build       构建生产版本"
	@echo "  preview     预览生产版本"
	@echo "  lint        代码检查"
	@echo "  test        运行测试"
	@echo "  clean       清理构建文件"
	@echo "  docker-build 构建Docker镜像"
	@echo "  docker-run  运行Docker容器"

# 安装依赖
install:
	@echo "📦 安装依赖..."
	npm install

# 启动开发服务器
dev:
	@echo "🚀 启动开发服务器..."
	npm run dev

# 构建生产版本
build:
	@echo "🔨 构建生产版本..."
	npm run build

# 预览生产版本
preview:
	@echo "👀 预览生产版本..."
	npm run preview

# 代码检查
lint:
	@echo "🔍 代码检查..."
	npm run lint

# 运行测试
test:
	@echo "🧪 运行测试..."
	npm test

# 清理构建文件
clean:
	@echo "🧹 清理构建文件..."
	rm -rf dist
	rm -rf node_modules/.cache

# 构建Docker镜像
docker-build:
	@echo "🐳 构建Docker镜像..."
	docker build -t opendeepwiki-frontend .

# 运行Docker容器
docker-run:
	@echo "🐳 运行Docker容器..."
	docker run -p 3000:80 opendeepwiki-frontend

# 完整构建流程
all: install lint build
	@echo "✅ 完整构建流程完成！" 