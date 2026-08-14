# FinDA_7,8week 강의자료 사이트

금융 데이터 분석 부트캠프 심화반 2기 7주차 강의자료를 MkDocs Material로 배포합니다.
(8주차는 별도 개편 후 추가 예정)

**공개 주소**: https://eunjung-cho.github.io/finda-week7-8/

---

## 폴더 구조

```
.
├─ docs/                    # 사이트에 배포되는 강의자료
│  ├─ index.md              # 첫 화면
│  ├─ week7/                # 7주차 Day 1-3 강의안 (원본에서 자동 생성됨)
│  └─ assets/images/        # 이미지
├─ tools/convert.py         # Obsidian 원본 -> docs/ 변환 스크립트
├─ mkdocs.yml               # 사이트 설정 (제목, 목차, 테마)
├─ requirements.txt
└─ .github/workflows/deploy.yml   # push 시 자동 빌드 및 배포

(instructor-notes/는 강사용 풀이 모음으로 로컬에만 존재하며 GitHub에 올라가지 않습니다)
```

## 자료를 수정하려면

**항상 Obsidian 원본을 고칩니다** (`FinDA/7주차 수업`의 v0.2 파일들).
`docs/`를 직접 고치면 다음 재변환 때 덮어써져 수정이 사라집니다.

원본을 고친 뒤:

```bash
python tools/convert.py   # 원본 -> docs/ 재변환, 강사용 풀이 분리
mkdocs serve              # (선택) http://127.0.0.1:8000 에서 미리보기
git add . && git commit -m "자료 수정" && git push
```

push하면 GitHub Actions가 1-2분 안에 자동으로 사이트에 반영합니다.

## 강사용 풀이의 위치

원본 문서 끝의 "### 강사 메모 (수강생 배포 전 확인)" 섹션에 실습 풀이를 적으면,
변환 스크립트가 그 부분을 사이트에서 제외하고 로컬 `instructor-notes/`로 분리합니다.
`instructor-notes/`는 .gitignore에 있어 GitHub에 올라가지 않습니다.

## 목차 순서를 바꾸려면

`mkdocs.yml` 맨 아래 `nav:` 항목의 순서나 표시명을 수정합니다.

## URL 형식

`mkdocs.yml`의 `use_directory_urls: false` 설정으로 `.../week7/day1-lecture.html` 형태가 됩니다.
`true`로 바꾸면 `.../week7/day1-lecture/` 형태가 되며, 기존 링크가 깨지므로 배포 후에는 바꾸지 않는 편이 좋습니다.
