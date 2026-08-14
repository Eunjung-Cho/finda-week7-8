# 강사 메모 — week7/day2-join-aggregation.md

> 이 내용은 사이트에 배포되지 않습니다. 원본 문서: docs/week7/day2-join-aggregation.md

### 강사 메모 (수강생 배포 전 확인)

- (1) 컨텍스트 문서에는 7주차 실습 환경이 SQL Server 또는 PostgreSQL로 되어 있으나, Day 1 적재 가이드가 이미 BigQuery 기준이므로 이 문서의 모든 SQL을 BigQuery Standard SQL로 통일해 작성함 (DATEFROMPARTS 대신 DATE(year, month, day) 등). 커리큘럼 원문과 표현이 다른 부분은 이 조정에 따른 것.
- (2) `YOUR_PROJECT`를 실제 시연용 프로젝트 ID로 바꾼 시연 버전을 별도로 준비할지 결정할 것.
- (3) 수업 전 본인 계정에서 확인할 값: users의 `gender` 실제 표기(Female/Male 또는 F/M), `current_age`와 `yearly_income_person`의 실제 컬럼명과 타입 (자동 감지 적재본은 컬럼명이 다를 수 있음 — Day 1 재적재본 기준으로 안내).
- (4) mcc_map의 26개 코드는 대표적인 ISO 18245 코드로 구성함. 수업 전 커버리지 쿼리를 실제로 돌려 보고, 미매핑 상위 코드가 크면 목록을 보강할 것.
- (5) 샌드박스(결제 미연결) 계정 학생이 있으면 INSERT DML이 막힐 수 있음 — 본문 팁의 CTAS 또는 CSV 업로드 대안을 미리 공지할 것.
- (6) Day 1에서 users 재적재(user_id 부여)를 못 끝낸 학생이 있으면 세션 2-1 시작 전에 Day 1 가이드의 해당 절차를 다시 안내할 것.
- (7) 📷 표시된 스크린샷 4곳을 실제 콘솔 캡처로 채울 것.
- (8) 세션 2-3의 소득 구간 경계값(3만, 6만, 10만 달러)은 임의 예시 — 실제 분포를 보고 조정하거나 "왜 이 경계인가"를 토론거리로 쓸 것.
