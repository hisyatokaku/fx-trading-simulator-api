package com.example.fxtrade.api.response;

import com.example.fxtrade.models.GameConfig;
import com.example.fxtrade.models.RateMatrix;
import com.example.fxtrade.models.enums.Currency;
import com.example.fxtrade.utils.reladomo.DateUtil;
import org.eclipse.collections.api.factory.Maps;
import org.eclipse.collections.api.tuple.Twin;
import org.eclipse.collections.impl.utility.Iterate;

import java.sql.Timestamp;
import java.time.LocalDate;
import java.util.Map;
import java.util.Set;

public class ScenarioResponse {
    private final LocalDate startDate;
    private final LocalDate endDate;

    private final Map<String, Map<String, Double>> dateToCurrencyPairToRate;

    public ScenarioResponse(GameConfig gameConfig) {
        this.startDate = gameConfig.getDateFrom();
        this.endDate = gameConfig.getDateTo();
        Map<String, Map<String, Double>> dateToCurrencyPairToRate = Maps.mutable.empty();
        for (LocalDate date : gameConfig.getBusinessDates()) {
            // 分足データでは暦日の0時ちょうどに行が存在するとは限らないため、
            // その日以降で最初に存在するタイムスタンプを採用する。
            Timestamp dayStart = DateUtil.toTimestamp(date.atStartOfDay());
            Timestamp resolved = DateUtil.firstAvailableTimestampOnOrAfter(dayStart, Currency.USD.name());
            if (resolved == null || !DateUtil.toLocalDateTime(resolved).toLocalDate().equals(date)) {
                continue;
            }
            RateMatrix rateMatrix = RateMatrix.newWith(resolved);
            Set<Twin<String>> currencyFromAndTos = rateMatrix.getCurrencyFromAndTo();
            Map<String, Double> currencyPairToRate = Iterate.toMap(currencyFromAndTos, currencyFromAndTo -> {
                return currencyFromAndTo.getOne() + "/" + currencyFromAndTo.getTwo();
            }, currencyFromAndTo -> rateMatrix.getRate(currencyFromAndTo.getOne(), currencyFromAndTo.getTwo()));
            dateToCurrencyPairToRate.put(date.toString(), currencyPairToRate);
        }
        this.dateToCurrencyPairToRate = dateToCurrencyPairToRate;
    }

    public LocalDate getStartDate() {
        return startDate;
    }

    public LocalDate getEndDate() {
        return endDate;
    }

    public Map<String, Map<String, Double>> getDateToCurrencyPairToRate() {
        return dateToCurrencyPairToRate;
    }
}
