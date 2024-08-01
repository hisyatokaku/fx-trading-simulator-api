package com.example.fxtrade.api.request;

public class ExchangeRequest {
    private final String currencyFrom;
    private final String currencyTo;
    private final double amount;

    public ExchangeRequest(String currencyFrom, String currencyTo, double amount) {
        this.currencyFrom = currencyFrom;
        this.currencyTo = currencyTo;
        this.amount = amount;
    }

    public String getCurrencyFrom() {
        return currencyFrom;
    }

    public String getCurrencyTo() {
        return currencyTo;
    }

    public double getAmount() {
        return amount;
    }
}
