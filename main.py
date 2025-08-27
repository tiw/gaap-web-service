#!/usr/bin/env python3
"""
US GAAP 2025 Web Service
根据指标名称查找标签定义和参考标准
"""

import sys
import os

# 添加项目目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from typing import Dict, List, Optional
from gaap_parser import GAAPParser

# 初始化FastAPI应用
app = FastAPI(
    title="US GAAP 2025 Web Service",
    description="根据指标名称查找标签定义和参考标准的Web服务",
    version="1.0.0"
)

# 初始化解析器
GAAP_DIR = "/Users/wangting/work/us-gaap-2025"
if not os.path.exists(GAAP_DIR):
    raise RuntimeError(f"GAAP directory not found: {GAAP_DIR}")

parser = GAAPParser(GAAP_DIR)

# API路由
@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "US GAAP 2025 Web Service",
        "description": "根据指标名称查找标签定义和参考标准",
        "endpoints": {
            "/elements": "获取所有GAAP指标列表",
            "/element/{element_name}": "获取指定元素的完整信息",
            "/element/{element_name}/label": "获取指定元素的标签定义",
            "/element/{element_name}/references": "获取指定元素的参考标准"
        },
        "web_interface": "/index.html"
    }

@app.get("/elements")
async def get_all_elements(skip: int = 0, limit: int = 100):
    """获取所有GAAP元素名称列表"""
    try:
        all_elements = parser.get_all_element_names()
        
        # 分页处理
        total = len(all_elements)
        elements = all_elements[skip:skip+limit]
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "elements": elements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/element/{element_name}")
async def get_element_info(element_name: str):
    """获取指定元素的完整信息"""
    try:
        info = parser.get_element_info(element_name)
        if not info['label'] and not info['references']:
            raise HTTPException(status_code=404, detail=f"Element '{element_name}' not found")
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/element/{element_name}/label")
async def get_element_label(element_name: str):
    """获取指定元素的标签定义"""
    try:
        label = parser.get_label_definition(element_name)
        if label is None:
            raise HTTPException(status_code=404, detail=f"Label for element '{element_name}' not found")
        return {"element_name": element_name, "label": label}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/element/{element_name}/references")
async def get_element_references(element_name: str):
    """获取指定元素的参考标准"""
    try:
        references = parser.get_reference_standards(element_name)
        if not references:
            raise HTTPException(status_code=404, detail=f"References for element '{element_name}' not found")
        return {"element_name": element_name, "references": references}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/search")
async def search_elements(keyword: str = Query(..., min_length=1), skip: int = 0, limit: int = 100):
    """根据关键字搜索元素"""
    try:
        all_elements = parser.get_all_element_names()
        
        # 根据关键字过滤元素
        filtered_elements = [elem for elem in all_elements if keyword.lower() in elem.lower()]
        
        # 分页处理
        total = len(filtered_elements)
        elements = filtered_elements[skip:skip+limit]
        
        return {
            "keyword": keyword,
            "total": total,
            "skip": skip,
            "limit": limit,
            "elements": elements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# 挂载静态文件目录
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)