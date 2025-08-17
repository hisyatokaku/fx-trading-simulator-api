package com.example.fxtrade.models;

import com.example.fxtrade.models.enums.Currency;
import org.eclipse.collections.api.factory.Maps;
import org.eclipse.collections.api.list.MutableList;
import org.eclipse.collections.api.tuple.Twin;
import org.eclipse.collections.impl.tuple.Tuples;
import org.eclipse.collections.impl.utility.ArrayIterate;

import java.util.Date;
import java.util.Map;
import java.util.Set;

public class RateMatrix {

    private final Map<Twin<String>, Double> currencyFromAndToToRate;

    private RateMatrix(Map<Twin<String>, Double> currencyFromAndToToRate) {
        this.currencyFromAndToToRate = currencyFromAndToToRate;
    }

    public static RateMatrix newWith(Date date) {
        Map<Twin<String>, Double> currencyFromAndToToRate = Maps.mutable.empty();
        RateList rates = RateFinder.findMany(RateFinder.date().eq(date).and(RateFinder.currency().in(Currency.CURRENCIES_AS_STRING)));
        for (Rate rate : rates) {
            String currencyFrom = rate.getCurrency();
            String currencyTo = Currency.JPY.name();
            currencyFromAndToToRate.put(Tuples.twin(currencyFrom, currencyTo), rate.getRate());
            currencyFromAndToToRate.put(Tuples.twin(currencyTo, currencyFrom), 1.0 / rate.getRate());
        }

        MutableList<String> nonJpyCurrencies = ArrayIterate.reject(Currency.values(), Currency.JPY::equals).collect(Currency::name);
        for (String currencyFrom : nonJpyCurrencies) {
            for (String currencyTo : nonJpyCurrencies) {
                if (currencyFrom.equals(currencyTo)) {
                    continue;
                }
                Double jpyRateForFromCurrency = currencyFromAndToToRate.get(Tuples.twin(currencyFrom, Currency.JPY.name()));
                Double jpyRateForToCurrency = currencyFromAndToToRate.get(Tuples.twin(currencyTo, Currency.JPY.name()));
                
                // null check for missing rate data
                if (jpyRateForFromCurrency != null && jpyRateForToCurrency != null) {
                    currencyFromAndToToRate.put(Tuples.twin(currencyFrom, currencyTo), jpyRateForFromCurrency / jpyRateForToCurrency);
                }
            }
        }

        return new RateMatrix(currencyFromAndToToRate);
    }

    public double getRate(String currencyFrom, String currencyTo) {
        Double rate = currencyFromAndToToRate.get(Tuples.twin(currencyFrom, currencyTo));
        return rate != null ? rate : 0.0;
    }

    public Set<Twin<String>> getCurrencyFromAndTo() {
        return currencyFromAndToToRate.keySet();
    }
}
