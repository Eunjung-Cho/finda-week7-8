---
tags: [FinDA, 7주차, BigQuery, SQL, 문법정리, 참고자료]
status: v0.1
---

# BigQuery 주요 문법 정리

7주차 2일차 실습에서 실제로 사용한 문법을 한 장에 모았습니다.
**여기 있는 것만으로 그날의 비즈니스 질문 4개를 전부 풀 수 있습니다.**

예시는 모두 실습 데이터(`tabformer`) 기준이며, `finda-week7-505502`는 본인 프로젝트 ID로 바꿔 쓰세요.

---

## 1. 테이블 참조와 별칭

| 문법 | 역할 | 예시 |
| --- | --- | --- |
| 백틱 3단 이름 | `프로젝트.데이터셋.테이블`을 백틱으로 감싼다 | `` FROM `finda-week7-505502.tabformer.transactions` `` |
| `AS` 별칭 | 테이블에 짧은 이름을 붙인다 | `` FROM `...transactions` AS t `` |
| `t.컬럼` | 어느 테이블의 컬럼인지 밝힌다 | `t.user_id`, `u.gender` |

> 💡 **왜 별칭을 꼭 쓰는가.** 조인이 들어오는 순간 `user_id`가 어느 테이블 것인지 모호해집니다. FinDA에서는 **테이블 별칭과 `t.컬럼` 표기를 항상 쓰는 것**을 규칙으로 합니다.

---

## 2. 기본 절 여섯 가지

| 문법 | 역할 | 예시 |
| --- | --- | --- |
| `SELECT` | 출력할 컬럼과 계산식 | `SELECT t.mcc, COUNT(*) AS tx_cnt` |
| `FROM` | 읽어올 테이블 | `` FROM `...transactions` AS t `` |
| `WHERE` | **행** 필터 (그룹 만들기 전) | `WHERE t.year = 2018` |
| `GROUP BY` | 묶는 축 | `GROUP BY t.mcc` |
| `ORDER BY` | 정렬 (`DESC` 내림차순) | `ORDER BY tx_cnt DESC` |
| `LIMIT` | 출력 행 수 제한 | `LIMIT 10` |

이 여섯 개를 조합한 기본형입니다.

```sql
SELECT
    t.mcc,
    COUNT(*)   AS tx_cnt
FROM `finda-week7-505502.tabformer.transactions` AS t
WHERE t.year = 2018
GROUP BY t.mcc
ORDER BY tx_cnt DESC
LIMIT 10;
```

> ⚠️ **가장 흔한 실수 두 가지.** (1) `ORDER BY` 없는 `LIMIT`은 Top N이 아니라 "아무 N행"입니다. (2) `SELECT`에 쓴 비집계 컬럼은 전부 `GROUP BY`에 있어야 합니다. 빠지면 BigQuery가 어느 컬럼인지 알려 주며 에러를 냅니다.

---

## 3. 조인

| 문법 | 역할 | 짝이 없으면 |
| --- | --- | --- |
| `INNER JOIN ... ON` | 양쪽에 다 있는 행만 남긴다 | **버린다** |
| `LEFT JOIN ... ON` | 왼쪽은 다 남기고 오른쪽을 붙인다 | 오른쪽이 `NULL` |
| `ON` | 조인 조건(키)을 지정한다 | — |

```sql
SELECT
    u.gender,
    COUNT(*)   AS tx_cnt
FROM `finda-week7-505502.tabformer.transactions` AS t
INNER JOIN `finda-week7-505502.tabformer.users` AS u
    ON t.user_id = u.user_id
GROUP BY u.gender;
```

> ⚠️ **조인 뒤에는 반드시 행 수를 확인하세요.** 조인이 **실행됐다**는 것과 **올바르게 됐다**는 것은 다릅니다. 조인 전후로 `SELECT COUNT(*)`를 비교하는 것이 실무의 기본 검증 절차입니다. 행이 **줄었다면** `INNER JOIN`인데 짝이 없는 행이 버려진 것이고, 행이 **늘었다면** 조인 키가 부족해 한 행이 여러 행과 짝지어진 것입니다.

---

## 4. 집계 함수

| 함수 | 역할 | 예시 |
| --- | --- | --- |
| `COUNT(*)` | 행 개수 | `COUNT(*) AS tx_cnt` |
| `COUNT(DISTINCT x)` | 중복 제거한 개수 | `COUNT(DISTINCT t.user_id)` |
| `SUM(x)` | 합계 | `SUM(amount_usd)` |
| `AVG(x)` | 평균 | `AVG(amount_usd)` |
| `MIN(x)` / `MAX(x)` | 최솟값 / 최댓값 | `MAX(t.year)` |
| `COUNTIF(조건)` | **조건에 맞는 행만** 세기 | `COUNTIF(t.is_fraud = "Yes")` |

`COUNTIF`는 BigQuery의 편의 함수입니다. 아래 두 줄은 같은 뜻인데 위가 훨씬 짧습니다.

```sql
COUNTIF(t.is_fraud = "Yes")                          -- BigQuery
COUNT(CASE WHEN t.is_fraud = "Yes" THEN 1 END)       -- 다른 DB에서도 통하는 방식
```

> 💡 **평균과 합계는 다른 이야기를 합니다.** 건당 금액(`AVG`)은 비슷해도 거래 빈도가 다르면 합계(`SUM`)는 크게 벌어집니다. **어느 숫자로 보고할 것인가**를 정하는 일이 곧 지표 정의입니다.

---

## 5. 타입 변환과 정제

| 함수 | 역할 | 실패하면 |
| --- | --- | --- |
| `CAST(x AS 타입)` | 타입 변환 | **쿼리 전체가 실패** |
| `SAFE_CAST(x AS 타입)` | 타입 변환 | 그 값만 `NULL`, 쿼리는 계속 |
| `REPLACE(문자열, 찾을것, 바꿀것)` | 문자 치환 | — |
| `ROUND(숫자, 자릿수)` | 반올림 | — |

실습에서 가장 많이 쓴 한 줄입니다. **금액이 `$318.35` 같은 문자열**이라 그대로 `SUM`할 수 없습니다.

```sql
SAFE_CAST(REPLACE(t.amount, "$", "") AS NUMERIC)   AS amount_usd
```

읽는 순서는 안쪽부터입니다. `$`를 지우고(`REPLACE`) → 숫자로 바꾸고(`SAFE_CAST`) → 이름을 붙입니다.

> ⚠️ **`CAST` 대신 `SAFE_CAST`를 쓰는 이유.** 2,400만 행 중 **단 한 행**이라도 숫자로 못 바꾸는 값이 있으면 `CAST`는 쿼리 전체를 실패시킵니다. `SAFE_CAST`는 그 행만 `NULL`로 두고 나머지를 계산합니다. 대신 **`NULL`이 몇 건 생겼는지 확인하는 습관**이 따라붙어야 합니다.

---

## 6. 조건 분기 — `CASE WHEN`

값을 구간이나 범주로 묶을 때 씁니다. 조건은 **위에서부터 순서대로** 검사하고, 처음 맞는 것에서 멈춥니다.

```sql
CASE
    WHEN u.current_age < 30 THEN "20대 이하"
    WHEN u.current_age < 40 THEN "30대"
    WHEN u.current_age < 50 THEN "40대"
    ELSE "50대 이상"
END   AS age_group
```

> 💡 **순서가 곧 로직입니다.** `WHEN` 순서를 바꾸면 결과가 달라집니다. 위 예시에서 `< 50` 조건을 맨 위로 올리면 20대도 "40대"로 분류됩니다. `ELSE`를 빼면 어디에도 걸리지 않은 값이 `NULL`이 됩니다.

---

## 7. 날짜 다루기

| 문법 | 역할 | 예시 |
| --- | --- | --- |
| `DATE(year, month, day)` | 흩어진 숫자 컬럼을 날짜로 조립 | `DATE(t.year, t.month, t.day)` |
| `DATE "2018-01-01"` | 날짜 리터럴 | `WHERE tx_date >= DATE "2018-01-01"` |

실습 데이터는 날짜가 `year`, `month`, `day` 세 개의 정수 컬럼으로 쪼개져 있습니다.
그래서 **연/월 필터는 조립 없이도** 됩니다.

```sql
WHERE t.year = 2018 AND t.month = 12     -- 조립 불필요
```

반면 "며칠 간격" 같은 날짜 계산을 하려면 `DATE()`로 조립해야 합니다.

---

## 8. 실습 데이터의 함정 (반드시 기억할 것)

| 함정 | 증상 | 해결 |
| --- | --- | --- |
| `amount`가 `$` 붙은 문자열 | `SUM` 하면 타입 오류 | `SAFE_CAST(REPLACE(...))` |
| `is_fraud`가 `"Yes"`/`"No"` 문자열 | `is_fraud = TRUE`가 동작 안 함 | `t.is_fraud = "Yes"` |
| `cards`의 키 이름이 `user` | `c.user_id`라고 쓰면 에러 | `ON t.user_id = c.user` |
| 카드 한 장은 **복합 키** | `user`만으로 조인하면 행이 불어남 | `AND t.card_id = c.card_index` |
| `card_id`가 **0부터** 시작 | 1부터로 착각하면 오프바이원 | 0-기반임을 기억 |
| `merchant_name`이 거대한 정수 | 상점 이름인 줄 알고 `GROUP BY` 하면 숫자만 나옴 | 해시값임을 인지 |
| 온라인 거래는 `merchant_city`가 `ONLINE` | 지역 분석 결과가 튐 | 필요하면 제외 조건 추가 |

---

## 9. 한 문제에 전부 담아 보기

7주차 2일차 마지막 문제(채널별 사기율)에는 위 문법이 거의 다 들어 있습니다.

```sql
SELECT
    t.use_chip,
    COUNT(*)                                                 AS tx_cnt,
    COUNTIF(t.is_fraud = "Yes")                              AS fraud_cnt,
    ROUND(COUNTIF(t.is_fraud = "Yes") / COUNT(*) * 100, 3)   AS fraud_rate_pct
FROM `finda-week7-505502.tabformer.transactions` AS t
GROUP BY t.use_chip
ORDER BY fraud_rate_pct DESC;
```

- 기본 절: `SELECT` / `FROM` / `GROUP BY` / `ORDER BY`
- 집계: `COUNT(*)`, `COUNTIF(조건)`
- 정제: `ROUND`
- 함정 회피: `is_fraud`를 **문자열로** 비교
- 별칭: `ORDER BY`에서 `fraud_rate_pct` 사용 — `SELECT`가 먼저 실행을 끝냈으므로 가능합니다 ([쿼리 작성 순서와 실행 순서](query-execution-order.md) 참고)

> 💡 **사기율이 아주 작게 나오는 것이 정상입니다.** 사기는 원래 희귀합니다. 이 데이터의 전체 사기율은 약 0.12%입니다.

---

## 10. 이어지는 문법

7주차 3일차와 8주차에서 확장되는 것들입니다.

| 문법 | 언제 배우는가 | 무엇을 해결하는가 |
| --- | --- | --- |
| `WITH` (CTE) | 7주차 Day 3 | 같은 정제를 반복해 쓰는 불편함 |
| `CREATE OR REPLACE TABLE ... AS` | 7주차 Day 3 | 결과를 테이블로 저장 (데이터 마트) |
| `CREATE OR REPLACE VIEW` | 7주차 Day 3 | 로직을 한 곳에만 정의 |
| `PARTITION BY` (테이블 설계) | 7주차 Day 3 | 스캔 바이트와 비용 절감 |
| `SAFE_DIVIDE(x, y)` | 8주차 Day 1 | 0으로 나누기 방어 |
| 윈도우 함수 `OVER()` | 8주차 Day 1 | 행을 남긴 채 집계값을 옆에 쓰기 |
| `QUALIFY` | 8주차 Day 1 | 윈도우 함수 결과 필터링 |
| `WITH RECURSIVE` | 8주차 Day 1 | 행이 행을 낳는 계산 |

---

## 함께 보기

- [쿼리 작성 순서와 실행 순서](query-execution-order.md) — 이 문법들이 **어떤 순서로 실행되는지**
- [쿼리 가독성을 높이는 팁](query-style-tips.md) — 같은 쿼리를 **읽기 좋게 쓰는 법**

---

