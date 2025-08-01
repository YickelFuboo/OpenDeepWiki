#!/usr/bin/env python3
"""
项目结构测试脚本
验证转换后的Python项目是否完整可用
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有关键模块的导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试核心模块
        from src.conf.settings import settings
        print("✅ 配置模块导入成功")
        
        from src.core.database import engine, Base
        print("✅ 数据库模块导入成功")
        
        from src.core.auth import create_access_token, get_current_user
        print("✅ 认证模块导入成功")
        
        # 测试模型
        from src.models.user import User
        from src.models.role import Role
        from src.models.repository import Repository
        print("✅ 数据模型导入成功")
        
        # 测试DTO
        from src.dto.user_dto import UserInfoDto
        from src.dto.auth_dto import LoginDto
        from src.dto.menu_dto import MenuItemDto
        print("✅ DTO模块导入成功")
        
        # 测试服务
        from src.services.user_service import UserService
        from src.services.auth_service import AuthService
        from src.services.menu_service import MenuService
        print("✅ 服务模块导入成功")
        
        # 测试API
        from src.api import api_router
        print("✅ API路由导入成功")
        
        print("\n🎉 所有关键模块导入成功！")
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_config():
    """测试配置加载"""
    print("\n🔍 测试配置加载...")
    
    try:
        from src.conf.settings import settings
        
        # 检查必要的配置项
        assert hasattr(settings, 'database')
        assert hasattr(settings, 'jwt')
        assert hasattr(settings, 'openai')
        
        print("✅ 配置加载成功")
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    print("\n🔍 测试数据库连接...")
    
    try:
        from src.core.database import engine
        
        # 测试数据库连接
        async def test_connection():
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
        
        asyncio.run(test_connection())
        print("✅ 数据库连接成功")
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_api_structure():
    """测试API结构"""
    print("\n🔍 测试API结构...")
    
    try:
        from src.api import api_router
        
        # 检查路由数量
        routes = len(api_router.routes)
        print(f"✅ API路由数量: {routes}")
        
        # 检查子路由
        sub_routers = [route for route in api_router.routes if hasattr(route, 'routes')]
        print(f"✅ 子路由数量: {len(sub_routers)}")
        
        return True
        
    except Exception as e:
        print(f"❌ API结构测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试KoalaWiki Python项目...\n")
    
    tests = [
        test_imports,
        test_config,
        test_database_connection,
        test_api_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！项目结构完整。")
        return True
    else:
        print("⚠️  部分测试失败，请检查项目结构。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 