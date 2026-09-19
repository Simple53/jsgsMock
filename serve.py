# -*- coding: utf-8 -*-
import http.server
import socketserver
import socket
import os
import sys

# 严格锁定 8080 端口，杜绝端口漂移导致手机连不上
PORT = 8080
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

def get_all_ips():
    ips = set()
    try:
        # 获取主机绑定的所有真实网卡 IP
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            # 过滤回环与虚拟代理 (如 Clash/Mihomo 的 198.18.x.x)
            if not ip.startswith("127.") and not ip.startswith("169.254.") and not ip.startswith("198.18."):
                ips.add(ip)
    except Exception:
        pass

    try:
        # UDP 路由探测主网卡 IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        primary = s.getsockname()[0]
        if primary and not primary.startswith("127.") and not primary.startswith("198.18."):
            ips.add(primary)
        s.close()
    except Exception:
        pass

    res = sorted(list(ips))
    if not res:
        res.append("127.0.0.1")
    return res

# 纯净的 SimpleHTTPRequestHandler，不改写 headers，杜绝 RemoteDisconnected 异常
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    ips = get_all_ips()

    print("=" * 60)
    print("  file2quiz 移动端刷题助手服务已就绪！")
    print("=" * 60)
    print("  电脑本机访问:  http://localhost:%d" % PORT)
    print("  手机局域网/Wi-Fi 请访问:")
    for ip in ips:
        print("     👉 http://%s:%d" % (ip, PORT))
    print("=" * 60)
    print("  提示: 手机浏览器输入时请务必使用 http:// ，严禁带 s")
    print("  按 Ctrl + C 即可停止服务。\n")

    # 允许端口快速重用，绑定所有网络接口 ("")
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()
    except OSError as e:
        if "10048" in str(e):
            print("\n[错误] 端口 %d 已被占用！" % PORT)
            print("请先关闭之前开启的命令行窗口或杀掉占用 8080 端口的 Python 进程后重试。")
        else:
            print("\n服务启动异常:", e)
    except KeyboardInterrupt:
        print("\n服务器已正常退出。")

if __name__ == "__main__":
    main()
