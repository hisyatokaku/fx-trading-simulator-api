package com.example.fxtrade.models;

import java.util.Date;

public class Rate extends RateAbstract {
    public Rate() {
        super();
        // You must not modify this constructor. Mithra calls this internally.
        // You can call this constructor. You can also add new constructors.
    }

    public Rate(String currency, Date date, double rateDouble) {
        this();
        this.setCurrency(currency);
        this.setDate(date);
        this.setRate(rateDouble);
    }
}
