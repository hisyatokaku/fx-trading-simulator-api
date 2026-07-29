package com.example.fxtrade.utils.reladomo;

import com.example.fxtrade.FxTradeApplication;
import com.example.fxtrade.models.Rate;
import com.example.fxtrade.models.RateFinder;
import com.example.fxtrade.models.RateList;
import org.eclipse.collections.api.factory.Lists;
import org.eclipse.collections.api.list.MutableList;
import org.eclipse.collections.impl.utility.ArrayIterate;
import org.eclipse.collections.impl.utility.Iterate;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.List;

public class RateInitializer {
    public static void run() {
        InputStream resourceAsStream = FxTradeApplication.class.getClassLoader().getResourceAsStream("data/rates_1min.csv");
        try {
            long existingCount = RateFinder.findMany(RateFinder.all()).count();
            if (existingCount > 0) {
                System.out.println("Rates already initialized (" + existingCount + " records). Skipping initialization.");
                return;
            }

            // CSVファイルの読み込み(1分足: DateTime,USD,EUR,... 形式。土日/市場クローズ時間帯は
            // データ自体に行が存在しないため、日次CSVで行っていた補間は不要)
            InputStreamReader isr = new InputStreamReader(resourceAsStream, "UTF-8");
            BufferedReader reader = new BufferedReader(isr);
            List<String> lines = Lists.mutable.empty();
            while(reader.ready()) {
                lines.add(reader.readLine());
            }

            MutableList<String> currencies = ArrayIterate.drop(lines.get(0).split(","), 1);
            RateList ratesList = Lists.mutable.ofAll(Iterate.select(Iterate.drop(lines, 1), line -> line != null && !line.isEmpty())).flatCollect(line -> {
                String[] items = line.split(",", -1);
                Timestamp timestamp = parseDateTime(items[0]);
                MutableList<Rate> rates = Lists.mutable.empty();
                for (int i = 1; i < items.length; i++) {
                    String value = items[i];
                    if (value == null || value.isEmpty()) {
                        // フォールバック元(rates.csv)にもその通貨の値が無かった行。スキップする。
                        continue;
                    }
                    rates.add(new Rate(currencies.get(i - 1), timestamp, Double.parseDouble(value)));
                }
                return rates;
            }, new RateList());

            int batchSize = 500;
            for (int i = 0; i < ratesList.size(); i += batchSize) {
                int end = Math.min(i + batchSize, ratesList.size());
                RateList batch = new RateList(ratesList.subList(i, end));
                batch.insertAll();
            }
        } catch (IOException e) {

        }
    }

    private static Timestamp parseDateTime(String dateTimeStr) {
        String[] dateAndTime = dateTimeStr.split(" ");
        String[] dateParts = dateAndTime[0].split("/");
        int year = Integer.parseInt(dateParts[0]);
        int month = Integer.parseInt(dateParts[1]);
        int day = Integer.parseInt(dateParts[2]);
        int hour = 0;
        int minute = 0;
        if (dateAndTime.length > 1) {
            String[] timeParts = dateAndTime[1].split(":");
            hour = Integer.parseInt(timeParts[0]);
            minute = Integer.parseInt(timeParts[1]);
        }
        return Timestamp.valueOf(LocalDateTime.of(year, month, day, hour, minute));
    }
}
