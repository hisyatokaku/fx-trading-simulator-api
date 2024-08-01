package com.example.fxtrade.api.response;

public class RateResponse {
    private final String currencyFromAndTo;
    private final double rate;

    public RateResponse(String currencyFromAndTo, double rate) {
        this.currencyFromAndTo = currencyFromAndTo;
        this.rate = rate;
    }

    public String getCurrencyFromAndTo() {
        return currencyFromAndTo;
    }

    public double getRate() {
        return rate;
    }
}
