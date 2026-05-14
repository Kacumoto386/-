"""
API服务器 - 轻量级HTTP服务器
用Python标准库 http.server 实现，无外部依赖
支持 JSON 请求/响应，为小程序和支付体系提供接口
"""
import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.business import BusinessLayer
from api.routes import ApiRoutes
from api.serializers import api_response


class ApiHandler(BaseHTTPRequestHandler):
    """API HTTP请求处理器"""

    # 类级别共享的业务层和路由
    biz = None
    routes = None

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PUT(self):
        self._handle("PUT")

    def do_DELETE(self):
        self._handle("DELETE")

    def _handle(self, method):
        """处理请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        # 将单值参数提取出来
        params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}

        # 读取请求体
        data = None
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            try:
                body = self.rfile.read(content_length)
                data = json.loads(body)
            except (json.JSONDecodeError, Exception):
                data = None

        try:
            result = self.routes.dispatch(method, path, params=params, data=data)
            self._send_json(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._send_json(api_response(False, message=f"服务器错误: {str(e)}"), status=500)

    def _send_json(self, response, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        body = json.dumps(response, ensure_ascii=False, default=str).encode("utf-8")
        self.wfile.write(body)

    def do_OPTIONS(self):
        """CORS预检请求"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        """自定义日志输出"""
        print(f"[API] {self.command} {self.path} - {args[0]}")


def start_server(host="0.0.0.0", port=8765):
    """启动API服务器"""
    # 确保项目目录在Path中
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    # 初始化业务层
    from config import EXCEL_PATH, PROJECT_NAME, __version__
    ApiHandler.biz = BusinessLayer(EXCEL_PATH)
    ApiHandler.routes = ApiRoutes(ApiHandler.biz)

    server = HTTPServer((host, port), ApiHandler)
    print(f"=" * 50)
    print(f"  {PROJECT_NAME} v{__version__} API Server")
    print(f"  Listening on http://{host}:{port}")
    print(f"=" * 50)
    print(f"  Endpoints:")
    for key in sorted(ApiHandler.routes.routes.keys()):
        print(f"    {key}")
    print(f"=" * 50)
    print(f"  Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        if ApiHandler.biz:
            ApiHandler.biz.save()
        server.server_close()
        print("Server stopped.")


def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description="gym-excel-system API Server")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8765, help="监听端口 (默认 8765)")
    args = parser.parse_args()
    start_server(args.host, args.port)


if __name__ == "__main__":
    main()
