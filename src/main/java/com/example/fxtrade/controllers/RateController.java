package com.example.fxtrade.controllers;

import com.example.fxtrade.models.RateMatrix;
import com.example.fxtrade.utils.reladomo.DateUtil;
import org.eclipse.collections.api.factory.Maps;
import org.eclipse.collections.api.tuple.Twin;
import org.eclipse.collections.impl.utility.Iterate;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping(value = {"api/rate"})
public class RateController {

    @GetMapping("{date}")
    public Map<String, Double> getRate(@PathVariable @DateTimeFormat(pattern = "yyyy-MM-dd") LocalDate date) {
        Map<String, Double> currencyPairToRate = Maps.mutable.empty();
        RateMatrix rateMatrix = RateMatrix.newWith(DateUtil.toDate(date));
        Set<Twin<String>> currencyFromAndTos = rateMatrix.getCurrencyFromAndTo();
        Iterate.forEach(currencyFromAndTos, currencyFromAndTo -> {
            String currencyFrom = currencyFromAndTo.getOne();
            String currencyTo = currencyFromAndTo.getTwo();
            double rate = rateMatrix.getRate(currencyFrom, currencyTo);
            currencyPairToRate.put(currencyFrom + "/" + currencyTo, rate);
        });
        return currencyPairToRate;
    }
}
