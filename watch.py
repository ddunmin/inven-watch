import os, re, json, pathlib, html, time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

URL = "https://www.inven.co.kr/board/fifaonline4/3145?category=%EC%BF%A0%ED%8F%B0"
COUPON_BOX = "https://fconline.nexon.com/coupon"
MAIN_PAGE = "https://fconline.nexon.com/main/index"
STATE = pathlib.Path("last_id.json")
TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT = os.environ["TG_CHAT"]
HEADERS = {"User-Agent": "Mozilla/5.0"}
FAIL_ALERT_AT = 6  # 연속 실패 이 횟수에 도달하면 텔레그램으로 알림


def send(text_html):
    r = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={"chat_id": TG_CHAT, "text": text_html, "parse_mode": "HTML",
              "disable_web_page_preview": "true"},
        timeout=15,
    )
    r.raise_for_status()


def notify(text, code=None):
    msg = html.escape(text)
    if code:
        msg += f"\n\n쿠폰: <code>{html.escape(code)}</code>"
    msg += f"\n\n넥슨 FC온라인 메인(로그인 후 쿠폰등록): {MAIN_PAGE}"
    msg += f"\n쿠폰등록 직접 링크: {COUPON_BOX}"
    send(msg)


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {}


def save_state(state):
    STATE.write_text(json.dumps(state))


def fetch():
    last_err = None
    for i in range(3):
        try:
            r = requests.get(URL, headers=HEADERS, timeout=(10, 30))
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            last_err = e
            print(f"접속 실패 {i + 1}/3: {e}")
            time.sleep(5 * (i + 1))
    raise last_err


def record_failure(state, reason):
    print("실패:", reason)
    if "id" not in state:
        return  # 아직 기준 글번호가 없으면 상태를 저장하지 않음
    state["fails"] = state.get("fails", 0) + 1
    save_state(state)
    if state["fails"] == FAIL_ALERT_AT:
        send(html.escape(f"⚠️ 인벤 접속/파싱이 {FAIL_ALERT_AT}회 연속 실패했습니다. "
                         f"GitHub Actions 로그를 확인해 보세요."))


state = load_state()

try:
    page = fetch()
except Exception as e:
    record_failure(state, str(e))
    raise SystemExit(0)

soup = BeautifulSoup(page, "html.parser")
posts = {}
for a in soup.select("a[href*='/board/fifaonline4/3145/']"):
    m = re.search(r"/3145/(\d+)", a["href"])
    title = a.get_text(strip=True)
    if m and title.startswith("[쿠폰]"):
        posts[int(m.group(1))] = (title, urljoin(URL, a["href"]))

if not posts:
    record_failure(state, "쿠폰 글을 찾지 못함 (차단되었거나 페이지 구조가 바뀜)")
    raise SystemExit(0)

if "id" not in state:
    save_state({"id": max(posts), "fails": 0})
    notify(f"쿠폰 알림 설정 완료 (기준 글번호 {max(posts)})")
else:
    last = state["id"]
    new = sorted(i for i in posts if i > last)
    for pid in new:
        title, link = posts[pid]
        code = title.replace("[쿠폰]", "", 1).strip()
        notify(f"{title}\n{link}", code)
    state["id"] = max([last] + new)
    state["fails"] = 0
    save_state(state)
