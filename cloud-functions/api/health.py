"""
健康检查 API
GET /api/health
"""
import json
import os
import pymysql
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理 GET 请求"""
        try:
            # 测试数据库连接
            conn = pymysql.connect(
                host=os.environ.get('DB_HOST', 'mysql7.sqlpub.com'),
                port=int(os.environ.get('DB_PORT', '3312')),
                user=os.environ.get('DB_USER', 'sfmmm1'),
                password=os.environ.get('DB_PASSWORD', 'fEPM4xyhL3WAVGYf'),
                database=os.environ.get('DB_NAME', 'sfmmm1'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5
            )
            cursor = conn.cursor()

            # 检查表是否存在
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s
            """, (os.environ.get('DB_NAME', 'sfmmm1'),))
            tables = [row['TABLE_NAME'] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "Database connection successful",
                "tables": tables
            }).encode())

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": f"Database error: {str(e)}",
                "detail": error_detail
            }).encode())
