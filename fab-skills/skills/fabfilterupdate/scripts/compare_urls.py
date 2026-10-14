"""붙여 넣은 Fab 검색 URL을 filters.md와 대조한다.

사용법:
    python compare_urls.py <filters.md 경로> < urls.txt

입력 텍스트 안의 fab.com 검색 URL을 모두 찾아, 각 파라미터와 값이
filters.md에 이미 적혀 있는지(백틱으로 감싼 토큰 기준) 표로 출력한다.
네트워크 접속은 하지 않는다.
"""
import re
import sys
from urllib.parse import parse_qsl, unquote_plus, urlparse

# 값이 자유 입력이라 목록 대조가 의미 없는 파라미터
FREE_VALUE_PARAMS = {"q", "seller", "sellers", "excluded_sellers"}
URL_RE = re.compile(r"https?://(?:www\.)?fab\.com/[^\s<>\"')\]]+")


def known_tokens(md_text):
    return set(re.findall(r"`([^`\n]+)`", md_text))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python compare_urls.py <filters.md> < urls.txt")
    with open(sys.argv[1], encoding="utf-8") as f:
        known = known_tokens(f.read())
    text = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    urls = URL_RE.findall(text)
    if not urls:
        print("fab.com URL을 찾지 못했습니다.")
        return

    rows = {}
    for url in urls:
        u = urlparse(url)
        path = u.path.rstrip("/")
        m = re.match(r"^/search/channels/([^/]+)$", path)
        if m:
            rows.setdefault(("(채널 경로)", m.group(1)), set()).add(url)
        elif path not in ("/search", "/search/creators"):
            rows.setdefault(("(경로)", path), set()).add(url)
        for key, value in parse_qsl(u.query, keep_blank_values=True):
            rows.setdefault((key, unquote_plus(value)), set()).add(url)

    out = sys.stdout
    out.reconfigure(encoding="utf-8")
    out.write(f"URL {len(urls)}개, 파라미터-값 {len(rows)}쌍\n\n")
    out.write("| 파라미터 | 값 | 문서에 파라미터 | 문서에 값 | 판정 |\n|---|---|---|---|---|\n")
    for (key, value) in sorted(rows):
        if key.startswith("("):
            key_known = True
        else:
            key_known = key in known
        if key in FREE_VALUE_PARAMS or key.startswith(("min_", "max_")):
            value_known = None
        else:
            value_known = value in known
        if not key_known:
            verdict = "🆕 새 파라미터"
        elif value_known is False:
            verdict = "🆕 새 값"
        else:
            verdict = "기존"
        vk = "-" if value_known is None else ("있음" if value_known else "없음")
        out.write(f"| `{key}` | `{value}` | {'있음' if key_known else '없음'} | {vk} | {verdict} |\n")


if __name__ == "__main__":
    main()
