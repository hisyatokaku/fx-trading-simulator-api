# FX Trading Simulator API - データベース設計とデータ投入フロー

このドキュメントでは、プロジェクトのデータベース構造とデータ投入フローについて詳しく説明します。

## データベース構造

### テーブル一覧

| テーブル名 | 役割 | 主要カラム |
|------------|------|------------|
| `rate` | 為替レート履歴 | currency, date_d, rate |
| `trader` | トレーダー情報 | user_id, type_c |
| `session` | 取引セッション | id, user_id, scenario, jpy_amount |
| `balance` | 残高履歴 | session_id, date_d, currency, amount |

### DDLファイルの場所

テーブル定義は以下のDDLファイルで管理されています：
```
src/main/resources/generated-db/sql/
├── BALANCE.ddl
├── RATE.ddl  
├── SESSION.ddl
└── TRADER.ddl
```

**注意**: これらのDDLファイルはReladomoによって自動生成されるため、直接編集しないでください。

## データ投入フロー

### 1. 投入タイミング

データ投入は**アプリケーション起動時**に自動実行されます：

```java
// ReladomoServiceWithPsql.java @PostConstruct
LOGGER.info("Setting up rates");
RateInitializer.run();        // 為替レートデータ投入
LOGGER.info("Setting up traders");  
TraderInitializer.run();      // トレーダーデータ投入
```

### 2. 為替レートデータ (rates)

#### データソース
- **ファイル**: `src/main/resources/data/rates.csv`
- **期間**: 2002年4月〜（約20年分）
- **通貨**: USD, GBP, EUR, CAD, CHF, SEK, DKK, NOK, AUD, NZD, ZAR, BHD, HKD, INR, PHP, SGD, THB, KWD, SAR, AED, MXN, IDR, TWD

#### 投入ロジック (`RateInitializer.java`)
1. **重複チェック**: 既存データがある場合はスキップ
   ```java
   long existingCount = RateFinder.findMany(RateFinder.all()).count();
   if (existingCount > 0) {
       System.out.println("Rates already initialized (" + existingCount + " records). Skipping initialization.");
       return;
   }
   ```

2. **CSVパース**: rates.csvをパースして通貨別レート作成

3. **データ補間**: 土日祝日の欠損データを線形補間で埋める
   ```java
   // 平日のみ処理、土日はスキップ
   if(date.getDayOfWeek().equals(DayOfWeek.SATURDAY) || date.getDayOfWeek().equals(DayOfWeek.SUNDAY)) {
       continue;
   }
   ```

4. **バッチ投入**: 500レコードずつバッチで投入
   ```java
   int batchSize = 500;
   for (int i = 0; i < ratesList.size(); i += batchSize) {
       RateList batch = new RateList(ratesList.subList(i, end));
       batch.insertAll();
   }
   ```

#### 投入結果
- **レコード数**: 約127,236件
- **データ範囲**: 2002年4月〜現在（土日除く）
- **通貨数**: 23通貨

### 3. トレーダーデータ (traders)

#### データソース
- **ファイル**: `src/main/resources/data/traders.csv`
- **形式**: `user_id,type_c`（ユーザーID, トレーダータイプ）

#### 投入ロジック (`TraderInitializer.java`)
1. **全件削除**: 毎回既存データを全削除
   ```java
   TraderFinder.findMany(TraderFinder.all()).deleteAllInBatches(1000);
   ```

2. **CSVパース**: traders.csvを読み込み
   ```java
   String[] data = reader.readLine().split(",");
   Trader trader = new Trader(data[0], data[1]);  // user_id, type_c
   ```

3. **一括投入**: 全件を一括投入
   ```java
   traders.insertAll();
   ```

#### 投入結果
- **レコード数**: 102件
- **データ内容**: testuser, rocky, hvwbtu等のユーザーとその属性

## セットアップ時の注意点

### 初回セットアップ時

1. **テーブル作成**: Reladomoは自動でテーブルを作成しない場合があります
   ```sql
   -- 手動でテーブル作成が必要な場合
   CREATE TABLE rate (currency varchar(255), date_d date, rate float8);
   CREATE TABLE trader (user_id varchar(255), type_c varchar(255));
   CREATE TABLE session (id int, user_id varchar(255), start_date date, c_date date, end_date date, is_complete boolean, scenario varchar(255), jpy_amount float8, commission_rate float8);
   CREATE TABLE balance (session_id int, date_d date, currency varchar(255), amount float8);
   ```

2. **アプリケーション再起動**: テーブル作成後、アプリケーションを再起動してデータ投入を実行

### データリセット方法

#### 全データリセット
```bash
# データベースコンテナとボリュームを削除
docker compose down
docker volume rm fx-trading-simulator-api_postgres_data
docker compose up -d

# テーブル再作成（必要に応じて）
# アプリケーション再起動でデータ自動投入
docker compose restart app
```

#### 特定テーブルのリセット
```sql
-- rateテーブルのみリセット
TRUNCATE TABLE rate;
-- アプリケーション再起動でデータ再投入

-- traderテーブルは起動時に自動削除・再投入される
```

## トラブルシューティング

### よくある問題

1. **"relation does not exist" エラー**
   - 原因: テーブルが作成されていない
   - 解決: 上記の手動テーブル作成SQLを実行

2. **"Rates already initialized" なのにテーブルが空**
   - 原因: 異なるスキーマを参照している
   - 解決: ReladomoConnectionManagerの設定確認

3. **データ投入が遅い**
   - 原因: レートデータが大量（127K件）
   - 対策: バッチサイズの調整（現在500件）

### ログ確認方法

```bash
# アプリケーション起動ログでデータ投入状況確認
docker logs fx-trading-simulator-api-app-1 | grep -E "(Setting up|already initialized)"

# データベース内容確認
docker exec fx-trading-simulator-api-db-1 psql -U fxuser -d fxtrade -c "SELECT COUNT(*) FROM rate;"
docker exec fx-trading-simulator-api-db-1 psql -U fxuser -d fxtrade -c "SELECT COUNT(*) FROM trader;"
```

## 開発時の注意事項

1. **CSVファイル編集**: `data/rates.csv`, `data/traders.csv`の編集時は、アプリケーション再起動が必要

2. **Reladomoモデル変更**: XMLファイル変更時は以下を実行
   ```bash
   ./gradlew mithraGenerateSources
   ./gradlew build
   ```

3. **パフォーマンス**: rateテーブルは大容量のため、本格的なインデックス設計が必要
   ```sql
   -- 推奨インデックス
   CREATE INDEX idx_rate_currency_date ON rate(currency, date_d);
   CREATE INDEX idx_balance_session_id ON balance(session_id);
   ```

4. **データ投入のカスタマイズ**: 初期化ロジックの変更は`RateInitializer.java`, `TraderInitializer.java`を編集