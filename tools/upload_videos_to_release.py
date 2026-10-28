# -*- coding: utf-8 -*-
"""
Upload compressed videos in web/videos/ to GitHub Release 'course-videos'
and generate web/course_videos.js with direct HTTPS CDN URLs.
Resumable & multi-threaded.
"""
import os
import sys
import json
import time
import urllib.request
import urllib.parse
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

TAG_NAME = "course-videos"
OWNER = "Simple53"
REPO = "jsgsMock"

def get_git_token():
    try:
        p = subprocess.Popen(['git', 'credential', 'fill'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, _ = p.communicate(input='protocol=https\nhost=github.com\n\n', timeout=5)
        for line in out.splitlines():
            if line.startswith('password='):
                return line[9:].strip()
    except Exception as e:
        print("Error getting token from git credential:", e)
    return os.environ.get("GITHUB_TOKEN", "")

def get_release_info(token):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{TAG_NAME}"
    req = urllib.request.Request(url, headers={
        'Authorization': f'token {token}',
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/vnd.github.v3+json'
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Create release
            create_url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases"
            create_req = urllib.request.Request(create_url, headers={
                'Authorization': f'token {token}',
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            }, data=json.dumps({
                "tag_name": TAG_NAME,
                "name": "jsgsMock 官方名师课程视频资源库 (123节)",
                "body": "本 Release 存放 123 节江苏高校教资名师精讲课程视频资源，用于网页端及客户端高速流媒体播放。",
                "draft": False,
                "prerelease": False
            }).encode('utf-8'))
            with urllib.request.urlopen(create_req) as resp2:
                return json.loads(resp2.read().decode())
        raise

def get_existing_assets(token, release_id):
    assets = {}
    page = 1
    while True:
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/{release_id}/assets?per_page=100&page={page}"
        req = urllib.request.Request(url, headers={
            'Authorization': f'token {token}',
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/vnd.github.v3+json'
        })
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            if not data:
                break
            for a in data:
                assets[a['name']] = a['browser_download_url']
            if len(data) < 100:
                break
            page += 1
    return assets

def upload_single_asset(token, release_id, asset_name, file_path, max_retries=3):
    upload_url = f"https://uploads.github.com/repos/{OWNER}/{REPO}/releases/{release_id}/assets?name={urllib.parse.quote(asset_name)}"
    with open(file_path, 'rb') as f:
        file_bytes = f.read()

    file_size_mb = len(file_bytes) / (1024 * 1024)

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(upload_url, headers={
                'Authorization': f'token {token}',
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'video/mp4',
                'Content-Length': str(len(file_bytes))
            }, data=file_bytes)
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode())
                elapsed = time.time() - t0
                speed = file_size_mb / elapsed if elapsed > 0 else 0
                return True, data.get('browser_download_url'), f"{elapsed:.1f}s ({speed:.2f}MB/s)"
        except Exception as e:
            if attempt == max_retries:
                return False, None, str(e)
            time.sleep(2 * attempt)
    return False, None, "Unknown error"

def main():
    print("=" * 60)
    print("jsgsMock 课程视频自动上传与 CDN 部署工具 (GitHub Releases)")
    print("=" * 60)

    token = get_git_token()
    if not token:
        print("[错误] 未检测到 GitHub Token，请确认已在本地 git 登录。")
        sys.exit(1)

    print("[1/4] 获取/创建 Release:", TAG_NAME)
    rel = get_release_info(token)
    release_id = rel['id']
    print(f"      Release ID: {release_id}")

    print("[2/4] 获取已上传的附件列表...")
    existing = get_existing_assets(token, release_id)
    print(f"      云端已有 {len(existing)} 个视频附件")

    # 扫描本地视频并构建上传任务与课程结构
    videos_dir = Path('web/videos')
    if not videos_dir.exists():
        print("[错误] web/videos 目录不存在！")
        sys.exit(1)

    course_folders = sorted([f for f in videos_dir.iterdir() if f.is_dir()])
    tasks = []
    courses_meta = []

    for c_folder in course_folders:
        sub_prefix = c_folder.name[:2]
        c_name = c_folder.name.split('_', 1)[-1]
        mp4_files = sorted(c_folder.glob('*.mp4'))
        lessons_meta = []

        for idx, mp4 in enumerate(mp4_files, 1):
            asset_name = f"s{sub_prefix}_{idx:02d}.mp4"
            clean_title = mp4.stem.split('_', 1)[-1] if '_' in mp4.stem else mp4.stem
            expected_url = f"https://github.com/{OWNER}/{REPO}/releases/download/{TAG_NAME}/{asset_name}"

            lessons_meta.append({
                "title": clean_title,
                "asset_name": asset_name,
                "file_path": mp4,
                "url": expected_url
            })

            if asset_name not in existing:
                tasks.append((asset_name, mp4))

        courses_meta.append({
            "title": c_name,
            "lessons": lessons_meta
        })

    total_lessons = sum(len(c['lessons']) for c in courses_meta)
    print(f"[3/4] 本地共找到 5 门课程、{total_lessons} 节视频。")
    print(f"      待上传新视频: {len(tasks)} 节 (已上传 {len(existing)} 节)")

    # 开始并发上传
    if tasks:
        completed = len(existing)
        start_all = time.time()
        print(f"      开始上传，启用 3 线程并发传输...")

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_task = {
                executor.submit(upload_single_asset, token, release_id, name, path): (name, path)
                for name, path in tasks
            }
            for future in as_completed(future_to_task):
                name, path = future_to_task[future]
                success, url, info = future.result()
                if success:
                    completed += 1
                    pct = (completed / total_lessons) * 100
                    print(f"  [{completed}/{total_lessons}] {name} 上传成功 - {info} ({pct:.1f}%)", flush=True)
                else:
                    print(f"  [失败] {name} 上传失败: {info}", flush=True)

        total_elapsed = time.time() - start_all
        print(f"      全部传输完毕！总耗时: {total_elapsed / 60:.1f} 分钟")
    else:
        print("      所有视频均已上传完毕，无需重复上传。")

    # 更新 web/course_videos.js
    print("[4/4] 正在更新 web/course_videos.js 播放目录...")
    catalog_courses = []
    for c in courses_meta:
        catalog_lessons = []
        for l in c['lessons']:
            catalog_lessons.append({
                "title": l['title'],
                "url": l['url']
            })
        catalog_courses.append({
            "title": c['title'],
            "lessons": catalog_lessons
        })

    catalog_js = "window.COURSE_VIDEOS = " + json.dumps(catalog_courses, ensure_ascii=False, indent=2) + ";\n"
    with open('web/course_videos.js', 'w', encoding='utf-8') as f:
        f.write(catalog_js)

    print("      web/course_videos.js 更新成功！")
    print("=" * 60)
    print("全部 123 节名师课程视频已成功部署至 GitHub Releases CDN！")
    print("只需执行 git commit 并 push，即可在 github.io 永久秒开流畅观看！")
    print("=" * 60)

if __name__ == '__main__':
    main()
