import http.server
import socketserver
import socket
import os
import sys

PORT = 8080
DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

def get_all_ips():
    ips = []
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass
    if not ips:
        ips.append("127.0.0.1")
    return ips

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def main():
    os.chdir(os.path.dirname(__file__))
    ips = get_all_ips()

    print("=" * 60)
    print("  🚀 考点刷题助手（移动端 PWA）已启动！")
    print("=" * 60)
    print(f"  💻 电脑浏览器直接访问:  http://localhost:{PORT}")
    print("  📱 手机在同一 WiFi 下可访问下列地址之一:")
    for ip in ips:
        print(f"     👉 http://{ip}:{PORT}")
    print("=" * 60)
    print("  💡 手机最佳体验技巧:")
    print("  1. 手机自带浏览器打开上述网址")
    print("  2. 点击浏览器菜单【添加到主屏幕】，即生成独立无框 App！")
    print("=" * 60)
    print("  按 Ctrl + C 可退出服务器。\n")

    # 允许端口快速重用
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止。")

if __name__ == "__main__":
    main()
