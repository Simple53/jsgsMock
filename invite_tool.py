"""邀请码管理工具（jsgsMock）。

用法：
  python invite_tool.py new [数量] [备注]   生成新邀请码，哈希写入 web/invite.json，明文只记在本地 invite_codes.local.txt
  python invite_tool.py revoke 邀请码        吊销一个邀请码（从 web/invite.json 删除其哈希）
  python invite_tool.py list                 查看本地记录的邀请码及其当前是否有效

修改后需 git commit + push，GitHub Pages 约 1 分钟生效；已输入过该码的设备在下次打开且联网时会被重新锁定。
invite.json 只含哈希，可以公开；invite_codes.local.txt 含明文，已加入 .gitignore，切勿提交。
"""
import hashlib
import json
import secrets
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INVITE_JSON = ROOT / "web" / "invite.json"
LOCAL_LOG = ROOT / "invite_codes.local.txt"
ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"  # 去掉易混淆字符 0/1/I/L/O


def normalize(code: str) -> str:
    return "".join(ch for ch in code.upper() if ch.isalnum())


def hash_code(code: str) -> str:
    # 必须与 web/index.html 中的 hashOf 一致：sha256('jsgsmock:' + 规范化邀请码)
    return hashlib.sha256(("jsgsmock:" + normalize(code)).encode("utf-8")).hexdigest()


def load_hashes() -> list:
    if INVITE_JSON.exists():
        return json.loads(INVITE_JSON.read_text(encoding="utf-8")).get("codes", [])
    return []


def save_hashes(hashes: list) -> None:
    INVITE_JSON.write_text(json.dumps({"codes": hashes}, indent=2) + "\n", encoding="utf-8")


def new_code() -> str:
    raw = "".join(secrets.choice(ALPHABET) for _ in range(12))
    return f"{raw[:4]}-{raw[4:8]}-{raw[8:]}"


def cmd_new(count: int, note: str) -> None:
    hashes = load_hashes()
    lines = []
    for _ in range(count):
        code = new_code()
        hashes.append(hash_code(code))
        lines.append(f"{code}\t{date.today()}\t{note}")
        print(code)
    save_hashes(hashes)
    with LOCAL_LOG.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def cmd_revoke(code: str) -> None:
    hashes = load_hashes()
    h = hash_code(code)
    if h not in hashes:
        print("名单中没有这个邀请码")
        return
    hashes.remove(h)
    save_hashes(hashes)
    print("已吊销，记得 git commit + push")


def cmd_list() -> None:
    if not LOCAL_LOG.exists():
        print("还没有本地记录")
        return
    valid = set(load_hashes())
    for line in LOCAL_LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        code = line.split("\t")[0]
        status = "有效" if hash_code(code) in valid else "已吊销"
        print(f"{status}\t{line}")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
    elif args[0] == "new":
        count = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
        note = args[2] if len(args) > 2 else (args[1] if len(args) > 1 and not args[1].isdigit() else "")
        cmd_new(count, note)
    elif args[0] == "revoke" and len(args) > 1:
        cmd_revoke(args[1])
    elif args[0] == "list":
        cmd_list()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
