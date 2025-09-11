#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于MySQL数据库的MCP服务器
使用标准MCP stdio协议实现，连接MySQL数据库
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List
from datetime import datetime

import pymysql
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MySQL数据库配置 - 支持跨库查询
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    # 不指定默认数据库，支持跨库查询
    'charset': 'utf8mb4',
    'autocommit': True
}

# 支持的数据库列表（从环境变量读取，用逗号分隔）
DATABASES = os.getenv('MYSQL_DATABASES', 'dpt_e-commerce,sso').split(',')
logger.info(f"📚 支持的数据库: {DATABASES}")

class MySQLManager:
    """MySQL数据库管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.test_connection()
    
    def get_connection(self):
        """获取MySQL连接"""
        try:
            connection = pymysql.connect(**self.config)
            return connection
        except Exception as e:
            logger.error(f"❌ MySQL连接失败: {str(e)}")
            raise
    
    def test_connection(self):
        """测试数据库连接"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            logger.info("✅ MySQL连接测试成功")
        except Exception as e:
            logger.error(f"❌ MySQL连接测试失败: {str(e)}")
            raise
    
    def get_user_info_by_mobile(self, mobile: str) -> Dict[str, Any]:
        """根据手机号查询用户基本信息"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    u.userId as 用户ID,
                    u.nickname as 用户昵称,
                    u.regdate as 注册日期,
                    u.mobile_status as 手机状态,
                    u.mobile_areacode as 手机区号
                FROM sso.sso_user_new u
                LEFT JOIN sso.sso_user_rela r on r.id=u.userId
                WHERE u.mobile=concat("hash0_",SHA2(%s, 256)) 
                AND r.reg_sys="NLCW"
            ''', (mobile,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                user_data = {
                    "用户ID": row[0],
                    "用户昵称": row[1],
                    "注册日期": str(row[2]) if row[2] else None,
                    "手机状态": row[3],
                    "手机区号": row[4]
                }
                return {
                    "success": True,
                    "data": user_data,
                    "message": f"成功查询手机号 {mobile} 的用户信息"
                }
            else:
                return {
                    "success": False,
                    "error": f"未找到手机号为 {mobile} 的用户"
                }
                
        except Exception as e:
            logger.error(f"❌ 根据手机号查询用户失败: {str(e)}")
            return {"success": False, "error": f"MySQL查询失败: {str(e)}"}
    
    def get_user_info_by_nickname(self, nickname: str) -> Dict[str, Any]:
        """根据用户名查询用户基本信息"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    u.userId as 用户ID,
                    u.nickname as 用户昵称,
                    u.regdate as 注册日期,
                    u.mobile_status as 手机状态,
                    u.mobile_areacode as 手机区号
                FROM sso.sso_user_new u
                LEFT JOIN sso.sso_user_rela r on r.id=u.userId
                WHERE u.nickname=%s
                AND r.reg_sys="NLCW"
            ''', (nickname,))
            
            rows = cursor.fetchall()
            conn.close()
            
            users = []
            for row in rows:
                user_data = {
                    "用户ID": row[0],
                    "用户昵称": row[1],
                    "注册日期": str(row[2]) if row[2] else None,
                    "手机状态": row[3],
                    "手机区号": row[4]
                }
                users.append(user_data)
            
            return {
                "success": True,
                "data": users,
                "total": len(users),
                "message": f"找到 {len(users)} 个昵称为 '{nickname}' 的用户"
            }
            
        except Exception as e:
            logger.error(f"❌ 根据用户名查询用户失败: {str(e)}")
            return {"success": False, "error": f"MySQL查询失败: {str(e)}"}
    
    def get_user_courses(self, user_id: int) -> Dict[str, Any]:
        """查询用户的课程"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    g.NAME as 商品名称,
                    l.goods_id as 商品ID,
                    l.stime as 开始时间,
                    l.lesson_status as 课程状态,
                    l.etime as 结束时间,
                    l.renew_time as 续费时间
                FROM `dpt_e-commerce`.study_manage_lesson l 
                LEFT JOIN `dpt_e-commerce`.goods g on g.id=l.goods_id
                WHERE l.uid=%s
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            courses = []
            for row in rows:
                course_data = {
                    "商品名称": row[0],
                    "商品ID": row[1],
                    "开始时间": str(row[2]) if row[2] else None,
                    "课程状态": row[3],
                    "结束时间": str(row[4]) if row[4] else None,
                    "续费时间": str(row[5]) if row[5] else None
                }
                courses.append(course_data)
            
            return {
                "success": True,
                "data": courses,
                "total": len(courses),
                "user_id": user_id,
                "message": f"用户 {user_id} 共有 {len(courses)} 个课程"
            }
            
        except Exception as e:
            logger.error(f"❌ 查询用户课程失败: {str(e)}")
            return {"success": False, "error": f"MySQL查询失败: {str(e)}"}
    
    def get_user_cases(self, user_id: int) -> Dict[str, Any]:
        """查询用户的案例"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    g.NAME as 商品名称,
                    l.case_id as 案例ID,
                    l.uploadtime as 上传时间,
                    l.knowname as 知识点名称,
                    d.grade as 成绩
                FROM `dpt_e-commerce`.study_manage_case l
                LEFT JOIN `dpt_e-commerce`.study_manage_case_details d on d.case_id=l.case_id
                LEFT JOIN `dpt_e-commerce`.goods g on g.id=l.goodsid
                WHERE l.userid=%s
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            cases = []
            for row in rows:
                case_data = {
                    "商品名称": row[0],
                    "案例ID": row[1],
                    "上传时间": str(row[2]) if row[2] else None,
                    "知识点名称": row[3],
                    "成绩": row[4]
                }
                cases.append(case_data)
            
            return {
                "success": True,
                "data": cases,
                "total": len(cases),
                "user_id": user_id,
                "message": f"用户 {user_id} 共有 {len(cases)} 个案例"
            }
            
        except Exception as e:
            logger.error(f"❌ 查询用户案例失败: {str(e)}")
            return {"success": False, "error": f"MySQL查询失败: {str(e)}"}
    
    def get_user_orders(self, user_id: int) -> Dict[str, Any]:
        """查询用户的订单"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    g.`name` as 商品名称,
                    o.ORDER_TIME as 下单时间,
                    o.ORDER_NUMBER as 订单号,
                    o.ORDER_STATUS as 订单状态,
                    o.totalAmt as 订单总金额,
                    o.discountAmt as 折扣金额,
                    o.REAL_PAY as 实付金额,
                    o.couponsAmt as 优惠券金额,
                    o.point as 积分,
                    go.PRICE as 商品价格,
                    go.`STATUS` as 商品状态
                FROM `dpt_e-commerce`.orders o
                LEFT JOIN `dpt_e-commerce`.goods_orders go on go.ORDERID=o.ID
                LEFT JOIN `dpt_e-commerce`.goods g on g.id=go.GOODSID
                WHERE o.userid=%s AND o.sys="NLCW" 
                ORDER BY o.PAY_TIME DESC LIMIT 5
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            orders = []
            for row in rows:
                order_data = {
                    "商品名称": row[0],
                    "下单时间": str(row[1]) if row[1] else None,
                    "订单号": row[2],
                    "订单状态": row[3],
                    "订单总金额": float(row[4]) if row[4] else 0,
                    "折扣金额": float(row[5]) if row[5] else 0,
                    "实付金额": float(row[6]) if row[6] else 0,
                    "优惠券金额": float(row[7]) if row[7] else 0,
                    "积分": row[8],
                    "商品价格": float(row[9]) if row[9] else 0,
                    "商品状态": row[10]
                }
                orders.append(order_data)
            
            return {
                "success": True,
                "data": orders,
                "total": len(orders),
                "user_id": user_id,
                "message": f"用户 {user_id} 最近5个订单"
            }
            
        except Exception as e:
            logger.error(f"❌ 查询用户订单失败: {str(e)}")
            return {"success": False, "error": f"MySQL查询失败: {str(e)}"}
    
    def get_user_invoices(self, user_id: int) -> Dict[str, Any]:
        """查询用户的订单以及发票金额"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    g.`name` as 商品名称,
                    o.totalAmt as 订单总金额,
                    o.discountAmt as 折扣金额,
                    o.REAL_PAY as 实付金额,
                    o.couponsAmt as 优惠券金额,
                    o.point as 积分,
                    t.`status` as 发票状态,
                    t.invoiceAmount as 发票金额
                FROM `dpt_e-commerce`.orders o
                LEFT JOIN `dpt_e-commerce`.goods_orders go on go.ORDERID=o.ID
                LEFT JOIN `dpt_e-commerce`.t_invoice t on t.orderNo=o.ORDER_NUMBER
                LEFT JOIN `dpt_e-commerce`.goods g on g.id=go.GOODSID
                WHERE o.userid=%s 
                AND o.sys="NLCW"
                AND go.`STATUS`=0
                GROUP BY o.id
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            invoices = []
            for row in rows:
                invoice_data = {
                    "商品名称": row[0],
                    "订单总金额": float(row[1]) if row[1] else 0,
                    "折扣金额": float(row[2]) if row[2] else 0,
                    "实付金额": float(row[3]) if row[3] else 0,
                    "优惠券金额": float(row[4]) if row[4] else 0,
                    "积分": row[5],
                    "发票状态": row[6],
                    "发票金额": float(row[7]) if row[7] else 0
                }
                invoices.append(invoice_data)
            
            return {
                "success": True,
                "data": invoices,
                "total": len(invoices),
                "user_id": user_id,
                "message": f"用户 {user_id} 共有 {len(invoices)} 个订单发票记录"
            }
            
        except Exception as e:
            logger.error(f"❌ 查询用户发票失败: {str(e)}")
            return {"success": False, "error": f"MySQL查询失败: {str(e)}"}
    
    def get_user_study_plan_stats(self, user_id: int) -> Dict[str, Any]:
        """查询统计用户加分计划的总数据"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT
                    aa.userid as 用户ID,
                    aa.truename as 真实姓名,
                    cardnum as 身份证号,
                    SUM(bxclassHour) as 必修累计学时,
                    SUM(yxclassHour) as 选修累计学时,
                    SUM(classHour) as 总累计学时,
                    SUM(study_status) as 通过周数,
                    passQuestionNum as 通过题目数,
                    aa.caseGrade as 案例成绩,
                    (SELECT COUNT(DISTINCT t2.testid) 
                     FROM study_manage_test t2 
                     WHERE t2.userId=aa.userId AND t2.goodsId=aa.goods_id AND t2.grade>=60
                     AND t2.testtype=1) as 测试通过数量,
                    t2.ctime as 创建时间,
                    t2.end_time as 结束时间,
                    s2.score as 分数
                FROM (
                    SELECT
                        u.userId,d.goods_id,
                        t.week_start,t.week_end,
                        u.truename,
                        u.cardnum,
                        ROUND(SUM(IF(t.week_start <=d.end_time and d.end_time<=t.week_end and s.is_required=1 ,total_playtime,0))/60/45,2) bxclassHour,
                        ROUND(SUM(IF(t.week_start <=d.end_time and d.end_time<=t.week_end and s.is_required=2 ,total_playtime,0))/60/45,2) yxclassHour,
                        ROUND(SUM(IF(t.week_start <=d.end_time and d.end_time<=t.week_end   ,total_playtime,0))/60/45,2)  classHour,
                        IF(ROUND(SUM(IF(t.week_start <=d.end_time and d.end_time<=t.week_end ,total_playtime,0))/60/45,2)>5,1,0) study_status,
                        passQuestionNum,d2.grade as caseGrade,
                        s.is_required 
                    FROM
                        `dpt_e-commerce`.`study_plan_week` t
                        LEFT JOIN  `dpt_e-commerce`.study_plan_checkrecord d on t.userid = d.user_id and t.goodsId = d.goods_id    and d.know_id>0
                        LEFT JOIN `dpt_e-commerce`. study_plan_dict s on d.know_id = s.relation_id and type = 3 
                        LEFT JOIN  sso.sso_user_new u on 	t.userid = u.userId
                        LEFT JOIN  `dpt_e-commerce`.study_plan_test te on t.userId = te.userId and t.goodsId = te.goodsId
                        LEFT JOIN `dpt_e-commerce`.study_manage_case c on c.userid=d.user_id and c.goodsid=d.goods_id
                        LEFT JOIN `dpt_e-commerce`.study_manage_case_details d2 on d2.case_id=c.case_id
                    WHERE  u.userId = %s
                    AND	d.check_result in (1,4)
                    GROUP BY u.userid,t.id   
                ) aa 
                LEFT JOIN `dpt_e-commerce`.study_plan_time t2 on t2.userId=aa.userId
                LEFT JOIN `dpt_e-commerce`.study_plan_fpsb_score_record s2 on s2.userid=aa.userId
                GROUP BY cardnum
                ORDER BY cardnum
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                stats_data = {
                    "用户ID": row[0],
                    "真实姓名": row[1],
                    "身份证号": row[2],
                    "必修累计学时": float(row[3]) if row[3] else 0,
                    "选修累计学时": float(row[4]) if row[4] else 0,
                    "总累计学时": float(row[5]) if row[5] else 0,
                    "通过周数": row[6] if row[6] else 0,
                    "通过题目数": row[7] if row[7] else 0,
                    "案例成绩": row[8] if row[8] else 0,
                    "测试通过数量": row[9] if row[9] else 0,
                    "创建时间": str(row[10]) if row[10] else None,
                    "结束时间": str(row[11]) if row[11] else None,
                    "分数": row[12] if row[12] else 0,
                    "加分计划要求": {
                        "必修累计总学时要求": ">=30",
                        "周完成要求": "5学时/周，>=4周",
                        "作业要求": ">30",
                        "案例要求": "完成案例",
                        "测试要求": "通过60题考核"
                    }
                }
                return {
                    "success": True,
                    "data": stats_data,
                    "user_id": user_id,
                    "message": f"用户 {user_id} 的加分计划统计数据"
                }
            else:
                return {
                    "success": False,
                    "error": f"未找到用户 {user_id} 的加分计划数据"
                }
            
        except Exception as e:
            logger.error(f"❌ 查询用户加分计划统计失败: {str(e)}")
            return {"success": False, "error": f"MySQL查询失败: {str(e)}"}

# 创建MySQL管理器实例
try:
    mysql_manager = MySQLManager(MYSQL_CONFIG)
    logger.info(f"✅ 连接到MySQL服务器: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
    logger.info(f"📚 支持跨库查询: {', '.join(DATABASES)}")
except Exception as e:
    logger.error(f"❌ MySQL连接失败: {str(e)}")
    logger.info("💡 请检查MySQL配置和连接信息")
    exit(1)

# 创建MCP服务器实例
server = Server("alibaba-bailian-mysql-service")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="get_user_info_by_mobile",
            description="根据手机号查询用户基本信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "mobile": {
                        "type": "string",
                        "description": "用户手机号"
                    }
                },
                "required": ["mobile"]
            }
        ),
        Tool(
            name="get_user_info_by_nickname",
            description="根据用户名查询用户基本信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "nickname": {
                        "type": "string",
                        "description": "用户昵称"
                    }
                },
                "required": ["nickname"]
            }
        ),
        Tool(
            name="get_user_courses",
            description="查询用户的课程信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "用户ID"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_user_cases",
            description="查询用户的案例信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "用户ID"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_user_orders",
            description="查询用户的订单信息（最近5个）",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "用户ID"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_user_invoices",
            description="查询用户的订单及发票信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "用户ID"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_user_study_plan_stats",
            description="查询用户加分计划的统计数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "用户ID"
                    }
                },
                "required": ["user_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""
    logger.info(f"🛠️ 调用MySQL工具: {name}, 参数: {arguments}")
    
    try:
        if name == "get_user_info_by_mobile":
            mobile = arguments.get("mobile")
            if not mobile:
                result = {"success": False, "error": "缺少必需参数: mobile"}
            else:
                result = mysql_manager.get_user_info_by_mobile(mobile)
        
        elif name == "get_user_info_by_nickname":
            nickname = arguments.get("nickname")
            if not nickname:
                result = {"success": False, "error": "缺少必需参数: nickname"}
            else:
                result = mysql_manager.get_user_info_by_nickname(nickname)
        
        elif name == "get_user_courses":
            user_id = arguments.get("user_id")
            if not user_id:
                result = {"success": False, "error": "缺少必需参数: user_id"}
            else:
                result = mysql_manager.get_user_courses(int(user_id))
        
        elif name == "get_user_cases":
            user_id = arguments.get("user_id")
            if not user_id:
                result = {"success": False, "error": "缺少必需参数: user_id"}
            else:
                result = mysql_manager.get_user_cases(int(user_id))
        
        elif name == "get_user_orders":
            user_id = arguments.get("user_id")
            if not user_id:
                result = {"success": False, "error": "缺少必需参数: user_id"}
            else:
                result = mysql_manager.get_user_orders(int(user_id))
        
        elif name == "get_user_invoices":
            user_id = arguments.get("user_id")
            if not user_id:
                result = {"success": False, "error": "缺少必需参数: user_id"}
            else:
                result = mysql_manager.get_user_invoices(int(user_id))
        
        elif name == "get_user_study_plan_stats":
            user_id = arguments.get("user_id")
            if not user_id:
                result = {"success": False, "error": "缺少必需参数: user_id"}
            else:
                result = mysql_manager.get_user_study_plan_stats(int(user_id))
        
        else:
            result = {"success": False, "error": f"未知工具: {name}"}
        
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"❌ 工具调用异常: {str(e)}")
        error_result = {"success": False, "error": f"工具执行异常: {str(e)}"}
        return [TextContent(
            type="text",
            text=json.dumps(error_result, ensure_ascii=False, indent=2)
        )]

async def main():
    """启动MCP服务器"""
    logger.info("🚀 启动连接现有MySQL数据库的MCP服务")
    logger.info(f"🗄️ 连接到: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
    logger.info(f"📚 支持数据库: {', '.join(DATABASES)}")
    logger.info("🔧 使用stdio协议")
    logger.info("🛠️ 可用工具: 7 个 (基于真实业务SQL查询)")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())