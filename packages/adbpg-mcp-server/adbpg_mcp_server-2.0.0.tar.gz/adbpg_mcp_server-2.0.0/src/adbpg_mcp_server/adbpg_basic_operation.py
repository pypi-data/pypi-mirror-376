# mcp_server/basic_operation.py
import psycopg
import logging
from pydantic import AnyUrl
from mcp.types import Resource, ResourceTemplate, Tool
from .adbpg import DatabaseManager
from typing import Tuple


logger = logging.getLogger(__name__)

async def list_resources() -> list[Resource]:
    """列出可用的基本资源"""
    return [
        Resource(
            uri="adbpg:///schemas",
            name="All Schemas",
            description="AnalyticDB PostgreSQL schemas. List all schemas in the database",
            mimeType="text/plain"
        )
    ]

async def list_resource_templates() -> list[ResourceTemplate]:
    """定义动态资源模板"""
    return [
        ResourceTemplate(
            uriTemplate="adbpg:///{schema}/tables",
            name="Schema Tables",
            description="List all tables in a specific schema",
            mimeType="text/plain"
        ),
        ResourceTemplate(
            uriTemplate="adbpg:///{schema}/{table}/ddl",
            name="Table DDL",
            description="Get the DDL script of a table in a specific schema",
            mimeType="text/plain"
        ),
        ResourceTemplate(
            uriTemplate="adbpg:///{schema}/{table}/statistics",
            name="Table Statistics",
            description="Get statistics information of a table",
            mimeType="text/plain"
        )
    ]

async def read_resource(uri: AnyUrl, db: DatabaseManager) -> str:
    """读取资源内容"""
    uri_str = str(uri)
    if not uri_str.startswith("adbpg:///"):
        raise ValueError(f"Invalid URI scheme: {uri_str}")

    try:
        conn = db.get_basic_connection()
        with conn.cursor() as cursor:
            path_parts = uri_str[9:].split('/')
            
            if path_parts[0] == "schemas":
                query = "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog', 'information_schema') ORDER BY schema_name;"
                cursor.execute(query)
                return "\n".join([schema[0] for schema in cursor.fetchall()])
                
            elif len(path_parts) == 2 and path_parts[1] == "tables":
                schema = path_parts[0]
                query = "SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = %s ORDER BY table_name;"
                cursor.execute(query, (schema,))
                return "\n".join([f"{table[0]} ({table[1]})" for table in cursor.fetchall()])
                
            elif len(path_parts) == 3 and path_parts[2] == "ddl":
                schema, table = path_parts[0], path_parts[1]
                query = f"SELECT pg_get_ddl('{schema}.{table}'::regclass);"
                cursor.execute(query)
                ddl = cursor.fetchone()
                return ddl[0] if ddl else f"No DDL found for {schema}.{table}"
                
            elif len(path_parts) == 3 and path_parts[2] == "statistics":
                schema, table = path_parts[0], path_parts[1]
                query = "SELECT attname, null_frac, avg_width, n_distinct, most_common_vals, most_common_freqs FROM pg_stats WHERE schemaname = %s AND tablename = %s ORDER BY attname;"
                cursor.execute(query, (schema, table))
                rows = cursor.fetchall()
                if not rows: return f"No statistics found for {schema}.{table}"
                
                result = [f"Statistics for {schema}.{table}:\n"]
                for row in rows:
                    result.append(f"Column: {row[0]}, Null fraction: {row[1]}, Avg width: {row[2]}, Distinct values: {row[3]}")
                return "\n".join(result)
            
            raise ValueError(f"Invalid resource URI format: {uri_str}")
  
    except psycopg.Error as e:
        logger.error(f"Database error in read_resource: {e}")
        raise RuntimeError(f"Database error: {str(e)}")

def get_basic_tools() -> list[Tool]:
    """返回基础数据库操作工具列表"""
    return [
        Tool(
            name="execute_select_sql",
            description="Execute SELECT SQL to query data from ADBPG database. Returns data in JSON format.",
            inputSchema={ "type": "object", "properties": {"query": {"type": "string", "description": "The (SELECT) SQL query to execute"}}, "required": ["query"]}
        ),
        Tool(
            name="execute_dml_sql",
            description="Execute (INSERT, UPDATE, DELETE) SQL to modify data in ADBPG database.",
            inputSchema={ "type": "object", "properties": {"query": {"type": "string", "description": "The DML SQL query to execute"}}, "required": ["query"]}
        ),
        Tool(
            name="execute_ddl_sql",
            description="Execute (CREATE, ALTER, DROP) SQL statements to manage database objects.",
            inputSchema={ "type": "object", "properties": {"query": {"type": "string", "description": "The DDL SQL query to execute"}}, "required": ["query"]}
        ),
        Tool(
            name="analyze_table",
            description="Execute ANALYZE command to collect table statistics.",
            inputSchema={ "type": "object", "properties": {"schema": {"type": "string"}, "table": {"type": "string"}}, "required": ["schema", "table"]}
        ),
        Tool(
            name="explain_query",
            description="Get query execution plan.",
            inputSchema={ "type": "object", "properties": {"query": {"type": "string", "description": "The SQL query to analyze"}}, "required": ["query"]}
        ),
    ]

async def call_basic_tool(name: str, arguments: dict, db: DatabaseManager) -> Tuple[str, dict, bool]:
    """
    准备执行基础工具的SQL和参数。
    返回 (query_string, params, needs_json_agg)
    """
    query, params, needs_json_agg = None, None, False
    
    if name == "execute_select_sql":
        query_text = arguments.get("query")
        if not query_text or not query_text.strip().upper().startswith("SELECT"):
            raise ValueError("Query must be a SELECT statement")
        query = f"SELECT json_agg(row_to_json(t)) FROM ({query_text.rstrip(';')}) AS t"
        needs_json_agg = True
    elif name == "execute_dml_sql":
        query = arguments.get("query")
        if not query or not any(query.strip().upper().startswith(k) for k in ["INSERT", "UPDATE", "DELETE"]):
            raise ValueError("Query must be a DML statement (INSERT, UPDATE, DELETE)")
    elif name == "execute_ddl_sql":
        query = arguments.get("query")
        if not query or not any(query.strip().upper().startswith(k) for k in ["CREATE", "ALTER", "DROP", "TRUNCATE"]):
            raise ValueError("Query must be a DDL statement (CREATE, ALTER, DROP)")
    elif name == "analyze_table":
        schema, table = arguments.get("schema"), arguments.get("table")
        if not all([schema, table]):
            raise ValueError("Schema and table are required")
        query = f"ANALYZE {schema}.{table}"
    elif name == "explain_query":
        query_text = arguments.get("query")
        if not query_text:
            raise ValueError("Query is required")
        query = f"EXPLAIN (FORMAT JSON) {query_text}"
        needs_json_agg = True # The output is already a single JSON value in a single row

    if query is None:
        raise ValueError(f"Unknown basic tool: {name}")

    return (query, params, needs_json_agg)

