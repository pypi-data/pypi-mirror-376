#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云百炼 MCP 服务器 - MySQL 业务查询服务
支持HTTP传输协议，提供7个业务查询工具
"""

import os
import asyncio
import logging
from typing import Any, Dict, List, Optional
import pymysql
from fastmcp import FastMCP

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 FastMCP 服务
mcp = FastMCP(
    service_name=os.getenv("MCP_SERVICE_NAME", "licai_mysql_mcp"),
    description="理财业务MySQL查询服务 - 提供用户、课程、订单等业务数据查询"
)

class MySQLConnection:
    """MySQL连接管理器"""
    
    def __init__(self):
        self.host = os.getenv("MYSQL_HOST", "localhost")
        self.port = int(os.getenv("MYSQL_PORT", "3306"))
        self.user = os.getenv("MYSQL_USER", "root")
        self.password = os.getenv("MYSQL_PASSWORD", "")
        self.databases = os.getenv("MYSQL_DATABASES", "").split(",")
        
    def get_connection(self):
        """获取MySQL连接"""
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            return connection
        except Exception as e:
            logger.error(f"MySQL连接失败: {e}")
            raise

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """执行SQL查询"""
        connection = None
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                cursor.execute(sql)
                results = cursor.fetchall()
                return list(results) if results else []
        except Exception as e:
            logger.error(f"SQL执行失败: {sql}, 错误: {e}")
            raise
        finally:
            if connection:
                connection.close()

# 全局MySQL连接管理器
mysql_manager = MySQLConnection()

@mcp.tool()
def get_user_info(user_id: int) -> Dict[str, Any]:
    """
    获取用户基本信息
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户基本信息，包含中文字段名
    """
    sql = f"""
    SELECT 
        u.id as '用户ID',
        u.username as '用户名',
        u.email as '邮箱',
        u.phone as '手机号',
        u.real_name as '真实姓名',
        u.created_at as '注册时间',
        p.nickname as '昵称',
        p.avatar as '头像',
        p.gender as '性别'
    FROM sso.users u
    LEFT JOIN sso.user_profiles p ON u.id = p.user_id
    WHERE u.id = {user_id}
    """
    
    try:
        results = mysql_manager.execute_query(sql)
        return {
            "success": True,
            "data": results,
            "message": f"成功获取用户ID {user_id} 的信息"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"查询失败: {str(e)}"
        }

@mcp.tool()
def get_user_courses(user_id: int) -> Dict[str, Any]:
    """
    获取用户购买的课程列表
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户课程列表，包含中文字段名
    """
    sql = f"""
    SELECT 
        c.id as '课程ID',
        c.title as '课程标题',
        c.description as '课程描述',
        c.price as '课程价格',
        c.status as '课程状态',
        uc.purchase_time as '购买时间',
        uc.progress as '学习进度',
        uc.status as '学习状态'
    FROM dpt_e-commerce.user_courses uc
    JOIN dpt_e-commerce.courses c ON uc.course_id = c.id
    WHERE uc.user_id = {user_id}
    ORDER BY uc.purchase_time DESC
    """
    
    try:
        results = mysql_manager.execute_query(sql)
        return {
            "success": True,
            "data": results,
            "message": f"成功获取用户ID {user_id} 的课程列表"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"查询失败: {str(e)}"
        }

@mcp.tool()
def get_user_cases(user_id: int) -> Dict[str, Any]:
    """
    获取用户的案例分析记录
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户案例列表，包含中文字段名
    """
    sql = f"""
    SELECT 
        ca.id as '案例ID',
        ca.title as '案例标题',
        ca.content as '案例内容',
        ca.analysis_result as '分析结果',
        ca.created_at as '创建时间',
        ca.status as '案例状态',
        c.title as '关联课程'
    FROM dpt_e-commerce.case_analysis ca
    LEFT JOIN dpt_e-commerce.courses c ON ca.course_id = c.id
    WHERE ca.user_id = {user_id}
    ORDER BY ca.created_at DESC
    """
    
    try:
        results = mysql_manager.execute_query(sql)
        return {
            "success": True,
            "data": results,
            "message": f"成功获取用户ID {user_id} 的案例分析记录"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"查询失败: {str(e)}"
        }

@mcp.tool()
def get_user_orders(user_id: int) -> Dict[str, Any]:
    """
    获取用户的订单信息
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户订单列表，包含中文字段名
    """
    sql = f"""
    SELECT 
        o.id as '订单ID',
        o.order_no as '订单号',
        o.total_amount as '订单金额',
        o.status as '订单状态',
        o.created_at as '下单时间',
        o.paid_at as '支付时间',
        oi.goods_name as '商品名称',
        oi.price as '商品价格',
        oi.quantity as '购买数量'
    FROM dpt_e-commerce.orders o
    LEFT JOIN dpt_e-commerce.order_items oi ON o.id = oi.order_id
    WHERE o.user_id = {user_id}
    ORDER BY o.created_at DESC
    """
    
    try:
        results = mysql_manager.execute_query(sql)
        return {
            "success": True,
            "data": results,
            "message": f"成功获取用户ID {user_id} 的订单信息"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"查询失败: {str(e)}"
        }

@mcp.tool()
def get_user_invoices(user_id: int) -> Dict[str, Any]:
    """
    获取用户的发票信息
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户发票列表，包含中文字段名
    """
    sql = f"""
    SELECT 
        i.id as '发票ID',
        i.invoice_no as '发票号码',
        i.title as '发票抬头',
        i.tax_no as '税号',
        i.amount as '发票金额',
        i.status as '发票状态',
        i.created_at as '申请时间',
        i.issued_at as '开具时间',
        o.order_no as '关联订单号'
    FROM dpt_e-commerce.invoices i
    LEFT JOIN dpt_e-commerce.orders o ON i.order_id = o.id
    WHERE i.user_id = {user_id}
    ORDER BY i.created_at DESC
    """
    
    try:
        results = mysql_manager.execute_query(sql)
        return {
            "success": True,
            "data": results,
            "message": f"成功获取用户ID {user_id} 的发票信息"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"查询失败: {str(e)}"
        }

@mcp.tool()
def get_user_study_plans(user_id: int) -> Dict[str, Any]:
    """
    获取用户的学习计划
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户学习计划列表，包含中文字段名
    """
    sql = f"""
    SELECT 
        sp.id as '计划ID',
        sp.title as '计划标题',
        sp.description as '计划描述',
        sp.start_date as '开始日期',
        sp.end_date as '结束日期',
        sp.status as '计划状态',
        sp.progress as '完成进度',
        c.title as '关联课程'
    FROM dpt_e-commerce.study_plans sp
    LEFT JOIN dpt_e-commerce.courses c ON sp.course_id = c.id
    WHERE sp.user_id = {user_id}
    ORDER BY sp.created_at DESC
    """
    
    try:
        results = mysql_manager.execute_query(sql)
        return {
            "success": True,
            "data": results,
            "message": f"成功获取用户ID {user_id} 的学习计划"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"查询失败: {str(e)}"
        }

@mcp.tool()
def get_course_study_plans(course_id: int) -> Dict[str, Any]:
    """
    获取指定课程的学习计划模板
    
    Args:
        course_id: 课程ID
        
    Returns:
        课程学习计划列表，包含中文字段名
    """
    sql = f"""
    SELECT 
        sp.id as '计划ID',
        sp.title as '计划标题',
        sp.description as '计划描述',
        sp.duration_days as '计划天数',
        sp.difficulty_level as '难度等级',
        sp.created_at as '创建时间',
        c.title as '课程名称',
        c.description as '课程描述'
    FROM dpt_e-commerce.study_plan_templates sp
    JOIN dpt_e-commerce.courses c ON sp.course_id = c.id
    WHERE sp.course_id = {course_id}
    ORDER BY sp.difficulty_level, sp.created_at
    """
    
    try:
        results = mysql_manager.execute_query(sql)
        return {
            "success": True,
            "data": results,
            "message": f"成功获取课程ID {course_id} 的学习计划模板"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"查询失败: {str(e)}"
        }

@mcp.tool()
def health_check() -> Dict[str, Any]:
    """
    健康检查接口
    
    Returns:
        服务状态信息
    """
    try:
        # 测试数据库连接
        mysql_manager.execute_query("SELECT 1 as test")
        
        return {
            "success": True,
            "service": "licai_mysql_mcp",
            "status": "healthy",
            "database": "connected",
            "message": "服务运行正常"
        }
    except Exception as e:
        return {
            "success": False,
            "service": "licai_mysql_mcp",
            "status": "unhealthy",
            "database": "disconnected",
            "message": f"数据库连接失败: {str(e)}"
        }

if __name__ == "__main__":
    # 启动服务
    port = int(os.getenv("MCP_SERVICE_PORT", "8001"))
    logger.info(f"启动理财MySQL MCP服务，端口: {port}")
    
    # 运行FastMCP服务
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port
    )

def main():
    """入口函数"""
    # 启动服务
    port = int(os.getenv("MCP_SERVICE_PORT", "8001"))
    logger.info(f"启动理财MySQL MCP服务，端口: {port}")
    
    # 运行FastMCP服务
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port
    )

if __name__ == "__main__":
    main()
