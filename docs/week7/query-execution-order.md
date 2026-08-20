---
tags: [FinDA, 7주차, BigQuery, SQL, 실행순서, 참고자료]
status: v0.1
---

# 쿼리 작성 순서와 실행 순서

SQL은 **우리가 쓰는 순서**와 **엔진이 실행하는 순서**가 다릅니다.
이 차이를 모르면 "분명 맞게 쓴 것 같은데 왜 에러가 나지?"라는 상황을 반복하게 됩니다.

반대로 이 순서 하나만 머릿속에 넣어 두면, 오류 메시지를 보자마자 원인이 짚입니다.

---

## 한눈에 보는 순서

| 순서 | 쿼리 작성 순서 | 실행 순서 | 역할 |
|---:|---|---|---|
| 1 | `SELECT` | **`FROM`** | 어떤 테이블에서 가져올지 결정 |
| 2 | `FROM` | **`JOIN` / `ON`** | 다른 테이블과 결합 |
| 3 | `JOIN` | **`WHERE`** | 필요한 행만 필터링 |
| 4 | `WHERE` | **`GROUP BY`** | 데이터를 그룹화 |
| 5 | `GROUP BY` | **`HAVING`** | 그룹화된 결과를 필터링 |
| 6 | `HAVING` | **윈도우 함수** | `ROW_NUMBER`, `RANK`, `SUM() OVER()` 등 계산 |
| 7 | `QUALIFY` | **`QUALIFY`** | 윈도우 함수 결과 필터링 |
| 8 | `ORDER BY` | **`SELECT`** | 최종 출력할 컬럼/표현식 결정 |
| 9 | `LIMIT` | **`DISTINCT`** | 중복 제거 |
| 10 | — | **`ORDER BY`** | 결과 정렬 |
| 11 | — | **`LIMIT`** | 출력 행 수 제한 |

핵심은 한 줄로 요약됩니다.

> **`SELECT`는 우리가 가장 먼저 쓰지만, 엔진은 거의 마지막에 실행합니다.**

---

## 왜 이 순서를 알아야 하는가

### (1) `WHERE`에서는 `SELECT`의 별칭을 쓸 수 없다

`WHERE`는 3번째로 실행되고 `SELECT`는 8번째로 실행됩니다.
`WHERE`가 돌아가는 시점에는 `amount_usd`라는 이름이 **아직 세상에 없습니다.**

**동작하지 않음**

```sql
SELECT
    t.user_id,
    SAFE_CAST(REPLACE(t.amount, "$", "") AS NUMERIC)   AS amount_usd
FROM `finda-week7-505502.tabformer.transactions` AS t
WHERE amount_usd > 1000        -- 오류: amount_usd를 아직 모른다
```

**해결 1 — 식을 그대로 반복한다**

```sql
SELECT
    t.user_id,
    SAFE_CAST(REPLACE(t.amount, "$", "") AS NUMERIC)   AS amount_usd
FROM `finda-week7-505502.tabformer.transactions` AS t
WHERE SAFE_CAST(REPLACE(t.amount, "$", "") AS NUMERIC) > 1000
```

**해결 2 — 단계를 나눈다 (권장)**

```sql
WITH clean AS (        -- 한 행 = 거래 1건 (금액 정제)
    SELECT
        t.user_id,
        SAFE_CAST(REPLACE(t.amount, "$", "") AS NUMERIC)   AS amount_usd
    FROM `finda-week7-505502.tabformer.transactions` AS t
)
SELECT c.user_id, c.amount_usd
FROM clean AS c
WHERE c.amount_usd > 1000      -- 안쪽 SELECT가 이미 끝났으므로 사용 가능
```

같은 정제를 두 번 쓰는 것이 싫다면 `WITH`로 나누는 것이 정답입니다.
7주차 3일차에서 배운 **뷰와 데이터 마트**도 결국 이 불편함을 없애기 위한 장치입니다.

### (2) `WHERE`와 `HAVING`은 자르는 대상이 다르다

- `WHERE`는 **그룹을 만들기 전**(3번), 개별 **행**을 거릅니다.
- `HAVING`은 **그룹을 만든 뒤**(5번), **그룹**을 거릅니다.

```sql
SELECT
    t.mcc,
    COUNT(*)   AS tx_cnt
FROM `finda-week7-505502.tabformer.transactions` AS t
WHERE t.year = 2018            -- 2018년 거래만 남긴다 (행 단위)
GROUP BY t.mcc
HAVING COUNT(*) >= 10000       -- 1만 건 이상인 업종만 남긴다 (그룹 단위)
```

`WHERE COUNT(*) >= 10000`이라고 쓰면 오류가 납니다.
`WHERE`가 실행되는 시점에는 아직 그룹이 없어서 `COUNT(*)`를 셀 수가 없기 때문입니다.

### (3) 윈도우 함수는 `WHERE`로 거를 수 없다 — 그래서 `QUALIFY`가 있다

윈도우 함수는 6번째, `WHERE`는 3번째에 실행됩니다.
`WHERE`가 돌 때 순위는 아직 매겨지지 않았습니다.

**동작하지 않음**

```sql
SELECT
    c.mcc,
    c.merchant_city,
    RANK() OVER (PARTITION BY c.mcc ORDER BY c.spend DESC)   AS rk
FROM city_spend AS c
WHERE rk <= 3                  -- 오류: 순위는 아직 계산되지 않았다
```

**해결 1 — 감싸서 거른다 (다른 DB에서도 통하는 방식)**

```sql
WITH ranked AS (
    SELECT
        c.mcc,
        c.merchant_city,
        RANK() OVER (PARTITION BY c.mcc ORDER BY c.spend DESC)   AS rk
    FROM city_spend AS c
)
SELECT r.mcc, r.merchant_city
FROM ranked AS r
WHERE r.rk <= 3
```

**해결 2 — `QUALIFY` (BigQuery 관용구)**

```sql
SELECT c.mcc, c.merchant_city
FROM city_spend AS c
QUALIFY RANK() OVER (PARTITION BY c.mcc ORDER BY c.spend DESC) <= 3
```

`QUALIFY`는 윈도우 함수(6번) **다음**인 7번에 실행되므로 순위를 볼 수 있습니다.
세 필터의 역할을 한 줄로 정리하면 이렇습니다.

> **`WHERE`는 행을, `HAVING`은 그룹을, `QUALIFY`는 윈도우 결과를 거릅니다.**

### (4) `ORDER BY` 없는 `LIMIT`은 "아무 N행"이다

`LIMIT`은 11번, 가장 마지막입니다. 그 앞의 `ORDER BY`(10번)가 없으면
엔진이 편한 순서대로 이미 나온 결과에서 그냥 N개를 잘라 옵니다.

```sql
-- Top 10이 아니라 "아무 10행"
SELECT t.mcc, COUNT(*) AS tx_cnt
FROM `finda-week7-505502.tabformer.transactions` AS t
GROUP BY t.mcc
LIMIT 10;

-- 이것이 Top 10
SELECT t.mcc, COUNT(*) AS tx_cnt
FROM `finda-week7-505502.tabformer.transactions` AS t
GROUP BY t.mcc
ORDER BY tx_cnt DESC
LIMIT 10;
```

**Top N에는 반드시 `ORDER BY`가 따라붙습니다.**

---

## 쿼리 한 개를 11단계로 따라가기

아래 쿼리가 실제로 어떤 순서로 처리되는지 보겠습니다.

```sql
SELECT
    u.gender,
    COUNT(*)                    AS tx_cnt,
    ROUND(AVG(c.amount_usd), 2) AS avg_amount
FROM `finda-week7-505502.tabformer.silver_transactions` AS c
INNER JOIN `finda-week7-505502.tabformer.users` AS u
    ON c.user_id = u.user_id
WHERE c.tx_date >= DATE "2018-01-01"
GROUP BY u.gender
HAVING COUNT(*) >= 1000
ORDER BY avg_amount DESC
LIMIT 10;
```

| 실행 | 무슨 일이 일어나는가 | 이 시점에 존재하는 것 |
|---:|---|---|
| 1 | `silver_transactions`를 읽는다 | 거래 원본 행 |
| 2 | `users`를 붙인다 | 거래 + 사용자 정보 |
| 3 | 2018년 이후만 남긴다 | 필터된 행 |
| 4 | 성별로 묶는다 | 성별 그룹 |
| 5 | 1,000건 미만 그룹을 버린다 | 살아남은 그룹 |
| 6 | (윈도우 함수 없음) | — |
| 7 | (`QUALIFY` 없음) | — |
| 8 | `gender`, `tx_cnt`, `avg_amount`를 만든다 | **여기서 처음 별칭이 생긴다** |
| 9 | (`DISTINCT` 없음) | — |
| 10 | `avg_amount` 내림차순 정렬 | 정렬된 결과 |
| 11 | 위에서 10행만 반환 | 최종 출력 |

8번에서야 `avg_amount`라는 이름이 생기기 때문에,
그보다 **뒤에 실행되는** `ORDER BY`(10번)에서는 이 별칭을 쓸 수 있습니다.
반면 **앞에서 실행되는** `WHERE`(3번)에서는 쓸 수 없습니다.

### 별칭을 쓸 수 있는 곳과 없는 곳

| 절 | `SELECT` 별칭 사용 | 이유 |
|---|:---:|---|
| `FROM` / `JOIN` | 불가 | `SELECT`(8번)보다 먼저 실행(1~2번) |
| `WHERE` | 불가 | 3번에 실행 — 별칭이 아직 없음 |
| `GROUP BY` | **가능** | BigQuery가 편의를 위해 허용 |
| `ORDER BY` | **가능** | 10번에 실행 — 별칭이 이미 있음 |

`GROUP BY`가 실행 순서상으로는 `SELECT`보다 앞(4번)인데도 별칭이 통하는 것은
**BigQuery가 편의를 위해 허용**해 주기 때문입니다. 표준 SQL을 엄격히 따르는 다른 DB에서는
같은 쿼리가 실패할 수 있으니, 이식을 염두에 둔 코드라면 식을 그대로 반복하는 편이 안전합니다.

```sql
-- 7주차 Day 2 실습에서 쓴 패턴 (BigQuery에서 동작)
SELECT
    CASE
        WHEN u.current_age < 30 THEN "20대 이하"
        WHEN u.current_age < 40 THEN "30대"
        ELSE "40대 이상"
    END        AS age_group,
    COUNT(*)   AS tx_cnt
FROM `finda-week7-505502.tabformer.transactions` AS t
INNER JOIN `finda-week7-505502.tabformer.users` AS u
    ON t.user_id = u.user_id
GROUP BY age_group       -- 별칭으로 묶기 (BigQuery 허용)
ORDER BY tx_cnt DESC     -- 별칭으로 정렬
```

---

## 오류 메시지로 원인 찾기

| 오류 메시지(요지) | 진짜 원인 | 해결 |
|---|---|---|
| `Unrecognized name: amount_usd` | `WHERE`에서 `SELECT` 별칭을 참조함 | 식을 반복하거나 `WITH`로 분리 |
| `Aggregate function COUNT not allowed in WHERE` | 집계를 `WHERE`로 거르려 함 | `HAVING`으로 옮기기 |
| `Analytic function not allowed in WHERE` | 윈도우 결과를 `WHERE`로 거르려 함 | `QUALIFY` 또는 `WITH`로 감싸기 |
| `SELECT list expression references column ... which is neither grouped nor aggregated` | `GROUP BY`에 없는 컬럼을 `SELECT`에 씀 | `GROUP BY`에 추가하거나 집계 함수로 감싸기 |
| Top N인데 결과가 매번 다름 | `ORDER BY` 없이 `LIMIT`만 씀 | `ORDER BY` 추가 |

---

## 정리

- (1) 쓰는 순서는 `SELECT`부터, 실행 순서는 `FROM`부터입니다.
- (2) `SELECT`가 8번째라는 사실 하나가 "별칭을 어디서 쓸 수 있는가"를 결정합니다.
- (3) 필터가 세 종류인 이유도 실행 순서 때문입니다. `WHERE`(행) → `HAVING`(그룹) → `QUALIFY`(윈도우).
- (4) 오류 메시지를 만나면 "이 절이 몇 번째에 실행되지?"를 먼저 떠올리세요. 대부분 거기서 답이 나옵니다.

---

## 함께 보기

- [BigQuery 주요 문법 정리](bigquery-syntax.md) — 이 순서대로 실행되는 **문법들의 목록**
- [쿼리 가독성을 높이는 팁](query-style-tips.md) — 같은 쿼리를 **읽기 좋게 쓰는 법**

---

