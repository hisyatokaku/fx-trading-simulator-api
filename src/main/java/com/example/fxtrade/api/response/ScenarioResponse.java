package com.example.fxtrade.api.response;

import com.example.fxtrade.models.GameConfig;
import com.example.fxtrade.models.RateMatrix;
import com.example.fxtrade.utils.reladomo.DateUtil;
import org.eclipse.collections.api.tuple.Twin;
import org.eclipse.collections.impl.utility.Iterate;

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
        this.dateToCurrencyPairToRate = Iterate.toMap(gameConfig.getBusinessDates(), date -> date.toString(), date -> {
            RateMatrix rateMatrix = RateMatrix.newWith(DateUtil.toDate(date));
            Set<Twin<String>> currencyFromAndTos = rateMatrix.getCurrencyFromAndTo();
            return Iterate.toMap(currencyFromAndTos, currencyFromAndTo -> {
                return currencyFromAndTo.getOne() + "/" + currencyFromAndTo.getTwo();
            }, currencyFromAndTo -> rateMatrix.getRate(currencyFromAndTo.getOne(), currencyFromAndTo.getTwo()));
        });
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
