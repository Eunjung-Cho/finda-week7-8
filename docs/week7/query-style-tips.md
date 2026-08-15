---
tags: [FinDA, 7주차, BigQuery, SQL, 스타일가이드]
status: v0.1
---

# BigQuery 쿼리를 깔끔하게 작성하는 Tip

SQL은 단순히 **실행되는 쿼리**를 작성하는 것뿐만 아니라,
**나중에 다시 봐도 이해하기 쉽고 다른 사람이 읽어도 이해할 수 있도록 작성하는 것**이 중요합니다.

아래와 같은 몇 가지 규칙을 습관화하면 훨씬 읽기 좋은 쿼리를 작성할 수 있습니다.

---

## 1. SQL 예약어와 함수는 대문자로 작성하기

`SELECT`, `FROM`, `WHERE`, `GROUP BY`와 같은 SQL 예약어와
`COUNT()`, `SUM()`, `AVG()` 같은 함수는 대문자로 작성합니다.

**Bad**

```sql
select
  user_id,
  sum(amount)
from transactions
where year = 2026
```

**Good**

```sql
SELECT
  user_id,
  SUM(amount) AS total_amount
FROM transactions
WHERE year = 2026
```

예약어와 함수가 눈에 잘 띄기 때문에 쿼리의 구조를 빠르게 파악할 수 있습니다.

---

## 2. 컬럼은 한 줄에 하나씩 작성하기

SELECT하는 컬럼이 많다면 한 줄에 몰아서 작성하지 않고 줄바꿈합니다.

**Bad**

```sql
SELECT user_id, card_id, amount, merchant_city, merchant_state
FROM transactions
```

**Good**

```sql
SELECT
  user_id,
  card_id,
  amount,
  merchant_city,
  merchant_state
FROM transactions
```

컬럼이 많아질수록 이러한 차이가 가독성에 큰 영향을 줍니다.

---

## 3. 들여쓰기를 일정하게 사용하기

서브쿼리, CTE, 조건문 등이 중첩될 때는 들여쓰기를 사용하여 구조를 표현합니다.

```sql
SELECT
  user_id,
  COUNT(*) AS transaction_count
FROM transactions
WHERE
  amount > 100
  AND merchant_state = 'CA'
GROUP BY
  user_id
```

특히 `AND`, `OR` 조건이 많아질수록 들여쓰기를 일정하게 사용하는 것이 중요합니다.

---

## 4. 의미 있는 Alias 이름 사용하기

Alias는 너무 짧거나 의미를 알 수 없는 이름보다 **테이블이나 데이터의 의미를 알 수 있는 이름**을 사용하는 것이 좋습니다.

**Bad**

```sql
SELECT
  a.user_id,
  b.card_id
FROM users AS a
LEFT JOIN cards AS b
  ON a.user_id = b.user_id
```

**Good**

```sql
SELECT
  user.user_id,
  card.card_id
FROM users AS user
LEFT JOIN cards AS card
  ON user.user_id = card.user_id
```

쿼리가 길어질수록 의미 있는 Alias가 쿼리를 이해하는 데 큰 도움이 됩니다.

---

## 5. Alias를 작성할 때 AS를 명시하기

BigQuery에서는 `AS`를 생략할 수도 있지만, 가독성을 위해 명시적으로 작성하는 것이 좋습니다.

**Bad**

```sql
SELECT
  SUM(amount) total_amount
FROM transactions
```

**Good**

```sql
SELECT
  SUM(amount) AS total_amount
FROM transactions
```

`AS`를 사용하면 원래 컬럼과 새롭게 정의한 컬럼명을 쉽게 구분할 수 있습니다.

---

## 6. 컬럼명은 snake_case 사용하기

여러 단어로 구성된 컬럼명이나 CTE 이름은 `_`를 사용하는 `snake_case` 형태로 작성하면 읽기 편합니다.

**Bad**

```text
TotalAmount
transactioncount
UserTransaction
```

**Good**

```text
total_amount
transaction_count
user_transaction
```

---

## 7. 복잡한 쿼리는 WITH(CTE)로 단계별로 나누기

하나의 쿼리에 모든 로직을 넣기보다, 의미 있는 단위로 CTE를 나누면 쿼리의 흐름을 이해하기 쉬워집니다.

```sql
WITH user_transaction AS (
  SELECT
    user_id,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount
  FROM transactions
  GROUP BY
    user_id
)
SELECT
  user_id,
  transaction_count,
  total_amount
FROM user_transaction
WHERE total_amount >= 1000
```

CTE 이름만 읽어도 해당 단계에서 무엇을 계산하는지 알 수 있도록 작성하는 것이 좋습니다.

---

## 8. 필요한 곳에 주석 작성하기

쿼리를 작성한 사람만 알고 있는 **조건의 이유, 데이터의 특징, 분석 기준** 등이 있다면 주석으로 남겨두는 것이 좋습니다.

```sql
-- 2026년 거래 데이터만 조회
SELECT
  user_id,
  amount
FROM transactions
WHERE year = 2026
```

특히 **"무엇을 하는 코드인지"보다 "왜 이렇게 처리했는지"**를 남겨두면 좋습니다.

```sql
-- 취소 거래는 실제 매출에서 제외
WHERE transaction_type != 'CANCEL'
```

---

## 9. GROUP BY / ORDER BY에는 가능하면 컬럼명을 명시하기

아래처럼 숫자로 작성할 수도 있습니다.

```sql
SELECT
  merchant_state,
  merchant_city,
  COUNT(*) AS transaction_count
FROM transactions
GROUP BY 1, 2
```

하지만 `1`, `2`가 어떤 컬럼인지 위의 SELECT 문을 다시 확인해야 합니다.
가능하면 다음처럼 작성합니다.

```sql
SELECT
  merchant_state,
  merchant_city,
  COUNT(*) AS transaction_count
FROM transactions
GROUP BY
  merchant_state,
  merchant_city
```

쿼리가 길어지거나 SELECT 컬럼 순서가 변경되었을 때도 이해하고 수정하기 쉽습니다.

---

## 10. SELECT *는 필요한 경우에만 사용하기

데이터를 간단하게 확인할 때는 `SELECT *`가 편리하지만, 실제 분석 쿼리에서는 필요한 컬럼만 명시하는 것이 좋습니다.

**데이터 확인**

```sql
SELECT *
FROM transactions
LIMIT 100
```

**분석 쿼리**

```sql
SELECT
  user_id,
  amount,
  merchant_city
FROM transactions
```

필요한 데이터가 무엇인지 명확해지고, 불필요한 컬럼을 읽지 않아 BigQuery의 데이터 처리량을 줄이는 데도 도움이 될 수 있습니다.

---

## 한눈에 보는 SQL 작성 습관

| 구분 | 권장 방법 |
|---|---|
| SQL 예약어 | `SELECT`, `FROM`, `WHERE` → 대문자 |
| 함수 | `SUM()`, `COUNT()`, `DATE()` → 대문자 |
| 컬럼명 | `total_amount`처럼 snake_case |
| 컬럼 나열 | 한 줄에 하나씩 |
| Alias | 의미 있는 이름 사용 |
| AS | 가능하면 명시적으로 작성 |
| 들여쓰기 | 일정한 규칙 유지 |
| 복잡한 로직 | `WITH`를 이용하여 단계별로 분리 |
| 주석 | 조건이나 로직의 이유를 기록 |
| GROUP BY | `GROUP BY 1`보다 컬럼명 명시 |
| SELECT * | 데이터 확인용으로 제한적으로 사용 |

> **좋은 SQL의 기준은 "짧은 SQL"이 아니라 "읽기 쉬운 SQL"입니다.**
>
> 내가 작성한 쿼리를 몇 달 뒤의 나 또는 다른 사람이 읽었을 때도 쉽게 이해할 수 있도록 작성하는 습관을 들이는 것이 좋습니다.
