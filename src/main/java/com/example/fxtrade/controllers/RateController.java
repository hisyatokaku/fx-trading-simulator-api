package com.example.fxtrade.controllers;

import com.example.fxtrade.api.response.RateResponse;
import com.example.fxtrade.api.response.RatesResponse;
import com.example.fxtrade.manager.GameConfigGenerator;
import com.example.fxtrade.models.GameConfig;
import com.example.fxtrade.models.RateMatrix;
import com.example.fxtrade.utils.reladomo.DateUtil;
import io.swagger.v3.oas.annotations.Operation;
import org.eclipse.collections.api.factory.Lists;
import org.eclipse.collections.api.factory.Maps;
import org.eclipse.collections.api.factory.Sets;
import org.eclipse.collections.api.list.MutableList;
import org.eclipse.collections.api.tuple.Twin;
import org.eclipse.collections.impl.utility.Iterate;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping(value = {"api/rate"})
public class RateController {
    private static final Set<LocalDate> INVALID_DATES = GameConfig.getHiddenDatesForRates();

    @GetMapping("{date}")
    @Operation(summary = "Rate is available from 2002/4/1 to 2023/6/13 only on weekday. Disabled from 2018, 2021 year.")
    public RatesResponse getRate(@PathVariable @DateTimeFormat(pattern = "yyyy-MM-dd") LocalDate date) {
        LocalDate startDate = date;
        LocalDate endDate = date;
        Map<LocalDate, List<RateResponse>> dateToRatesResponse = Maps.mutable.empty();

        while(date.isBefore(endDate) || date.equals(endDate)) {
            if(!INVALID_DATES.contains(date)) {
                RateMatrix rateMatrix = RateMatrix.newWith(DateUtil.toDate(date));
                Set<Twin<String>> currencyFromAndTos = rateMatrix.getCurrencyFromAndTo();
                MutableList<RateResponse> rateResponses = Iterate.collect(currencyFromAndTos, currencyFromAndTo -> {
                    String currencyFrom = currencyFromAndTo.getOne();
                    String currencyTo = currencyFromAndTo.getTwo();
                    double rate = rateMatrix.getRate(currencyFrom, currencyTo);
                    return new RateResponse(currencyTo + "/" + currencyFrom, rate);
                }, Lists.mutable.empty());
                dateToRatesResponse.put(date, rateResponses);
            }
            date = DateUtil.nextBusinessDate(date);
        }
        return new RatesResponse(dateToRatesResponse);
    }
}
