# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # FXトレードシミュレーター 参加者向けガイド
#
# ## 1. 概要
#
# 本シミュレーターでは、過去の実際のFX為替レートデータを使って**仮想FXトレード**を行い、**最終日の日本円（JPY）資産の最大化**を目指します。
#
# ---
#
# ## 2. ルール
#
# | 項目 | 内容 |
# |------|------|
# | 初期資産 | 1,000,000円（JPY） |
# | トレード頻度 | 1シナリオにつき、1ステップごとに1回取引可能 |
# | 取引可能通貨 | JPY, USD, EUR, GBP, AUD, NZD, CAD, CHF, TRY, ZAR, MXN, NOK, SEK, HKD |
# | 評価方法 | 最終ステップ終了時に全資産をJPYに換算した合計額 |
#
# ---
#
# ## 3. シナリオ
#
# 各シナリオには**名前・開始日・終了日・時間間隔**が設定されています。  
# 当日お配りするシナリオ名と `user_id` を使ってセッションを開始してください。
#
# シナリオ一覧は以下のAPIで確認できます：
# ```
# GET /api/scenario/
# ```
#
# ---
#
# ## 4. APIの流れ
#
# ```
# ① セッション開始  POST /api/trade/start/{scenario}/{user_id}
#         ↓
# ② 取引実行       POST /api/trade/next   ← is_complete == true になるまで繰り返す
#         ↓
# ③ 結果確認       GET  /api/trade/session/{session_id}
# ```
#
# ---
#
# ## 5. API詳細
#
# ### 5-1. セッション開始
#
# **エンドポイント**: `POST /api/trade/start/{scenario}/{user_id}`
#
# - `scenario` : シナリオ名（例: `DEMO_3DAY`）
# - `user_id`  : 配布されたユーザーID
#
# **レスポンス例**:
# ```json
# {
#   "id": 1,
#   "user_id": "testuser",
#   "scenario_name": "DEMO_3DAY",
#   "start_datetime": "2016-01-04T00:00:00",
#   "end_datetime": "2016-12-30T00:00:00",
#   "current_datetime": "2016-01-04T00:00:00",
#   "is_complete": false,
#   "jpy_balance": null,
#   "balances": {
#     "JPY": 1000000.0,
#     "USD": 0.0,
#     "EUR": 0.0
#   }
# }
# ```
#
# | フィールド | 説明 |
# |-----------|------|
# | `id` | セッションID（以降のAPIで使用） |
# | `current_datetime` | 現在の日時 |
# | `end_datetime` | 最終日時（これになったら終了） |
# | `is_complete` | `true` になったらシミュレーション終了 |
# | `jpy_balance` | 現在の全資産をJPY換算した合計（初回は`null`） |
# | `balances` | 各通貨の保有残高 |
#
# ---
#
# ### 5-2. 取引実行・時間を進める
#
# **エンドポイント**: `POST /api/trade/next`
#
# **リクエスト例**:
# ```json
# {
#   "session_id": 1,
#   "exchange_requests": [
#     {"currency_from": "JPY", "currency_to": "USD", "amount": 100000},
#     {"currency_from": "JPY", "currency_to": "EUR", "amount": 50000}
#   ]
# }
# ```
#
# - `exchange_requests` は空リスト `[]` でもOK（取引なしで時間だけ進む）
# - `amount` は `currency_from` の通貨単位で指定
# - 残高が不足している取引はスキップされます
#
# **レスポンス例**:
# ```json
# {
#   "session_id": 1,
#   "previous_datetime": "2016-01-04T00:00:00",
#   "current_datetime": "2016-01-05T00:00:00",
#   "is_complete": false,
#   "balances": {
#     "JPY": 850000.0,
#     "USD": 845.67,
#     "EUR": 389.11
#   },
#   "trades": [
#     {
#       "currency_from": "JPY",
#       "currency_to": "USD",
#       "amount_from": 100000.0,
#       "amount_to": 845.67,
#       "rate": 0.0084567
#     }
#   ],
#   "rates": {
#     "USD": 118.25,
#     "EUR": 128.5,
#     "JPY": 1.0
#   },
#   "jpy_balance": 1000012.35
# }
# ```
#
# | フィールド | 説明 |
# |-----------|------|
# | `previous_datetime` | 取引を実行した日時（取引前） |
# | `current_datetime` | 取引後の現在日時（次のステップの日時） |
# | `rates` | **`previous_datetime`時点**の為替レート（対JPY）|
# | `jpy_balance` | 取引後の全資産をJPY換算した合計 |
# | `is_complete` | `true` になったら終了 |
#
# > **注意**: `rates` の値はすべて「1単位あたりの日本円」です。  
# > 例: `USD: 118.25` → 1ドル = 118.25円
#
# ---
#
# ### 5-3. 為替レートの参照
#
# **エンドポイント**: `GET /api/rate/{datetime}`
#
# 指定した日時の為替レートを取得します。日時は**完全一致**で検索されます。
#
# ```
# GET /api/rate/2016-01-04T00:00:00
# ```
#
# **レスポンス例**:
# ```json
# {
#   "timestamp": "2016-01-04T00:00:00",
#   "rates": {
#     "USD": 118.25,
#     "EUR": 128.5,
#     "GBP": 173.25,
#     "AUD": 85.5,
#     "CHF": 118.0,
#     "CNY": 18.05,
#     "HKD": 15.25
#   }
# }
# ```
#
# レートが存在しない日時を指定するとエラー（500）になります。

# %%
# ライブラリのインポート
# %matplotlib inline
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib import ticker

# %%
# ===== 設定 =====
# BASE_URL は演習環境（JupyterHub）では自動設定されます。他環境では主催者の案内に従ってください
import os
BASE_URL   = os.environ.get("FX_API_BASE_URL", "http://34.146.231.219:8000")
SCENARIO   = 'DEMO_3DAY'   # 使用するシナリオ名
USER_ID    = 'dummyUser'   # 配布されたユーザーID に置き換えること（このままではエラーになります）

START_URL  = BASE_URL + '/api/trade/start/{}/{}'
NEXT_URL   = BASE_URL + '/api/trade/next'
RATE_URL   = BASE_URL + '/api/rate/{}'

# 取引可能な通貨リスト
CURRENCY_LIST = ['JPY', 'USD', 'EUR', 'GBP', 'AUD', 'NZD', 'CAD', 'CHF', 'TRY', 'ZAR', 'MXN', 'NOK', 'SEK', 'HKD']


# %%
# ===== ユーティリティ関数 =====

def get_prev_weekdays(date_str, n):
    """指定日から遡ってn営業日分の日付リストを返す"""
    dt = datetime.fromisoformat(date_str)
    weekdays = []
    current = dt
    while len(weekdays) < n:
        if current.weekday() < 5:  # 月〜金
            weekdays.append(current)
        current -= timedelta(days=1)
    return list(reversed(weekdays))

def fetch_rates(dt):
    """指定日時の為替レート（対JPY）を取得する"""
    resp = requests.get(RATE_URL.format(dt.strftime('%Y-%m-%dT%H:%M:%S')))
    if resp.status_code != 200:
        return {}
    return {k: float(v) for k, v in resp.json()['rates'].items()}

def init_rate_history(start_date_str, n=10):
    """
    開始日から遡ってn営業日分の為替レート履歴を初期化する。
    currency_history[currency] = [rate_oldest, ..., rate_newest]
    """
    dates = get_prev_weekdays(start_date_str, n)
    currency_history = {c: [] for c in CURRENCY_LIST if c != 'JPY'}
    for dt in dates:
        rates = fetch_rates(dt)
        for currency in currency_history:
            if currency in rates:
                currency_history[currency].append(rates[currency])
    return currency_history

def update_rate_history(currency_history, rates):
    """レート履歴に最新レートを追記する"""
    for currency in currency_history:
        if currency in rates:
            currency_history[currency].append(float(rates[currency]))

def get_dma(rates, n):
    """n日移動平均を計算する"""
    return [sum(rates[max(0, i-n+1):i+1]) / len(rates[max(0, i-n+1):i+1]) for i in range(len(rates))]


# %% [markdown]
# ## 6. サンプル戦略①：毎日固定額をUSDに換える
#
# 最もシンプルな戦略です。毎日一定額のJPYをUSDに変換します。

# %%
SCENARIO = 'DEMO_3DAY'

# セッション開始
resp = requests.post(START_URL.format(SCENARIO, USER_ID))
session = resp.json()
session_id  = session['id']
is_complete = session['is_complete']
current_dt  = session['current_datetime']
balances    = session['balances']

jpy_history = []

while not is_complete:
    # 毎日10,000円分をUSDに換える
    exchange_requests = [
        {'currency_from': 'JPY', 'currency_to': 'USD', 'amount': 10000}
    ]

    body = {'session_id': session_id, 'exchange_requests': exchange_requests}
    resp = requests.post(NEXT_URL, json=body)
    result = resp.json()

    is_complete = result['is_complete']
    current_dt  = result['current_datetime']
    balances    = result['balances']
    if result['jpy_balance']:
        jpy_history.append(float(result['jpy_balance']))

print(f'最終JPY資産: {float(result["jpy_balance"]):,.2f} 円')
print(f'最終残高: {balances}')

# %%
# 資産推移グラフ
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(jpy_history)
ax.axhline(1_000_000, color='gray', linestyle='--', label='初期資産')
ax.set_title('JPY資産推移（固定額戦略）')
ax.set_xlabel('ステップ数')
ax.set_ylabel('JPY')
ax.grid(True)
ax.legend()
plt.tight_layout()
plt.show()


# %% [markdown]
# ## 7. サンプル戦略②：逆張り戦略
#
# **直近x日間、ある通貨が対JPYで連続下落していたら**、そのタイミングで保有JPYをその通貨に換えます（下落しすぎたら反転するという逆張り発想）。

# %%
def contrarian_strategy(currency_history, balances, lookback=5, ratio=0.3):
    """
    直近lookback日間連続で対JPYレートが下落している通貨があれば、
    保有JPYのratio割合をその通貨に換える。
    """
    exchange_requests = []
    jpy_balance = float(balances.get('JPY', 0))
    if jpy_balance <= 0:
        return exchange_requests

    for currency, rates in currency_history.items():
        if len(rates) < lookback:
            continue
        recent = rates[-lookback:]
        # 連続下落チェック
        if all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
            exchange_requests.append({
                'currency_from': 'JPY',
                'currency_to': currency,
                'amount': jpy_balance * ratio
            })
            break  # 1通貨のみ
    return exchange_requests


# %%
SCENARIO = 'DEMO_3DAY'

resp = requests.post(START_URL.format(SCENARIO, USER_ID))
session = resp.json()
session_id       = session['id']
is_complete      = session['is_complete']
current_dt       = session['current_datetime']
balances         = session['balances']
currency_history = init_rate_history(current_dt, n=10)

jpy_history = []

while not is_complete:
    exchange_requests = contrarian_strategy(currency_history, balances, lookback=5, ratio=0.3)

    body = {'session_id': session_id, 'exchange_requests': exchange_requests}
    resp = requests.post(NEXT_URL, json=body)
    result = resp.json()

    update_rate_history(currency_history, result['rates'])
    is_complete = result['is_complete']
    current_dt  = result['current_datetime']
    balances    = result['balances']
    if result['jpy_balance']:
        jpy_history.append(float(result['jpy_balance']))

print(f'最終JPY資産: {float(result["jpy_balance"]):,.2f} 円')


# %% [markdown]
# ## 8. サンプル戦略③：ゴールデンクロス・デッドクロス戦略
#
# - **短期移動平均 > 長期移動平均** → 上昇トレンド → その通貨を買う（JPY → 外貨）
# - **短期移動平均 < 長期移動平均** → 下降トレンド → ポジション解消（外貨 → JPY）

# %%
def golden_cross_strategy(currency_history, balances, short=5, long=10, target_currency='USD'):
    """
    target_currencyの短期/長期移動平均でゴールデン・デッドクロスを判定し、
    JPYと対象通貨を全力で入れ替える。
    """
    exchange_requests = []
    rates = currency_history.get(target_currency, [])
    if len(rates) < long:
        return exchange_requests

    short_ma = sum(rates[-short:]) / short
    long_ma  = sum(rates[-long:])  / long

    jpy_balance    = float(balances.get('JPY', 0))
    target_balance = float(balances.get(target_currency, 0))

    if short_ma > long_ma and jpy_balance > 0:
        # ゴールデンクロス → 買い
        exchange_requests.append({
            'currency_from': 'JPY',
            'currency_to': target_currency,
            'amount': jpy_balance
        })
    elif short_ma < long_ma and target_balance > 0:
        # デッドクロス → 売り
        exchange_requests.append({
            'currency_from': target_currency,
            'currency_to': 'JPY',
            'amount': target_balance
        })
    return exchange_requests


# %%
SCENARIO = 'DEMO_3DAY'
SHORT, LONG = 5, 20

resp = requests.post(START_URL.format(SCENARIO, USER_ID))
session = resp.json()
session_id       = session['id']
is_complete      = session['is_complete']
current_dt       = session['current_datetime']
balances         = session['balances']
currency_history = init_rate_history(current_dt, n=max(SHORT, LONG))

jpy_history = []

while not is_complete:
    exchange_requests = golden_cross_strategy(currency_history, balances, SHORT, LONG, 'USD')

    body = {'session_id': session_id, 'exchange_requests': exchange_requests}
    resp = requests.post(NEXT_URL, json=body)
    result = resp.json()

    update_rate_history(currency_history, result['rates'])
    is_complete = result['is_complete']
    current_dt  = result['current_datetime']
    balances    = result['balances']
    if result['jpy_balance']:
        jpy_history.append(float(result['jpy_balance']))

print(f'最終JPY資産: {float(result["jpy_balance"]):,.2f} 円')

# %%
# USD/JPYレートと移動平均の可視化
usd_rates = currency_history['USD']
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))

ax1.plot(usd_rates, label='USD/JPY')
ax1.plot(get_dma(usd_rates, SHORT), label=f'{SHORT}日移動平均', linestyle='--')
ax1.plot(get_dma(usd_rates, LONG),  label=f'{LONG}日移動平均',  linestyle='--')
ax1.set_title('USD/JPY レートと移動平均')
ax1.legend()
ax1.grid(True)

ax2.plot(jpy_history)
ax2.axhline(1_000_000, color='gray', linestyle='--', label='初期資産')
ax2.set_title('JPY資産推移（ゴールデンクロス戦略）')
ax2.set_ylabel('JPY')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()

# %% [markdown]
# ## 9. ヒント
#
# - `rates` は「1外貨 = X円」の形式です。`USD: 118.25` → 1ドル = 118.25円
# - **取引は `previous_datetime` のレートで実行されます**。`current_datetime` のレートは次のステップで適用されます
# - `exchange_requests` を空リスト `[]` にすると取引なしで日時だけ進みます（様子見も戦略のうち）
# - 残高不足の取引はサーバー側でスキップされます（エラーにはなりません）
# - 過去レートの取得には `GET /api/rate/{datetime}` を使えます（`datetime` は `2016-01-04T00:00:00` 形式）
#
# ---
#
# ## 10. よくあるエラー
#
# | エラー | 原因 |
# |--------|------|
# | `500 Rates not found` | そのdatetimeのレートが存在しない（週末・祝日など）|
# | `404 Scenario not found` | シナリオ名が間違っている |
# | `400 Bad Request` | リクエストのJSONフォーマットが間違っている |
# | セッションが開始できない | `user_id` が登録されていない可能性があります。主催者に確認してください |
