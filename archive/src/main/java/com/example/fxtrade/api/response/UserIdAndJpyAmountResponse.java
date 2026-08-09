package com.example.fxtrade.api.response;

public class UserIdAndJpyAmountResponse {
    private final String userId;
    private final double jpyAmount;

    public UserIdAndJpyAmountResponse(String userId, double jpyAmount) {
        this.userId = userId;
        this.jpyAmount = jpyAmount;
    }

    public String getUserId() {
        return userId;
    }

    public double getJpyAmount() {
        return jpyAmount;
    }
}
