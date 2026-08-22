---
tags: [FinDA, 7주차, 8주차, 핵심정리]
status: draft-v0.1
---

# 7·8주차 핵심 정리

2주간 배운 것의 압축본. 복습과 최종 프로젝트 준비용.

## 7주차 — BigQuery와 데이터 마트

### Day 1 — BigQuery 입문, 데이터 적재, 기초 쿼리

- 구조: 프로젝트 > 데이터셋 > 테이블. 데이터셋에 리전이 있다 (우리는 `asia-northeast3` 통일).
- 과금은 **처리 바이트** 기준. 미리보기 탭은 무료, `SELECT *`는 습관적으로 쓰지 않는다.
- 테이블 3탭 확인 습관: 미리보기(생김새) · 스키마(타입) · 세부정보(크기).
- 금액이 STRING으로 온다 → `SAFE_CAST`로 변환, 실패는 NULL.

### Day 2 — 금융 데이터 분석 직무와 실습 데이터

- TabFormer: IBM 공개 시뮬레이션 카드 거래 데이터. 사용자 약 2천 명, 거래 약 2,400만 건.
- 데이터의 함정을 먼저 확인한다 — `errors` 컬럼의 NaN은 "오류 없음"이라는 의미 있는 값.
- 분석은 비즈니스 질문에서 시작한다. 질문 → 쿼리 → 검증의 순서.

### Day 3 — 데이터 마트 설계와 구축

- 원본 직접 조회의 3가지 문제: 비용, 로직 불일치, 속도 → 마트가 해결.
- 개념 세트: OLTP vs OLAP, 정규화 vs 비정규화, 팩트/디멘전, **그레인**.
- 설계의 첫 질문은 "**한 행이 무엇인가**" (그레인 선언).
- 저장 도구: CTAS(테이블 복사), 뷰(저장 비용 0, 로직 일원화), 파티셔닝(스캔 절감).
- 층위: Bronze(원본) → Silver(정제) → Gold(마트).

## 8주차 — 고급 SQL과 금융 데이터 분석

### Day 1 — 비즈니스 질문을 SQL로 (고급 쿼리 패턴)

- 루프 대신 **집합 연산** — 절차형으로 풀고 싶은 문제를 서브쿼리·CTE·윈도우로.
- 서브쿼리 3형태: 스칼라, 인라인 뷰, 상관. anti-join 2문형: `NOT EXISTS`, `LEFT JOIN … IS NULL`.
- CTE는 "설계"다: 단계 분리 + 산출물 이름 + 그레인 주석.
- OVER 3요소: `PARTITION BY`, `ORDER BY`, FRAME. 활용: 비중, Top-N(`QUALIFY`), 작년 대비(`LAG`), 누적·이동 집계.
- 재귀 CTE: 앵커 + 재귀부 + 종료 조건. 계층·연속 구조에만.
- 종합: RFM 고객 등급화를 다단계 CTE 파이프라인으로.

### Day 2 — SQL로 하는 금융 데이터 분석

- 시계열: 날짜 스파인으로 불규칙한 거래를 균일하게 → 이동평균, 롤링 변동성, z-score, 볼린저 밴드.
- 리스크: DTI, 한도 소진율, FICO 밴드. 분위수(`PERCENTILE_CONT`, `APPROX_QUANTILES`)로 꼬리 리스크.
- FDS 룰 3종: 고액 이상치, velocity, 지역 점프.
- 평가: confusion matrix, precision/recall. 기저율이 낮으면 "정확도"는 함정 — lift로 다시 본다.

### Day 3 — DART → BigQuery 재무분석 파이프라인

- 파이프라인 4단계: 수집 → 정제 → 적재 → **검증**(장식이 아니라 필수).
- load job은 무료, 스트리밍 insert는 유료 — 비용 제약이 아키텍처를 정한다.
- 멱등성 2패턴: 전체 재적재(replace), 하이워터마크 append(준-멱등이라 검증 필수).
- OpenDART: `corp_code`(8자리)로 식별, 응답은 계정과목 단위 long format, 미공시는 status `013`.
- 재무제표 3표: 손익계산서(벌었나) · 재무상태표(가졌나) · 현금흐름표(현금이 들어왔나).
- 재무비율: 부채비율(부채/자본), 영업이익률(영업이익/매출), ROE(순이익/자본). 전부 `SAFE_DIVIDE`.
- 피벗은 함수가 아니라 패턴 — `MAX(CASE WHEN … THEN … END)` 조건부 집계.
- 자동화: GitHub Actions cron(무료, Secrets로 키 관리). 시각화: Looker Studio + BigQuery 뷰.

## 자주 쓴 문법 한눈에

| 문법 | 용도 | 등장 |
| --- | --- | --- |
| `SAFE_CAST(x AS INT64)` | 문자열 → 숫자, 실패는 NULL | 7주차 Day 1 |
| `CREATE TABLE AS SELECT` | 가공 결과를 테이블로 | 7주차 Day 3 |
| `CREATE OR REPLACE VIEW` | 저장 비용 0의 로직 일원화 | 7주차 Day 3, 8주차 Day 3 |
| `WITH cte AS (…)` | 단계 분리 | 8주차 전체 |
| `SUM(x) OVER (PARTITION BY … ORDER BY …)` | 그룹 내 누적·비중 | 8주차 Day 1 |
| `LAG(x) OVER (…)` | 전기 대비(YoY) | 8주차 Day 1·3 |
| `QUALIFY RANK() OVER (…) <= n` | Top-N 필터 | 8주차 Day 1·3 |
| `PERCENTILE_CONT(x, 0.99)` | 분위수·꼬리 | 8주차 Day 2 |
| `MAX(CASE WHEN … THEN … END)` | long → wide 피벗 | 8주차 Day 3 |
| `SAFE_DIVIDE(a, b)` | 0 나누기 방어 | 8주차 Day 2·3 |
| `COUNTIF(조건)` | 조건 집계 | 8주차 Day 2·3 |
