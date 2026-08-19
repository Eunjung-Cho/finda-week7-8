---
tags: [FinDA, 8주차, 사전배포, 워크시트, 윈도우함수, 프레임]
status: draft-v0.1
---

# 8주차 Day 1 사전 배포 워크시트: 윈도우 프레임 손풀기

> 수업 전 30분 분량. 토요일 수업(윈도우 함수 심화)의 핵심인 **프레임(ROWS BETWEEN …)**을 미리 손으로 풀어봅니다. 모든 데이터는 쿼리 안에 들어 있어서 **테이블 적재가 필요 없고, 처리 바이트도 사실상 0**입니다. BigQuery 콘솔만 열면 됩니다.

## 0. 왜 이걸 미리 풀어야 하나

수업에서 이런 쿼리가 나옵니다.

```sql
SUM(spend) OVER (ORDER BY d ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
```

이 한 줄에 세 가지 개념이 압축되어 있습니다 — (1) 창의 정렬 (2) 프레임의 범위 (3) 생략했을 때의 기본값. 이 워크시트로 셋을 미리 손에 익히면, 수업에서는 응용(이동평균, 볼린저 밴드)에 바로 들어갈 수 있습니다.

## 1. 장난감 데이터

가상 사용자의 6월 카드 소비 6건입니다. **6월 3일에 두 건**이 있다는 점을 기억하세요 — 뒤에서 중요해집니다.

```sql
WITH toy AS (
    SELECT DATE '2019-06-01' AS d, 100 AS spend UNION ALL
    SELECT DATE '2019-06-02', 200 UNION ALL
    SELECT DATE '2019-06-03', 150 UNION ALL
    SELECT DATE '2019-06-03', 50 UNION ALL
    SELECT DATE '2019-06-04', 300 UNION ALL
    SELECT DATE '2019-06-05', 100
)
SELECT * FROM toy ORDER BY d
```

## STEP 1. 손계산 — 실행하기 전에 표부터 채우세요

아래 두 컬럼을 **연필로** 계산해 채우세요. 쿼리는 아직 실행하지 않습니다.

- (A) `SUM(spend) OVER (ORDER BY d ROWS UNBOUNDED PRECEDING)` — 행 순서 누적합
- (B) `SUM(spend) OVER (ORDER BY d)` — **프레임을 생략**한 누적합

| d | spend | (A) ROWS 누적 | (B) 프레임 생략 누적 |
| --- | --- | --- | --- |
| 6/1 | 100 | | |
| 6/2 | 200 | | |
| 6/3 | 150 | | |
| 6/3 | 50 | | |
| 6/4 | 300 | | |
| 6/5 | 100 | | |

> 생각할 것: (A)와 (B)가 다르게 나오는 행이 있나요? 있다면 왜 하필 **그 행**인가요?

## STEP 2. 실행해서 확인

```sql
WITH toy AS (
    -- (위의 장난감 데이터 그대로)
)
SELECT
    t.d, t.spend,
    SUM(t.spend) OVER (ORDER BY t.d
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS a_rows,
    SUM(t.spend) OVER (ORDER BY t.d) AS b_default
FROM toy AS t
ORDER BY t.d
```

손계산과 비교하세요. 6월 3일 두 행에서 (B)가 똑같이 500이 나왔다면 — 정상입니다. 이유는 STEP 3에서.

## STEP 3. 세 가지 문답 — 빈칸을 채우세요

- (1) ORDER BY만 쓰고 프레임을 생략하면 기본 프레임은 `______ BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`다. (ROWS일까 RANGE일까?)
- (2) RANGE는 행 개수가 아니라 `______ ______의 값`으로 창을 자른다. 그래서 같은 날짜(동점) 행들은 (같은 / 다른) 누적값을 가진다.
- (3) 3일 이동평균의 프레임은 `ROWS BETWEEN ______ PRECEDING AND ______ ______`다.

## STEP 4. 일부러 망가뜨리기 — 두 가지 실험

**실험 1.** STEP 2 쿼리에서 `ORDER BY t.d`를 창 안에서 지우면(`SUM(t.spend) OVER ()`) 결과가 어떻게 될까요? 예상을 적고 실행해서 확인하세요.

- 예상: ______
- 관찰: ______

**실험 2.** 3일 이동평균을 만들려다 방향을 반대로 쓴 사람이 있습니다.

```sql
AVG(t.spend) OVER (ORDER BY t.d ROWS BETWEEN CURRENT ROW AND 2 FOLLOWING)
```

이 창은 과거가 아니라 ______를 보고 있습니다. 시계열 분석에서 이 실수가 위험한 이유를 한 줄로 적으세요 (힌트: "그 시점에 알 수 없었던 정보").

- 답: ______

## 정답과 해설 (다 풀기 전에는 열지 마세요)

STEP 1 정답:

| d | spend | (A) ROWS 누적 | (B) 프레임 생략 누적 |
| --- | --- | --- | --- |
| 6/1 | 100 | 100 | 100 |
| 6/2 | 200 | 300 | 300 |
| 6/3 | 150 | 450 | **500** |
| 6/3 | 50 | 500 | **500** |
| 6/4 | 300 | 800 | 800 |
| 6/5 | 100 | 900 | 900 |

STEP 3 정답: (1) **RANGE** — 프레임 생략 시 기본값은 RANGE입니다. 그래서 (B)에서 같은 날짜 두 행이 한 묶음(500)이 됩니다. (2) **ORDER BY의 값** / **같은** 누적값. (3) `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` — "3일"은 자기 자신 + 앞의 2행입니다.

STEP 4 해설: 실험 1 — ORDER BY가 없으면 프레임 개념이 사라지고 전체 합(900)이 모든 행에 붙습니다. 실험 2 — 미래를 보는 창입니다. 시계열에서는 "그 시점에 알 수 없었던 정보"(미래 값)로 지표를 만들면 백테스트가 실제보다 좋아 보이는 **미리보기 편향(lookahead bias)**이 생깁니다. 탐지·예측 지표의 창은 언제나 과거를 향해야 합니다.

---

