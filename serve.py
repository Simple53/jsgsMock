# -*- coding: utf-8 -*-
import http.server
import socketserver
import socket
import subprocess
import os
import sys

DEFAULT_PORT = 8080
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

def get_all_valid_ips():
    valid_ips = set()

    # 方法1: 通过系统原生 UDP socket 探测本机路由 IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        if primary_ip:
            valid_ips.add(primary_ip.strip())
        s.close()
    except Exception:
        pass

    # 方法2: 获取主机名绑定的所有 IP
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip:
                valid_ips.add(ip.strip())
    except Exception:
        pass

    # 方法3: Windows ipconfig 提取所有适配器真实 IPv4 (支持 Windows 移动热点 192.168.137.1)
    try:
        res = subprocess.run(["ipconfig"], capture_output=True, text=True, errors="ignore")
        for line in res.stdout.splitlines():
            if "IPv4" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    raw_ip = parts[-1].strip().replace("(首选)", "").replace("(Preferred)", "").strip()
                    if raw_ip:
                        valid_ips.add(raw_ip)
    except Exception:
        pass

    # 严格过滤回环地址与代理虚拟网卡 (如 Clash/Mihomo TUN 的 198.18.x.x)
    cleaned = []
    for ip in valid_ips:
        if ip.startswith("127.") or ip.startswith("169.254.") or ip.startswith("198.18."):
            continue
        cleaned.append(ip)

    return sorted(cleaned)

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # 允许跨域与强制不缓存更新，避免旧版本困扰
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def log_message(self, format, *args):
        # 简洁打印请求日志
        sys.stderr.write("[%s] %s - %s\n" % (self.log_date_time_string(), self.client_address[0], format % args))

def find_available_port(start_port=DEFAULT_PORT):
    for p in range(start_port, start_port + 10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return start_port

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = find_available_port(DEFAULT_PORT)
    valid_ips = get_all_valid_ips()

    print("=" * 66)
    print("  🚀 file2quiz 移动端极速刷题服务器已启动 (纯 Python 原生标准库，零依赖)")
    print("=" * 66)
    print("  💻 电脑浏览器访问:   http://localhost:%d" % port)
    print("  📱 手机访问方式:")
    if valid_ips:
        for ip in valid_ips:
            print("     👉 http://%s:%d" % (ip, port))
    else:
        print("     👉 http://127.0.0.1:%d" % port)
    print("=" * 66)
    print("  ⚡ 手机无法连接排查排查手册:")
    print("  1. 【校园网/公司网隔离】如果 IP 是 10.x.x.x 或打不开，说明路由开启了设备隔离。")
    print("     解决方式：开启电脑【移动热点】，手机连电脑热点；手机直接访问 http://192.168.137.1:%d 即可 100%% 秒开！" % port)
    print("  2. 【协议前缀】：手机浏览器务必以 http:// 开头，不要带 s。")
    print("=" * 66)
    print("  按 Ctrl + C 可退出服务器。\n")

    # 允许端口快速重用
    socketserver.TCPServer.allow_reuse_address = True
    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), CustomHandler)
    server.daemon_threads = True

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已安全退出。")
        server.server_close()

if __name__ == "__main__":
    main()
