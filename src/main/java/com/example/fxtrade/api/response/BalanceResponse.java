package com.example.fxtrade.api.response;

import com.example.fxtrade.models.Balance;

public class BalanceResponse {
    private final String currency;
    private final double amount;

    public BalanceResponse(Balance balance) {
        this(balance.getCurrency(), balance.getAmount());
    }

    public BalanceResponse(String currency, double amount) {
        this.currency = currency;
        this.amount = amount;
    }

    public String getCurrency() {
        return currency;
    }

    public double getAmount() {
        return amount;
    }
}