# 강사 메모 — week7/day1-bigquery-load.md

> 이 내용은 사이트에 배포되지 않습니다. 원본 문서: docs/week7/day1-bigquery-load.md

### 강사 메모 (수강생 배포 전 정리할 것)

- `YOUR_BUCKET`, `YOUR_PROJECT`를 실제 값 또는 "각자 본인 값으로 교체" 안내로 바꾸기
- 40명이 각자 GCS 버킷을 만들면 이름 충돌은 없지만(전역 고유), 비용과 정리를 위해 실습 후 버킷 삭제 안내를 넣을지 결정
- users와 cards도 컬럼명을 깔끔하게 고정하려면 수동 스키마 전체 버전이 필요함 (요청 시 별도 제공)
