"""
DDL操作核心实现模块

功能说明：
- 执行CREATE、ALTER、DROP等DDL操作
- 支持本地SQLite和外部数据库
- 自动检测SQL类型，拒绝非DDL操作
- 提供事务支持和错误处理
"""

import sqlite3
import logging
import re
import json
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# 设置日志
logger = logging.getLogger("DataMaster_MCP.DDL")

# DDL操作类型定义
DDL_OPERATIONS = {
    'CREATE': ['CREATE TABLE', 'CREATE INDEX', 'CREATE VIEW', 'CREATE DATABASE'],
    'ALTER': ['ALTER TABLE', 'ALTER DATABASE'],
    'DROP': ['DROP TABLE', 'DROP INDEX', 'DROP VIEW', 'DROP DATABASE'],
    'TRUNCATE': ['TRUNCATE TABLE'],
    'RENAME': ['RENAME TABLE', 'ALTER TABLE RENAME']
}

class DDLExecutor:
    """DDL执行器类"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
    
    def is_ddl_statement(self, sql: str) -> Tuple[bool, str]:
        """
        检测SQL是否为DDL语句
        
        Args:
            sql: SQL语句
            
        Returns:
            (是否为DDL, 操作类型)
        """
        sql_upper = sql.strip().upper()
        
        for operation, patterns in DDL_OPERATIONS.items():
            for pattern in patterns:
                if sql_upper.startswith(pattern.upper()):
                    return True, operation
        
        return False, "UNKNOWN"
    
    def execute_ddl_sqlite(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """在本地SQLite数据库上执行DDL操作"""
        try:
            db_path = self.data_dir / "local_database.db"
            
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 执行DDL操作
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                
                # 获取影响的表信息
                affected_table = self._extract_table_name(query)
                
                return {
                    "status": "success",
                    "message": f"DDL操作执行成功",
                    "operation": "sqlite_ddl",
                    "affected_table": affected_table,
                    "query": query,
                    "row_count": cursor.rowcount
                }
                
        except sqlite3.Error as e:
            logger.error(f"SQLite DDL执行错误: {e}")
            return {
                "status": "error",
                "message": f"SQLite DDL执行失败: {str(e)}",
                "operation": "sqlite_ddl",
                "query": query
            }
    
    def _extract_table_name(self, sql: str) -> Optional[str]:
        """从SQL中提取表名"""
        sql = sql.strip()
        
        # CREATE TABLE
        create_match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)', sql, re.IGNORECASE)
        if create_match:
            return create_match.group(1)
        
        # ALTER TABLE
        alter_match = re.search(r'ALTER\s+TABLE\s+(\w+)', sql, re.IGNORECASE)
        if alter_match:
            return alter_match.group(1)
        
        # DROP TABLE
        drop_match = re.search(r'DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(\w+)', sql, re.IGNORECASE)
        if drop_match:
            return drop_match.group(1)
        
        # CREATE INDEX
        index_match = re.search(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+\w+\s+ON\s+(\w+)', sql, re.IGNORECASE)
        if index_match:
            return index_match.group(1)
        
        return None

def execute_ddl_impl(query: str, params: Optional[Dict[str, Any]] = None, data_source: Optional[str] = None) -> str:
    """
    执行DDL操作的核心实现
    
    Args:
        query: DDL语句
        params: 参数化查询参数
        data_source: 数据源名称，None表示本地SQLite
    
    Returns:
        JSON格式的执行结果
    """
    executor = DDLExecutor()
    
    # 检查是否为DDL语句
    is_ddl, operation_type = executor.is_ddl_statement(query)
    if not is_ddl:
        return json.dumps({
            "status": "error",
            "message": "此工具仅支持DDL操作（CREATE、ALTER、DROP等），请使用其他工具执行查询操作",
            "operation": "ddl_validation",
            "provided_query": query
        }, ensure_ascii=False)
    
    # 本地SQLite执行
    if data_source is None:
        result = executor.execute_ddl_sqlite(query, params)
        return json.dumps(result, ensure_ascii=False)
    
    # 外部数据库执行（需要实现外部数据库连接）
    else:
        return json.dumps({
            "status": "error",
            "message": f"外部数据库 '{data_source}' 的DDL操作暂不支持，请使用本地SQLite数据库",
            "operation": "external_ddl",
            "data_source": data_source
        }, ensure_ascii=False)

# 初始化函数
def init_ddl_module():
    """初始化DDL模块"""
    logger.info("DDL操作模块初始化完成")

if __name__ == "__main__":
    # 测试代码
    init_ddl_module()
    
    # 测试DDL检测
    test_queries = [
        "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)",
        "ALTER TABLE test_table ADD COLUMN age INTEGER",
        "DROP TABLE test_table",
        "SELECT * FROM users",
        "CREATE INDEX idx_name ON test_table(name)"
    ]
    
    executor = DDLExecutor()
    for query in test_queries:
        is_ddl, op_type = executor.is_ddl_statement(query)
        print(f"查询: {query}")
        print(f"是否为DDL: {is_ddl}, 类型: {op_type}")
        print("-" * 50)