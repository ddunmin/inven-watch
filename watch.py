import os, re, json, pathlib, sys, html
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

URL = "https://www.inven.co.kr/board/fifaonline4/3145?category=%EC%BF%A0%ED%8F%B0"
COUPON_BOX = "https://box.coupon.nexon.com/CouponBox"
STATE = pathlib.Path("last_id.json")
TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT = os.environ["TG_CHAT"]

def notify(text, code=None):
    msg = html.escape(text)
    if code:
        msg += f"\n\n쿠폰: <code>{html.escape(code)}</code>"
    msg += f"\n\n넥슨 쿠폰함: {COUPON_BOX}"
    r = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={"chat_id": TG_CHAT, "text": msg, "parse_mode": "HTML",
              "disable_web_page_preview": "true"},
        timeout=15,
    )
    r.raise_for_status()

resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

posts = {}
for a in soup.select("a[href*='/board/fifaonline4/3145/']"):
    m = re.search(r"/3145/(\d+)", a["href"])
    title = a.get_text(strip=True)
    if m and title.startswith("[쿠폰]"):
        posts[int(m.group(1))] = (title, urljoin(URL, a["href"]))

if not posts:
    sys.exit("쿠폰 글을 찾지 못했습니다 (차단되었거나 페이지 구조가 바뀜)")

if not STATE.exists():
    STATE.write_text(json.dumps({"id": max(posts)}))
    notify(f"쿠폰 알림 설정 완료 (기준 글번호 {max(posts)})")
else:
    last = json.loads(STATE.read_text())["id"]
    new = sorted(i for i in posts if i > last)
    for pid in new:
        title, link = posts[pid]
        code = title.replace("[쿠폰]", "", 1).strip()
        notify(f"{title}\n{link}", code)
    if new:
        STATE.write_text(json.dumps({"id": max(new)}))
