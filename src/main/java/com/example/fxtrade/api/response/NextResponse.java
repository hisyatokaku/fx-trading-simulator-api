package com.example.fxtrade.api.response;

import com.example.fxtrade.models.*;
import com.example.fxtrade.models.enums.Currency;
import com.example.fxtrade.utils.reladomo.DateUtil;
import org.eclipse.collections.api.factory.Maps;
import org.eclipse.collections.impl.utility.Iterate;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.Date;
import java.util.Map;

public class NextResponse {
    private final int sessionId;
    private final boolean isComplete;
    private final LocalDate startDate;
    private final LocalDate endDate;
    private final LocalDate currentDate;
    private final double jpyBalance;
    private final Map<String, Double> currencyToBalance;
    private final Map<String, Double> nextDateRates;

    public NextResponse(int sessionId, boolean isComplete, LocalDate startDate, LocalDate endDate, LocalDate currentDate, double jpyBalance, Map<String, Double> currencyToBalance, Map<String, Double> nextDateRates) {
        this.sessionId = sessionId;
        this.isComplete = isComplete;
        this.startDate = startDate;
        this.endDate = endDate;
        this.currentDate = currentDate;
        this.jpyBalance = jpyBalance;
        this.currencyToBalance = currencyToBalance;
        this.nextDateRates = nextDateRates;
    }

    public static NextResponse newWith(Session session) {
        BalanceList balances = BalanceFinder.findMany(BalanceFinder.sessionId().eq(session.getId()).and(BalanceFinder.date().eq(session.getCurrentDate())));
        Map<String, Double> currencyToBalance = Iterate.toMap(balances, Balance::getCurrency, Balance::getAmount);
        RateMatrix rateMatrix = RateMatrix.newWith(DateUtil.toDate(DateUtil.toLocalDate(session.getCurrentDate())));
        Map<String, Double> nextDateRates = Maps.mutable.empty();
        for (Currency currencyFrom: Currency.values()) {
            for (Currency currencyTo: Currency.values()) {
                if(!currencyFrom.equals(currencyTo)) {
                    nextDateRates.put(currencyFrom.name() + "/" + currencyTo.name(), rateMatrix.getRate(currencyFrom.name(), currencyTo.name()));
                }
            }
        }
        return new NextResponse(session.getId(), session.isIsComplete(),
                DateUtil.toLocalDate(session.getStartDate()),
                DateUtil.toLocalDate(session.getEndDate()),
                DateUtil.toLocalDate(session.getCurrentDate()),
                session.getJpyAmount(), currencyToBalance, nextDateRates);
    }

    public int getSessionId() {
        return sessionId;
    }

    public boolean isComplete() {
        return isComplete;
    }

    public LocalDate getStartDate() {
        return startDate;
    }

    public LocalDate getEndDate() {
        return endDate;
    }

    public LocalDate getCurrentDate() {
        return currentDate;
    }

    public double getJpyBalance() {
        return jpyBalance;
    }

    public Map<String, Double> getCurrencyToBalance() {
        return currencyToBalance;
    }

    public Map<String, Double> getNextDateRates() {
        return nextDateRates;
    }
}
