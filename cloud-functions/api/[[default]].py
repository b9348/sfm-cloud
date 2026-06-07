"""
Cloud Functions 默认路由处理器
处理所有 API 请求并路由到对应的处理函数
"""
import json
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

# 导入各个路由处理器
from auth.register import handler as RegisterHandler
from auth.login import handler as LoginHandler

class handler:
    def do_GET(self):
        """处理 GET 请求"""
        path = self.path
        
        # Mod 列表
        if path.startswith('/api/mods/list') or path == '/api/mods':
            from mods.list import handler as ListHandler
            h = ListHandler()
            h.rfile = self.rfile
            h.wfile = self.wfile
            h.headers = self.headers
            h.path = self.path
            h.do_GET()
            return
        
        # Mod 详情
        if path.startswith('/api/mods/detail/'):
            from mods.detail import handler as DetailHandler
            h = DetailHandler()
            h.rfile = self.rfile
            h.wfile = self.wfile
            h.headers = self.headers
            h.path = self.path
            h.do_GET()
            return
        
        # 用户资料
        if path == '/api/user/profile':
            from user.profile import handler as ProfileHandler
            h = ProfileHandler()
            h.rfile = self.rfile
            h.wfile = self.wfile
            h.headers = self.headers
            h.path = self.path
            h.do_GET()
            return
        
        # 404
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "message": "API endpoint not found"}).encode())
    
    def do_POST(self):
        """处理 POST 请求"""
        path = self.path
        
        # 注册
        if path == '/api/auth/register':
            h = RegisterHandler()
            h.rfile = self.rfile
            h.wfile = self.wfile
            h.headers = self.headers
            h.path = self.path
            h.do_POST()
            return
        
        # 登录
        if path == '/api/auth/login':
            h = LoginHandler()
            h.rfile = self.rfile
            h.wfile = self.wfile
            h.headers = self.headers
            h.path = self.path
            h.do_POST()
            return
        
        # 创建 Mod
        if path == '/api/mods/create':
            from mods.create import handler as CreateHandler
            h = CreateHandler()
            h.rfile = self.rfile
            h.wfile = self.wfile
            h.headers = self.headers
            h.path = self.path
            h.do_POST()
            return
        
        # 404
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "message": "API endpoint not found"}).encode())
