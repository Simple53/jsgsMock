"""Compress local course MP4s for static hosting and generate the tutorial catalog.

Usage: python build_course_videos.py --source PATH --output PATH --base-url HTTPS_URL
Requires ffmpeg on PATH. Upload the output directory to the chosen video host.
"""

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base-url', required=True, help='Public HTTPS URL of the output directory')
    parser.add_argument('--ffmpeg', default='ffmpeg')
    args = parser.parse_args()
    if not args.source.is_dir():
        parser.error('Video source directory does not exist')
    if not (args.base_url.startswith('https://') or args.base_url == './videos'):
        parser.error('Video base URL must use HTTPS or ./videos for local preview')
    ffmpeg = shutil.which(args.ffmpeg)
    if not ffmpeg and args.ffmpeg == 'ffmpeg':
        try:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
    if not ffmpeg:
        parser.error('ffmpeg is required to compress videos')

    courses = []
    for folder in sorted(p for p in args.source.iterdir() if p.is_dir()):
        lessons = []
        for source in sorted(folder.glob('*.mp4')):
            dest = args.output / folder.name / source.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists() or dest.stat().st_mtime < source.stat().st_mtime:
                print(f'Compressing {folder.name}/{source.name}', flush=True)
                temp = dest.with_name(dest.stem + '.tmp.mp4')
                subprocess.run([
                    ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
                    '-vf', 'scale=-2:480', '-c:v', 'libx264', '-preset', 'veryfast', '-threads', '2',
                    '-crf', '34', '-c:a', 'aac', '-ac', '1', '-b:a', '48k',
                    '-movflags', '+faststart', str(temp)
                ], check=True)
                temp.replace(dest)
            url = args.base_url.rstrip('/') + '/' + '/'.join(quote(part) for part in dest.relative_to(args.output).parts)
            lessons.append({'title': source.stem.split('_', 1)[-1], 'url': url})
        if lessons:
            courses.append({'title': folder.name.split('_', 1)[-1], 'lessons': lessons})

    catalog = Path('web/course_videos.js')
    catalog.write_text('window.COURSE_VIDEOS = ' + json.dumps(courses, ensure_ascii=False) + ';\n', encoding='utf-8')
    print(f'{sum(len(c["lessons"]) for c in courses)} videos compressed; catalog: {catalog}')


if __name__ == '__main__':
    main()
