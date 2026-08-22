"""OpenDART 재무제표를 BigQuery로 적재하는 주간 배치.

새 분기 보고서가 올라왔는지는 알림이 아니라 폴링으로 판단한다.
아직 제출되지 않은 분기를 요청하면 DART가 status "013"(데이터 없음)을
돌려주므로, 그때는 조용히 건너뛰고 다음 분기를 확인한다.

멱등 패턴 (1) 전체 재적재를 쓴다. 대상 기업이 수십 곳으로 늘기 전까지는
매번 전부 다시 부어도 API 호출 수백 회, 수만 행 수준이고
BigQuery 로드 잡은 과금 대상이 아니라서 비용이 들지 않는다.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone

import pandas as pd
import requests
from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from google.oauth2 import service_account
from pandas_gbq import to_gbq

API_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"

# 수집 대상. corp_code는 corpCode.xml 기준 (삼성전자 005930 -> 00126380)
TARGETS = {
    "00126380": "삼성전자",
    "00164779": "SK하이닉스",
}

REPORTS = {
    "11013": "1분기",
    "11012": "반기",
    "11014": "3분기",
    "11011": "사업보고서",
}

FS_DIVS = ["CFS"]        # 연결. 별도까지 쌓으려면 "OFS" 추가
START_YEAR = 2020

PROJECT = os.environ.get("GCP_PROJECT", "finda-week7")
DATASET = os.environ.get("BQ_DATASET", "dart")
TABLE = os.environ.get("BQ_TABLE", "fs_long")
LOCATION = os.environ.get("BQ_LOCATION", "asia-northeast3")
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in {"1", "true", "yes"}

# 응답에서 가져오는 컬럼. 기업·연도·보고서 구분은 우리가 보낸 요청 값이
# 확실하므로 응답에서 읽지 않고 직접 채운다.
PAYLOAD_COLS = ["sj_div", "sj_nm", "account_id", "account_nm", "ord", "thstrm_amount"]

COLUMN_ORDER = [
    "corp_code", "corp_name", "bsns_year", "reprt_code", "fs_div",
    "sj_div", "sj_nm", "account_id", "account_nm", "ord",
    "amount_krw", "loaded_at",
]


def credentials():
    """GitHub Actions에서는 시크릿의 서비스 계정 JSON, 로컬에서는 gcloud ADC."""
    raw = os.environ.get("GCP_SA_KEY")
    if not raw:
        return None
    return service_account.Credentials.from_service_account_info(json.loads(raw))


def ensure_dataset(creds) -> None:
    client = bigquery.Client(project=PROJECT, credentials=creds, location=LOCATION)
    dataset_id = f"{PROJECT}.{DATASET}"
    try:
        client.get_dataset(dataset_id)
    except NotFound:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = LOCATION
        client.create_dataset(dataset)
        print(f"데이터셋 생성: {dataset_id} ({LOCATION})")


def fetch(session, api_key, corp_code, year, reprt_code, fs_div) -> dict:
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bsns_year": str(year),
        "reprt_code": reprt_code,
        "fs_div": fs_div,
    }
    last_error = None
    for attempt in range(3):
        try:
            res = session.get(API_URL, params=params, timeout=30)
            res.raise_for_status()
            return res.json()
        except (requests.RequestException, ValueError) as error:
            last_error = error
            time.sleep(2**attempt)
    raise RuntimeError(
        f"DART 호출 실패: {corp_code} {year} {reprt_code} {fs_div}"
    ) from last_error


def clean_amount(s: pd.Series) -> pd.Series:
    """콤마 제거 후 숫자로. 실패하면 NaN (SAFE_CAST의 pandas 버전)."""
    return pd.to_numeric(
        s.astype(str).str.replace(",", "", regex=False), errors="coerce"
    )


def as_integer_won(s: pd.Series) -> pd.Series:
    """금액을 nullable 정수로. 원 단위라 정수가 맞고, BigQuery INTEGER로 실린다.

    NaN이 섞이면 to_numeric이 float64를 돌려주는데, 그대로 적재하면
    강의 2-2가 만드는 INTEGER 스키마와 어긋나고 금액을 부동소수점으로
    다루게 된다. 소수가 실제로 섞여 있을 때만 float를 유지한다.
    """
    non_null = s.dropna()
    if not non_null.empty and (non_null % 1 != 0).any():
        print("경고: 소수점이 있는 금액이 있어 FLOAT64로 적재합니다.")
        return s
    return s.astype("Int64")


def to_frame(items, corp_code, corp_name, year, reprt_code, fs_div) -> pd.DataFrame:
    raw = pd.DataFrame(items)
    fs = raw.reindex(columns=PAYLOAD_COLS).copy()
    fs["corp_code"] = corp_code
    fs["corp_name"] = corp_name
    fs["bsns_year"] = int(year)
    fs["reprt_code"] = reprt_code
    fs["fs_div"] = fs_div
    fs["amount_krw"] = clean_amount(fs["thstrm_amount"])
    fs["ord"] = pd.to_numeric(fs["ord"], errors="coerce").astype("Int64")
    return fs.drop(columns=["thstrm_amount"])


def collect(api_key) -> tuple[list[pd.DataFrame], int]:
    this_year = datetime.now(timezone.utc).year
    session = requests.Session()
    frames: list[pd.DataFrame] = []
    pending = 0

    for corp_code, corp_name in TARGETS.items():
        for year in range(START_YEAR, this_year + 1):
            for reprt_code, reprt_name in REPORTS.items():
                for fs_div in FS_DIVS:
                    data = fetch(session, api_key, corp_code, year, reprt_code, fs_div)
                    status = data.get("status")

                    if status == "013":          # 아직 공시 전
                        pending += 1
                        continue
                    if status == "020":
                        sys.exit("DART 일일 호출 한도를 초과했습니다. 내일 다시 실행하세요.")
                    if status != "000":
                        raise RuntimeError(
                            f"{corp_name} {year} {reprt_name}: "
                            f"{status} {data.get('message')}"
                        )

                    frame = to_frame(
                        data["list"], corp_code, corp_name, year, reprt_code, fs_div
                    )
                    frames.append(frame)
                    print(f"OK   {corp_name} {year} {reprt_name} {fs_div}: {len(frame)}행")
                    time.sleep(0.2)             # DART 서버 배려

    return frames, pending


def main() -> None:
    api_key = os.environ.get("DART_API_KEY")
    if not api_key:
        sys.exit("DART_API_KEY 환경변수가 없습니다. GitHub Secrets를 확인하세요.")

    frames, pending = collect(api_key)
    print(f"\n수집 완료: {len(frames)}건, 미공시로 건너뜀 {pending}건")

    # 안전장치: DART 장애로 전부 건너뛴 상태에서 replace를 하면
    # 멀쩡한 테이블이 빈 테이블로 덮인다. 그럴 바엔 실패시킨다.
    if not frames:
        sys.exit("수집된 데이터가 없어 적재를 중단합니다 (기존 테이블 보존).")

    fs_all = pd.concat(frames, ignore_index=True)
    fs_all["amount_krw"] = as_integer_won(fs_all["amount_krw"])
    fs_all["loaded_at"] = pd.Timestamp.now(tz="UTC")
    fs_all = fs_all[COLUMN_ORDER]

    print(f"적재 대상: {len(fs_all)}행")
    print(fs_all.groupby(["corp_name", "bsns_year"]).size().to_string())

    if DRY_RUN:
        print("\nDRY_RUN=1 이므로 BigQuery 적재를 건너뜁니다.")
        return

    creds = credentials()
    ensure_dataset(creds)
    to_gbq(
        fs_all,
        destination_table=f"{DATASET}.{TABLE}",
        project_id=PROJECT,
        if_exists="replace",         # 멱등 패턴 (1): 전체 재적재
        location=LOCATION,
        credentials=creds,
        progress_bar=False,
    )
    print(f"\n적재 완료: {PROJECT}.{DATASET}.{TABLE} ({len(fs_all)}행)")


if __name__ == "__main__":
    main()
