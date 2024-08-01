package com.example.fxtrade.api.response;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

public class RatesResponse {
    private final Map<LocalDate, List<RateResponse>> dateToRateResponse;

    public RatesResponse(Map<LocalDate, List<RateResponse>> dateToRateResponse) {
        this.dateToRateResponse = dateToRateResponse;
    }

    public Map<LocalDate, List<RateResponse>> getDateToRateResponse() {
        return dateToRateResponse;
    }
}
