from typing import List
from fastapi import FastAPI, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from src.core.database import get_db
from src.models.warehouse import Warehouse, WarehouseStatus
from src.models.document_catalog import DocumentCatalog


class SitemapExtensions:
    """站点地图扩展"""
    
    URL_TEMPLATE = '<url><loc>{0}</loc><changefreq>{1}</changefreq><priority>{2}</priority></url>'
    
    @staticmethod
    async def execute_sitemap(request: Request, db: AsyncSession) -> Response:
        """执行站点地图生成"""
        try:
            # 获取所有已完成的仓库
            warehouses_result = await db.execute(
                select(Warehouse).where(Warehouse.status == WarehouseStatus.Completed)
            )
            warehouses = warehouses_result.scalars().all()
            
            # 获取仓库的所有目录
            warehouse_ids = [w.id for w in warehouses]
            catalogs_result = await db.execute(
                select(DocumentCatalog).where(DocumentCatalog.warehouse_id.in_(warehouse_ids))
            )
            catalogs = catalogs_result.scalars().all()
            
            # 构建XML内容
            xml_parts = []
            
            # 添加仓库URL
            for warehouse in warehouses:
                url = f"https://{request.base_url.hostname}/{warehouse.organization_name}/{warehouse.name}"
                xml_parts.append(SitemapExtensions.URL_TEMPLATE.format(url, "weekly", "0.5"))
            
            # 添加目录URL
            for catalog in catalogs:
                warehouse = next((w for w in warehouses if w.id == catalog.warehouse_id), None)
                if warehouse:
                    url = f"https://{request.base_url.hostname}/{warehouse.organization_name}/{warehouse.name}/{catalog.url}"
                    xml_parts.append(SitemapExtensions.URL_TEMPLATE.format(url, "weekly", "0.5"))
            
            # 构建完整的XML
            xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" 
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9" 
        xmlns:xhtml="http://www.w3.org/1999/xhtml" 
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" 
        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">
{''.join(xml_parts)}
</urlset>"""
            
            return Response(
                content=xml_content,
                media_type="application/xml"
            )
            
        except Exception as e:
            logger.error(f"生成站点地图失败: {e}")
            return Response(
                content="<error>站点地图生成失败</error>",
                media_type="application/xml",
                status_code=500
            )
    
    @staticmethod
    def map_sitemap(app: FastAPI):
        """映射站点地图路由"""
        @app.get("/sitemap.xml")
        async def sitemap_xml(request: Request, db: AsyncSession = Depends(get_db)):
            return await SitemapExtensions.execute_sitemap(request, db)
        
        @app.get("/api/sitemap.xml")
        async def api_sitemap_xml(request: Request, db: AsyncSession = Depends(get_db)):
            return await SitemapExtensions.execute_sitemap(request, db)
        
        return app 