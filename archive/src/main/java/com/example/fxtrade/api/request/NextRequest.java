package com.example.fxtrade.api.request;

import java.util.List;

public class NextRequest {
    private final int sessionId;
    private final List<ExchangeRequest> exchangeRequests;

    public NextRequest(int sessionId, List<ExchangeRequest> exchangeRequests) {
        this.sessionId = sessionId;
        this.exchangeRequests = exchangeRequests;
    }

    public int getSessionId() {
        return sessionId;
    }

    public List<ExchangeRequest> getExchangeRequests() {
        return exchangeRequests;
    }
}
