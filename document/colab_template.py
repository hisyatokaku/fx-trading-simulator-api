# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown] id="ce377058-5ed6-4ea1-8b05-2de37a869015"
# # システム概要 - 仕様書
#
# ## 1. **課題**
# - **目標**: FXのトレードを繰り返し、日本円での資産の最大化。
# - **評価**: 当日案内する 5 つの評価シナリオを同一の戦略で 1 回ずつ実行し、5 つの最終資産（JPY 換算）の中央値で評価します。提出（実行）は 1 回限りです。
#
# ---
#
# ## 2. **条件**
# - **初期資産**: 1,000,000円
# - **トレード頻度**: 1 分刻み（1 シナリオ = 1,439 ステップ）。各ステップで FX レートを基に貨幣の取引が可能。
# - **取引可能な通貨**: JPY, USD, EUR, GBP, AUD, NZD, CAD, CHF, TRY, ZAR, MXN, NOK, SEK, HKD の 14 通貨。（以下のテンプレートコードは例として JPY, USD, EUR, AUD, HKD の 5 通貨を扱います。CURRENCY_LIST に追加すれば他の通貨も戦略に組み込めます。）
# - **評価方法**: セッション終了時に全資産をその時点のレートで JPY に変換し、その額を評価。
#
# ---
#
# ## 3. **問題セット**
# 各問題セットでは、以下の情報が提供されます：
# - **シナリオ名**
# - **取引開始日時**
# - **取引終了日時**
#
# 問題セット（いずれも 1 分刻み・初期資産 1,000,000 円。TEST4 以外は 1 日分の 1,439 ステップ）:
# - テスト用（いつでも実行可）
#   - TEST0: 2026-06-01 の 1 日
#   - TEST1: 2026-06-02 の 1 日
#   - TEST2: 2026-06-03 の 1 日
#   - TEST3: 2026-06-04 の 1 日
#   - TEST4: 2026-06-05 の 00:00〜16:59（1,019 ステップ）
#   - TEST5: 2026-06-09 の 1 日
#   - TEST6: 2026-06-10 の 1 日
#
# - 本番用（一回だけ実行可）:
#   - 5 つのシナリオ名を当日午後会場で発表します。
#
#
# 当日皆様にお配りする `user_id` を用いないと、セッションを開始することはできません。
#
# ---
#
# ## 4. **API 概要**
# APIに関する詳細が知りたい場合は本セクションをご覧ください．
# <details><summary>API概要</summary>
#
# システムは以下のAPIを使用してトレードセッションを管理します。
#
# 1. **セッション開始**:
#    - **概要**: 指定されたシナリオと `user_id` に基づいて、トレードセッションを開始します。
#    - **エンドポイント**: `POST /api/trade/start/<scenario_name>/<user_id>`
#    - **user_id**: `user_id` は皆さんにご入場の際にお配りした文字列をお使いください。
#    - **current_datetime**: 現在の日時
#    - **time_interval_seconds**: 1 tick の間隔（秒）
#    - **jpy_balance**: 現在の日本円換算での総資産（開始直後は null）
#    - **is_complete**: セッションが終了しているかどうかを表すフラグ
#    - **balances**: 現在のそれぞれの貨幣の資産の量
#    - **レスポンス例**:
#      ```json
#      {
#        "id": 0,
#        "user_id": "abc123",
#        "scenario_name": "TEST1",
#        "start_datetime": "2016-01-04T00:00:00",
#        "end_datetime": "2016-01-04T23:59:00",
#        "current_datetime": "2016-01-04T00:00:00",
#        "time_interval_seconds": 60,
#        "is_complete": false,
#        "jpy_balance": null,
#        "balances": {
#          "JPY": 1000000.0,
#          "USD": 0.0
#        }
#      }
#      ```
#
# 2. **取引の実行**:
#    - **概要**: セッションの現在日時において、指定された取引を実行します。指定した量の貨幣をcurrency_fromからcurrency_toへ、その日時の為替レートで変換し、セッションの日時を1ステップ進めます。
#    - **エンドポイント**: `POST /api/trade/next`
#    - **リクエスト例**:
#      ```json
#      {
#        "session_id": 0,
#        "exchange_requests": [
#          {
#            "currency_from": "JPY",
#            "currency_to": "USD",
#            "amount": 1000
#          },
#          {
#            "currency_from": "JPY",
#            "currency_to": "AUD",
#            "amount": 1000
#          }
#        ]
#      }
#      ```
#    - **レスポンス例**（balances が取引結果で更新され、current_datetime が翌ステップに進み、rates はその日時の**対JPYレート**、jpy_balance は総資産のJPY換算値）:
#      ```json
#      {
#        "session_id": 0,
#        "previous_datetime": "2016-01-04T00:00:00",
#        "current_datetime": "2016-01-04T00:01:00",
#        "is_complete": false,
#        "balances": {
#          "JPY": 998000.0,
#          "USD": 8.305,
#          "AUD": 11.415
#        },
#        "trades": [
#          {"currency_from": "JPY", "currency_to": "USD", "amount_from": 1000.0, "amount_to": 8.305, "rate": 120.4}
#        ],
#        "rates": {
#          "USD": 119.27,
#          "EUR": 129.17
#        },
#        "jpy_balance": 999969.03
#      }
#      ```
#     - これをcurrent_datetime == end_datetime になるまで繰り返す。その際、is_complete == trueとなっている。
#
# 3. **FxRateの参照**:
#    - **エンドポイント**:
#      - `GET /api/rate/{timestamp}`（例: `/api/rate/2016-01-04T00:00:00`）
#    - **レスポンス例**（**対JPYレート**。通貨ペアのクロスレートが必要な場合は割り算で求める: EUR/USD = rates["EUR"] / rates["USD"]）:
#      ```json
#      {
#          "timestamp": "2016-01-04T00:00:00",
#          "rates": {
#              "USD": 120.4,
#              "EUR": 130.59
#          }
#      }
#      ```
# **その他詳細**:
# - exchange_requestsのamountが保有するcurrency_fromの残高より多い場合、そのリクエストは実行されません（スキップ）。
# - amountには正の値を指定してください。
# - rateのAPIはレートデータが投入されている日時のみ返します。データが無い日時は404を返します。
# - 実際のレスポンスの balances / rates には例より多くの通貨（14 通貨 / 13 通貨）が含まれます。
#
# </details>
#
# ---
#
# ## 5. **実行**
#
# 以下のコード群を上から順に実行することで、セッション開始に必要な事前準備を行うことができます。
#
#
# 自作の Session クラスを実装する際には、BaseTradingSession を継承し、strategy メソッドを override してください。コード群の下部に、サンプルとして FixedStrategySession, ContrarianStrategySession が提供されています。
#
# 詳細は、BaseTradingSession の strategy メソッド部分に記載されたコメントを参照してください。
#
# session.proceed_one_tick() を実行すると、strategy メソッドが 1 度だけ呼ばれ、セッション内部の tick (self.current_tick) が次の tick に進みます。session.proceed_to_end() を実行すると、セッションが終了するまで strategy メソッドを繰り返し呼び出します。
#
# ---

# %% id="f39d5052-553f-4889-b683-e8dec9f087cc"
# ライブラリをインポート
import requests
from datetime import datetime, timedelta
from typing import Union


# %% id="a95f2670-1a02-48ce-ae94-ac7fdb12254f"
# 共通変数を定義
import os

CURRENCY_LIST = ['JPY','USD','AUD','HKD','EUR']
CURRENCY_PAIR = [f"{currency1}/{currency2}" for currency1 in CURRENCY_LIST for currency2 in CURRENCY_LIST if currency1 != currency2]
BASE_URL = os.environ.get("FX_API_BASE_URL", 'http://34.146.231.219:8000')  # TLJH では内部IP、Colab では外部IP
START_URL = BASE_URL + '/api/trade/start/{}/{}'
NEXT_URL = BASE_URL + '/api/trade/next'
RATE_URL = BASE_URL + '/api/rate/{}'
HTTP = requests.Session()

# 当日午後会場で発表される 5 つの評価シナリオ名をすべて入れる
EVAL_TEST_CASES = [
    "TODO: fill here",
]

# 自分の user_id に置き換える
USER_ID = 'dummy'

######## ここから下は編集しないこと ########
if USER_ID == 'dummy':
    raise ValueError("Replace USER_ID with your own user_id.")
##################################


# %% id="fa072731-cbea-4c83-acd0-0882689cda60"
# 共通関数を定義

def fetch_rates_to_jpy(timestamp: str) -> dict[str, float]:
    """
    API から `timestamp` 時点の対 JPY レートを取得する。

    API は {"timestamp": ..., "rates": {"USD": 147.2, ...}} を返す。
    各値は、その通貨 1 単位あたりの JPY 価値を表す。

    戻り値:
        {'JPY': 1.0} を含む {currency: rate_to_jpy} 形式の辞書。
        指定日時のレートが存在しない場合（HTTP 404）は空の辞書。
    """
    resp = HTTP.get(RATE_URL.format(timestamp))
    if resp.status_code != 200:
        return {}
    rates = {k: float(v) for k, v in resp.json()['rates'].items()}
    rates['JPY'] = 1.0
    return rates

def pair_rates_from_jpy_rates(rates_to_jpy: dict[str, float]) -> dict[str, float]:
    """
    対 JPY レートを 'BASE/QUOTE' 形式のクロスレートへ変換する。

    BASE/QUOTE =（BASE の JPY 価値）/（QUOTE の JPY 価値）。

    使用例:
        >>> pair_rates_from_jpy_rates({'USD': 150.0, 'EUR': 165.0, 'JPY': 1.0})['EUR/USD']
        1.1
    """
    result = {}
    for pair in CURRENCY_PAIR:
        base, quote = pair.split('/')
        if base in rates_to_jpy and quote in rates_to_jpy:
            result[pair] = rates_to_jpy[base] / rates_to_jpy[quote]
    return result

def fetch_rates_for_last_n_ticks(
    end: str, n: int, tick_seconds: int
) -> dict[str, list[float]]:
    """
    `end` の直前にある n 個の tick の FX レートを取得する。

    引数:
        end: 基準となる tick の ISO 形式日時。
        n: 取得する tick 数。
        tick_seconds: tick 間隔（秒）。

    戻り値:
        各通貨ペアを tick 順のレート一覧に対応させた辞書。
        レートが記録されていない tick は読み飛ばす。

    使用例:
        >>> fetch_rates_for_last_n_ticks("2026-06-02T00:03:00", 3, 60)
        {
            'USD/JPY': [147.2, 147.4, 147.8],
            'EUR/JPY': [157.9, 158.1, 158.6],
            ...
        }
    """
    end_tick = datetime.fromisoformat(end)
    result: dict[str, list[float]] = {pair: [] for pair in CURRENCY_PAIR}

    for offset in range(n, 0, -1):  # end の n tick 前から古い順にたどる
        tick = (end_tick - timedelta(seconds=tick_seconds * offset)).isoformat()
        jpy_rates = fetch_rates_to_jpy(tick)
        if not jpy_rates:
            continue  # この tick のレートが記録されていない場合は読み飛ばす
        for pair, rate in pair_rates_from_jpy_rates(jpy_rates).items():
            result[pair].append(rate)

    return result

def append_tick_rates(
    currency_pair_to_rates: dict[str, list[float]],
    tick_rates: dict[str, float]
) -> None:
    """
    1 tick 分のレートを既存の currency_pair_to_rates 辞書へ追加する。

    引数:
        currency_pair_to_rates: 既存の {pair: [rates...]} 形式の辞書。
        tick_rates: 取引 API レスポンスの 'rates' に含まれる、
            取引を実行した tick の {currency: rate_to_jpy} 形式の対 JPY レート。
            各通貨ペアのクロスレートを計算してから追加する。

    使用例:
        >>> rates = {"USD/JPY": [147.5, 147.8]}
        >>> append_tick_rates(rates, {"USD": 148.0})
        >>> rates
        {'USD/JPY': [147.5, 147.8, 148.0]}
    """
    rates_to_jpy = {k: float(v) for k, v in tick_rates.items()}
    rates_to_jpy['JPY'] = 1.0
    for pair, rate in pair_rates_from_jpy_rates(rates_to_jpy).items():
        currency_pair_to_rates[pair].append(rate)

def calc_simple_moving_average(values: list[float], window: int) -> list[float]:
    """
    数値リストの単純移動平均（SMA）を計算する。

    各位置 i について、i で終わる直近 `window` 個の平均を求める。
    先頭付近で値が `window` 個に満たない場合は、存在する値だけを使用する。

    引数:
        values: 数値のリスト。
        window: 平均する点数（1 以上）。

    戻り値:
        `values` と同じ長さの SMA 値リスト。

    使用例:
        >>> calc_simple_moving_average([1, 2, 3, 4, 5], 3)
        [1.0, 1.5, 2.0, 3.0, 4.0]
    """
    return [
        sum(values[max(0, i - window + 1):i + 1]) / len(values[max(0, i - window + 1):i + 1])
        for i in range(len(values))
    ]



# %% id="E39lVYGEN0ZO"
# 評価提出処理
from tqdm.auto import tqdm

def eval_submission(test_cases: Union[list, str], StrategySession: type, user_id=None, *args, **kwargs):
    if user_id is None:
        user_id = USER_ID  # 呼び出し時点の USER_ID を参照する
    # 単一の文字列もリストへ変換し、処理を統一する
    if isinstance(test_cases, str):
        test_cases = [test_cases]

    # 1. 評価実行前の確認
    evaluation_cases = [tc for tc in test_cases if "EVAL" in tc]

    if evaluation_cases:
        print(f"This batch contains {len(evaluation_cases)} evaluation submission(s). "
              "Evaluation can only be submitted ONCE: all 5 scenarios run with the same strategy, "
              "and your score is the MEDIAN of the 5 final JPY balances.")
        ans = input("Type 'yes' to proceed: ")
        if ans != "yes":
            print("Execution aborted.")
            return

        # 誤実行を防ぐため、最初の評価シナリオ名を入力して確認する
        print(f"To confirm, type the exact name of the first evaluation case ({evaluation_cases[0]}):")
        ans = input()
        if ans != evaluation_cases[0]:
            print("Execution aborted.")
            return

        print("DO NOT INTERUPT: An interruped test is also evaluation as one submission")

    # 2. 実行ループ
    print(f"Proceeding {len(test_cases)} session(s)...")
    for test_case in tqdm(test_cases):
        session = StrategySession(test_case, user_id, *args, **kwargs)
        session.proceed_to_end()

class BaseTradingSession:
    def __init__(self, test_case, user_id):
        response = HTTP.post(START_URL.format(test_case, user_id))
        response.raise_for_status()  # シナリオ名や user_id の誤りを HTTP エラーとして即検出する
        self.test_case = test_case
        session_info = response.json()  # 詳細は「4. API 概要」を参照
        self.session_id = session_info['id']
        self.is_complete = session_info['is_complete']
        self.start_tick = session_info['start_datetime']
        self.end_tick = session_info['end_datetime']
        self.current_tick = session_info['current_datetime']
        self.tick_interval_seconds = session_info['time_interval_seconds']
        self.currency_to_balance = session_info['balances']
        # レート履歴は空から始まり、tick を進めるたびに 1 件ずつ増える
        self.currency_pair_to_rates = {pair: [] for pair in CURRENCY_PAIR}

    def proceed_one_tick(self):
        if self.is_complete:
            print("already end")
            return
        exchange_request_body = self.get_exchange_requests_body()
        next_info = self.post_trade_request(exchange_request_body)
        if self.is_complete:
            print(f'JPY: {next_info["jpy_balance"]}')

    def proceed_to_end(self):
        remaining_seconds = (
            datetime.fromisoformat(self.end_tick)
            - datetime.fromisoformat(self.current_tick)
        ).total_seconds()
        remaining_ticks = max(
            0,
            int((remaining_seconds + self.tick_interval_seconds - 1) // self.tick_interval_seconds)
        )
        with tqdm(total=remaining_ticks, desc=self.test_case, unit='tick') as progress:
            while not self.is_complete:
                self.proceed_one_tick()
                progress.update(1)

    def get_exchange_requests_body(self):
        # strategy() は従来どおり camelCase で書けるようにし、ここで API の形式に変換する
        exchange_requests = [
            {'currency_from': r['currencyFrom'],
             'currency_to': r['currencyTo'],
             'amount': r['amount']}
            for r in self.strategy()
        ]
        return {
            'session_id': self.session_id,
            'exchange_requests': exchange_requests
        }

    def strategy(self):
        """
        独自の取引戦略を実装するには、サブクラスでこのメソッドをオーバーライドする。

        戻り値:
            取引リクエストオブジェクトのリスト（空でもよい）。
            戻り値の例:
                [
                  {"currencyFrom": "JPY", "currencyTo": "USD", "amount": 1000},
                  {"currencyFrom": "JPY", "currencyTo": "AUD", "amount": 1000}
                ]

        利用できるインスタンス変数:
            self.is_complete : bool
                セッションが終了したかどうか。True の場合、それ以上取引は処理されない。
            self.start_tick : str
                セッション開始 tick の日時（例: "2026-06-02T00:00:00"）。
            self.end_tick : str
                セッション終了 tick の日時。
            self.current_tick : str
                セッションの現在 tick の日時（リクエストごとに次の tick へ進む）。
            self.tick_interval_seconds : int
                tick 間隔（秒）。
            self.currency_to_balance : dict[str, float]
                通貨ごとの現在残高。例: {"JPY": 1000000, "USD": 0.0, ...}。
            self.currency_pair_to_rates : dict[str, list[float]]
                通貨ペアごとの FX レート履歴。セッション開始時は空で、取引リクエスト
                送信後、tick ごとに `append_tick_rates(...)` で 1 件ずつ増える。
                開始前のレートが必要な場合は `fetch_rates_for_last_n_ticks(...)` で
                取得できる（レートが記録されていない日時では空になる）。

        """
        pass

    def post_trade_request(self, request_body_next):
        response = HTTP.post(NEXT_URL, json=request_body_next)
        response.raise_for_status()
        next_info = response.json()
        append_tick_rates(self.currency_pair_to_rates, next_info.get('rates', {}))
        self.current_tick = next_info['current_datetime']
        self.currency_to_balance = next_info['balances']
        self.is_complete = next_info['is_complete']
        return next_info


# %% id="umcKjREzH1__"
# 解答例
class FixedStrategySession(BaseTradingSession):
    """`strategy` をオーバーライドして独自の取引計画を定義する例。"""

    def strategy(self):
        """各 tick で JPY 1000 → USD、JPY 1000 → AUD を実行する固定計画。"""
        return [
            {'currencyFrom': 'JPY', 'currencyTo': 'USD', 'amount': 1000},
            {'currencyFrom': 'JPY', 'currencyTo': 'AUD', 'amount': 1000}
        ]

session = FixedStrategySession(test_case="TEST1", user_id=USER_ID)

# %% id="wHm-s4qDaE6P"
# 1 tick だけ実行したい場合に使用する
session.proceed_one_tick()

# %% id="9b9F4QRU4q2h"
# 終了まで実行したい場合に使用する
session.proceed_to_end()


# %% id="db7dfb8d-9832-43cb-9565-fa4e49ffdd80"
# 解答例 (2): 逆張り戦略
# 保有通貨が別の通貨に対して {x} tick 連続で上昇した場合、
# その通貨へ {y}% を配分し直す。
# 例: USD/JPY が 3 tick 連続で [130, 129, 128] と下落した場合、
# 円がドルに対して上昇しているため、円をドルへ交換する。

class ContrarianStrategySession(BaseTradingSession):
    def __init__(self, test_case, user_id, x, y):
        super().__init__(test_case, user_id)
        self.x = x
        self.y = y

    def strategy(self):
        exchange_requests = []
        for currency, balance in self.currency_to_balance.items():
            if balance > 0:
                currency_pairs = [pair for pair in CURRENCY_PAIR if pair.endswith('/' + currency)]
                for currency_pair in currency_pairs:
                    # 直近 x tick のレートを確認する
                    rates = self.currency_pair_to_rates[currency_pair][-self.x:]
                    if len(rates) == self.x and all(rates[i] > rates[i + 1] for i in range(len(rates) - 1)):
                        exchange_requests.append({
                            'currencyFrom': currency,
                            'currencyTo': currency_pair[:3],
                            'amount': balance * self.y / 100.0
                        })
                        break
        return exchange_requests

session = ContrarianStrategySession(test_case="TEST1", user_id=USER_ID, x=5, y=30)
session.proceed_to_end()


# %% [markdown]
# ### 戦略のアイデア例: ゴールデンクロス / デッドクロス
#
# 短期移動平均（例: 直近 5 tick の平均）が長期移動平均（例: 直近 10 tick の平均）を
# 上抜けたら「上昇トレンド」とみなしてその通貨を買い、下抜けたら売るという
# 古典的な手法もあります。
#
# ContrarianStrategySession の実装を参考に、BaseTradingSession を継承して
# 自分で実装してみてください（移動平均の計算には `calc_simple_moving_average()` が使えます）。
#

# %% id="SqIO9vvvzXgQ"
# 本番提出用
# eval_submission(EVAL_TEST_CASES, ContrarianStrategySession, x=5, y=30)
