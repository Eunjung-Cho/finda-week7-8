# FinDA_7,8week 강의자료 사이트

금융 데이터 분석 부트캠프 심화반 2기 7-8주차 강의자료를 MkDocs Material로 배포합니다.

**공개 주소**: https://eunjung-cho.github.io/finda-week7-8/

---

## 폴더 구조

```
.
├─ docs/                    # 사이트에 배포되는 강의자료 (여기만 편집하면 됩니다)
│  ├─ index.md              # 첫 화면
│  ├─ week7/                # 7주차 5개 문서
│  ├─ week8/                # 8주차 4개 문서
│  └─ assets/               # 이미지 (여기에 넣으세요)
├─ instructor-notes/        # 강사 메모 — 사이트에 배포되지 않음
├─ tools/convert.py         # Obsidian .md -> docs/ 변환 스크립트 (재변환용)
├─ mkdocs.yml               # 사이트 설정 (제목, 목차, 테마)
├─ requirements.txt
└─ .github/workflows/deploy.yml   # push 시 자동 빌드 및 배포
```

## 자료를 수정하려면

**방법 A. GitHub 웹에서 직접** (가장 간단)
`docs/` 안의 .md 파일을 열고 연필 아이콘 클릭 → 수정 → Commit changes. 2분 뒤 사이트에 반영됩니다.

**방법 B. 로컬에서 미리보기하며**
```bash
pip install -r requirements.txt
mkdocs serve          # http://127.0.0.1:8000 에서 실시간 확인
git add . && git commit -m "자료 수정" && git push
```

## 목차 순서를 바꾸려면

`mkdocs.yml` 맨 아래 `nav:` 항목의 순서나 표시명을 수정합니다.

## 강사 메모를 사이트에 포함하려면

`instructor-notes/`의 내용을 해당 `docs/` 파일 끝에 붙여 넣으면 됩니다.
기본값은 **미포함**입니다.

## URL 형식

`mkdocs.yml`의 `use_directory_urls: false` 설정으로 `.../week7/day2-worksheet.html` 형태가 됩니다.
`true`로 바꾸면 `.../week7/day2-worksheet/` 형태가 되며, 기존 링크가 깨지므로 배포 후에는 바꾸지 않는 편이 좋습니다.
