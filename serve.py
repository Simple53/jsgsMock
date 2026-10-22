# -*- coding: utf-8 -*-
import http.server
import socketserver
import socket
import os
import sys
import json
try:
    import psutil
except ImportError:
    psutil = None

# 严格锁定 8080 端口，杜绝端口漂移导致手机连不上
PORT = 8080
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

def get_all_ips():
    ips = set()
    try:
        # 遍历所有网卡接口获取 IP (Windows 兼容)
        import psutil
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip = addr.address
                    if not ip.startswith("127.") and not ip.startswith("169.254.") and not ip.startswith("198.18."):
                        ips.add(ip)
    except Exception:
        # 回退方案：gethostbyname_ex
        try:
            hostname = socket.gethostname()
            for ip in socket.gethostbyname_ex(hostname)[2]:
                if not ip.startswith("127.") and not ip.startswith("169.254.") and not ip.startswith("198.18."):
                    ips.add(ip)
        except Exception:
            pass

    # UDP 路由探测主网卡 IP (最后兜底)
    try:
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

STORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_sync_store.json")

def load_server_store():
    if os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_server_store(data):
    try:
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def merge_stores(server_store, client_store):
    """双向时间戳冲突合并：合并答题记录、错题本、艾宾浩斯、收藏夹、考试记录与进度"""
    merged = dict(server_store)

    # 1. 答题记录 (按答题时间戳谁新取谁)
    merged_answers = dict(server_store.get("answers", {}))
    client_answers = client_store.get("answers", {})
    for q_key, c_rec in client_answers.items():
        if q_key not in merged_answers:
            merged_answers[q_key] = c_rec
        else:
            s_time = merged_answers[q_key].get("time", 0) if isinstance(merged_answers[q_key], dict) else 0
            c_time = c_rec.get("time", 0) if isinstance(c_rec, dict) else 0
            if c_time >= s_time:
                merged_answers[q_key] = c_rec
    merged["answers"] = merged_answers

    # 2. 收藏夹 (并集去重)
    s_fav = set(server_store.get("favorites", []))
    c_fav = set(client_store.get("favorites", []))
    merged["favorites"] = list(s_fav.union(c_fav))

    # 3. 艾宾浩斯复习记录 (保留最新复习时间，累加或取最大复习次数)
    s_ebb = dict(server_store.get("ebbinghausWrong", {}))
    c_ebb = client_store.get("ebbinghausWrong", {})
    for q_key, c_item in c_ebb.items():
        if not isinstance(c_item, dict):
            continue
        if q_key not in s_ebb or not isinstance(s_ebb[q_key], dict):
            s_ebb[q_key] = c_item
        else:
            s_item = s_ebb[q_key]
            merged_item = dict(s_item)
            merged_item["lastReviewAt"] = max(s_item.get("lastReviewAt", 0), c_item.get("lastReviewAt", 0))
            merged_item["reviewCount"] = max(s_item.get("reviewCount", 0), c_item.get("reviewCount", 0))
            merged_item["firstWrongAt"] = min(s_item.get("firstWrongAt", 9999999999999), c_item.get("firstWrongAt", 9999999999999))
            s_ebb[q_key] = merged_item
    merged["ebbinghausWrong"] = s_ebb

    # 4. 模拟考试记录 (按试卷 ID 唯一去重)
    s_exams = {e.get("id"): e for e in server_store.get("savedExams", []) if isinstance(e, dict) and e.get("id")}
    for e in client_store.get("savedExams", []):
        if isinstance(e, dict):
            eid = e.get("id")
            if eid:
                if eid not in s_exams or (e.get("score") is not None and s_exams[eid].get("score") is None):
                    s_exams[eid] = e
    merged["savedExams"] = list(s_exams.values())

    # 5. 科目做题进度 progress (取最大进度)
    s_prog = dict(server_store.get("progress", {}))
    c_prog = client_store.get("progress", {})
    for sub, p in c_prog.items():
        s_prog[sub] = max(s_prog.get(sub, 0), p)
    merged["progress"] = s_prog

    # 6. 打卡记录 checkin
    s_check = server_store.get("checkin", {})
    c_check = client_store.get("checkin", {})
    history = set(s_check.get("history", [])).union(set(c_check.get("history", [])))
    sorted_hist = sorted(list(history))
    merged["checkin"] = {
        "history": sorted_hist,
        "days": len(sorted_hist),
        "lastDate": sorted_hist[-1] if sorted_hist else ""
    }

    # 7. AI 解析缓存 aiCache
    s_ai = dict(server_store.get("aiCache", {}))
    s_ai.update(client_store.get("aiCache", {}))
    merged["aiCache"] = s_ai

    # 8. 最后刷题科目与打开过的科目
    merged["lastSubject"] = client_store.get("lastSubject") or server_store.get("lastSubject", "")
    s_opened = dict(server_store.get("openedSubjects", {}))
    s_opened.update(client_store.get("openedSubjects", {}))
    merged["openedSubjects"] = s_opened

    return merged

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/network-info.json":
            body = json.dumps({"port": PORT, "ips": get_all_ips()}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        elif path == "/api/sync":
            store = load_server_store()
            body = json.dumps(store, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/sync":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_data = self.rfile.read(content_length).decode("utf-8")
            try:
                client_store = json.loads(raw_data)
                server_store = load_server_store()
                merged_store = merge_stores(server_store, client_store)
                save_server_store(merged_store)
                body = json.dumps(merged_store, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                err_body = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body)
            return
        self.send_error(404, "Not Found")

def cleanup_zombie_servers(port=PORT):
    """仅在 8080 端口被旧残留 Python 进程占用时安全释放，杜绝误杀自身父进程或正常进程"""
    if not psutil:
        return
    current_pid = os.getpid()
    parent_pid = os.getppid() if hasattr(os, 'getppid') else None
    try:
        for conn in psutil.net_connections(kind='tcp'):
            if conn.laddr and conn.laddr.port == port and conn.pid:
                if conn.pid not in (current_pid, parent_pid):
                    try:
                        p = psutil.Process(conn.pid)
                        if 'python' in p.name().lower():
                            p.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
    except Exception:
        pass

class ExclusiveThreadingHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        # Windows 专属：设置独占端口模式，严禁其他进程同时绑定或抢占 8080
        if sys.platform == "win32" and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            try:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            except OSError:
                pass
        super().server_bind()

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    cleanup_zombie_servers(PORT)
    ips = get_all_ips()

    print("=" * 60)
    print("  jsgsMock 移动端刷题助手服务已就绪！")
    print("=" * 60)
    print("  电脑本机访问:  http://localhost:%d" % PORT)
    print("  手机局域网/Wi-Fi 请访问:")
    for ip in ips:
        print("     👉 http://%s:%d" % (ip, PORT))
    print("=" * 60)
    print("  重要提示:")
    print("  1. 手机浏览器请务必输入完整地址，如: http://%s:%d" % (ips[0] if ips else "127.0.0.1", PORT))
    print("  2. 请勿输入 https:// 或省略 :%d 端口" % PORT)
    print("  按 Ctrl + C 即可停止服务。\n")

    try:
        with ExclusiveThreadingHTTPServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()
    except OSError as e:
        if "10048" in str(e):
            print("\n[错误] 端口 %d 已被占用！" % PORT)
            print("请先关闭之前开启的命令行窗口或杀掉占用 8080 端口的进程后重试。")
        else:
            print("\n服务启动异常:", e)
    except KeyboardInterrupt:
        print("\n服务器已正常退出。")

if __name__ == "__main__":
    main()
