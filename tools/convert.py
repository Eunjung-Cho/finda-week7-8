# -*- coding: utf-8 -*-
"""FinDA 강의 md -> MkDocs docs 변환 스크립트.
- 코드 펜스(``` ... ```) 내부는 건드리지 않음 (pandas의 [[...]] 보호)
- Obsidian 위키링크 [[이름]] / [[이름|별칭]] -> 상대 md 링크
- Obsidian 이미지 임베드 ![[Pasted image X.png]] -> ![](../assets/images/X.png)
"""
import re
import shutil
from pathlib import Path

VAULT = Path(r"C:/Users/eunju/OneDrive/문서/Obsidian Vault")
SRC = VAULT / "FinDA"
SITE = SRC / "finda-week7-8-site"
DOCS = SITE / "docs"
IMG_DIR = DOCS / "assets" / "images"
ATTACH = VAULT / "attachments"

# (원본 파일, 대상 상대 경로)
# 7주차 3개 문서 + 8주차 개편본(강의안 3개, 사전 배포물 2개)을 배포한다.
# 수업 중 배포물(재귀 CTE 짝풀이, 이동평균 스켈레톤)은 수업 시점에 나눠 주는 자료라 사이트에서 제외.
FILES = [
    ("7주차 수업/FinDA_7주차_1일차_BigQuery입문_적재_기초쿼리_v0.2.md", "week7/day1-lecture.md"),
    ("7주차 수업/FinDA_7주차_2일차_금융데이터분석_직무_데이터소개_v0.2.md", "week7/day2-lecture.md"),
    ("7주차 수업/FinDA_7주차_3일차_데이터마트_설계_구축_v0.2.md", "week7/day3-lecture.md"),
    ("7주차 수업/FinDA_7주차_쿼리_가독성_팁_v0.1.md", "week7/query-style-tips.md"),
    ("7주차 수업/FinDA_7주차_쿼리_작성순서_실행순서_v0.1.md", "week7/query-execution-order.md"),
    ("7주차 수업/FinDA_7주차_BigQuery_주요문법_v0.1.md", "week7/bigquery-syntax.md"),
    ("8주차 수업/FinDA_8주차_1일차_고급SQL_비즈니스패턴_v0.1.md", "week8/day1-lecture.md"),
    ("8주차 수업/FinDA_8주차_1일차_사전배포_윈도우프레임_워크시트_v0.1.md", "week8/day1-worksheet.md"),
    ("8주차 수업/FinDA_8주차_2일차_SQL_금융데이터분석_v0.1.md", "week8/day2-lecture.md"),
    ("8주차 수업/FinDA_8주차_3일차_DART_BigQuery_재무분석_v0.1.md", "week8/day3-lecture.md"),
    ("8주차 수업/FinDA_8주차_3일차_사전배포_DART키발급_GCP점검_가이드_v0.1.md", "week8/day3-prep-guide.md"),
]

# 위키링크 대상 -> (대상 md 파일명, 기본 라벨)  ※ 같은 폴더(week7) 기준 상대 경로
WIKILINK_MAP = {
    "FinDA_7주차_1일차_BigQuery입문_적재_기초쿼리_v0.2": ("day1-lecture.md", "Day 1 강의안"),
    "FinDA_7주차_2일차_금융데이터분석_직무_데이터소개_v0.2": ("day2-lecture.md", "Day 2 강의안"),
    "FinDA_7주차_3일차_데이터마트_설계_구축_v0.2": ("day3-lecture.md", "Day 3 강의안"),
    "FinDA_7주차_쿼리_가독성_팁_v0.1": ("query-style-tips.md", "쿼리 가독성을 높이는 팁"),
    "FinDA_7주차_쿼리_작성순서_실행순서_v0.1": ("query-execution-order.md", "쿼리 작성 순서와 실행 순서"),
    "FinDA_7주차_BigQuery_주요문법_v0.1": ("bigquery-syntax.md", "BigQuery 주요 문법 정리"),
}

# 변환 전에 이전 산출물 정리 (assets와 index.md는 유지)
# OneDrive와 파일 감시 프로세스가 디렉터리를 잠글 수 있어 파일 단위로 삭제
for stale in ["week7", "week8"]:
    for base in (DOCS / stale, SITE / "instructor-notes" / stale):
        if base.exists():
            for f in base.rglob("*"):
                if f.is_file():
                    f.unlink()

IMG_RE = re.compile(r"!\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")
WIKI_RE = re.compile(r"(?<!\!)\[\[([^\]|]+?)(?:\|([^\]]*))?\]\]")
FENCE_RE = re.compile(r"^(\s*)(```|~~~)")

copied_images = set()


def convert_line(line: str) -> str:
    def img_sub(m):
        name = m.group(1).strip()
        src = ATTACH / name
        clean = name.replace(" ", "-").lower()
        if src.exists():
            IMG_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, IMG_DIR / clean)
            copied_images.add(clean)
            return f"![스크린샷](../assets/images/{clean})"
        return f"(그림: {name} — 파일 없음)"

    def wiki_sub(m):
        target = m.group(1).strip()
        alias = (m.group(2) or "").strip()
        if target in WIKILINK_MAP:
            fname, label = WIKILINK_MAP[target]
            return f"[{alias or label}]({fname})"
        return alias or target  # 미지 링크는 텍스트로

    line = IMG_RE.sub(img_sub, line)
    line = WIKI_RE.sub(wiki_sub, line)
    return line


for rel_src, rel_dst in FILES:
    src_path = SRC / rel_src
    dst_path = DOCS / rel_dst
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    out_lines = []
    in_fence = False
    fence_marker = None
    for line in src_path.read_text(encoding="utf-8").splitlines():
        m = FENCE_RE.match(line)
        if m:
            if not in_fence:
                in_fence = True
                fence_marker = m.group(2)
            elif line.strip().startswith(fence_marker):
                in_fence = False
                fence_marker = None
            out_lines.append(line)
            continue
        out_lines.append(line if in_fence else convert_line(line))
    dst_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"OK  {rel_src} -> {rel_dst}")

print("images:", sorted(copied_images))

# 변환 후 잔여 Obsidian 문법 검사 (코드 펜스 밖)
print("\n-- 잔여 위키링크/임베드 검사 --")
issues = 0
for rel_src, rel_dst in FILES:
    in_fence = False
    fence_marker = None
    for i, line in enumerate((DOCS / rel_dst).read_text(encoding="utf-8").splitlines(), 1):
        m = FENCE_RE.match(line)
        if m:
            if not in_fence:
                in_fence, fence_marker = True, m.group(2)
            elif line.strip().startswith(fence_marker):
                in_fence, fence_marker = False, None
            continue
        if not in_fence and ("[[" in line or "![[" in line):
            print(f"WARN {rel_dst}:{i}: {line.strip()[:100]}")
            issues += 1
print("clean" if issues == 0 else f"{issues} issue(s)")


from pathlib import Path

SITE = Path(r"C:/Users/eunju/OneDrive/문서/Obsidian Vault/FinDA/finda-week7-8-site")
DOCS = SITE / "docs"
NOTES = SITE / "instructor-notes"

for md in sorted(list((DOCS / "week7").glob("*.md")) + list((DOCS / "week8").glob("*.md"))):
    lines = md.read_text(encoding="utf-8").splitlines()
    start = end = None
    for i, line in enumerate(lines):
        if re.match(r"^#{2,3} 강사 메모", line):
            start = i
        elif start is not None and line.startswith("오늘의 핵심 교훈"):
            end = i
            break
    if start is None:
        print(f"SKIP (메모 없음): {md.name}")
        continue
    if end is None:
        end = len(lines)
    memo = lines[start:end]
    # 추출본 뒤쪽의 구분선/빈 줄 정리
    while memo and memo[-1].strip() in ("", "---"):
        memo.pop()
    rel = md.relative_to(DOCS)
    note_path = NOTES / rel
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(
        f"# 강사 메모 — {rel.as_posix()}\n\n"
        f"> 이 내용은 사이트에 배포되지 않습니다. 원본 문서: docs/{rel.as_posix()}\n\n"
        + "\n".join(memo) + "\n",
        encoding="utf-8",
    )
    # 본문에서 제거 (메모 앞의 빈 줄 하나 정리)
    before = lines[:start]
    while before and before[-1].strip() == "":
        before.pop()
    remainder = lines[end:]
    new_lines = before + [""] + remainder
    text = "\n".join(new_lines) + "\n"
    # 남은 본문의 '강사 메모' 참조 문구 정리
    text = text.replace("아래 강사 메모 참고", "실행마다 값이 달라질 수 있음에 유의")
    md.write_text(text, encoding="utf-8")
    print(f"OK  {rel.as_posix()}: 메모 {len(memo)}줄 -> instructor-notes/{rel.as_posix()}")

# 검증: docs에 '강사 메모' 잔여 여부
left = []
for md in DOCS.rglob("*.md"):
    t = md.read_text(encoding="utf-8")
    if "강사 메모" in t:
        for i, l in enumerate(t.splitlines(), 1):
            if "강사 메모" in l:
                left.append(f"{md.relative_to(DOCS)}:{i}: {l.strip()[:80]}")
print("\n잔여 언급:", len(left))
for x in left:
    print(" ", x)
