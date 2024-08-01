package com.example.fxtrade.manager;

import com.example.fxtrade.api.request.ExchangeRequest;
import com.example.fxtrade.api.request.NextRequest;
import com.example.fxtrade.models.*;
import com.example.fxtrade.models.enums.Currency;
import com.example.fxtrade.utils.reladomo.DateUtil;
import com.gs.fw.common.mithra.AggregateList;
import com.gs.fw.common.mithra.MithraNullPrimitiveException;
import org.eclipse.collections.impl.Counter;
import org.eclipse.collections.impl.utility.ArrayIterate;
import org.eclipse.collections.impl.utility.Iterate;
import org.eclipse.collections.impl.utility.MapIterate;

import java.time.LocalDate;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public class SessionManager {
    public synchronized static Session generateSession(Optional<String> userId, String scenario) {
        Session session = new Session();
        int sessionId = getId();
        session.setId(sessionId);

        session.setIsComplete(false);
        session.setJpyAmount(1_000_000);
        userId.ifPresent(session::setUserId);
        GameConfigGenerator.setUpSession(session, scenario);
        session.insert();
        new Balance(sessionId, session.getCurrentDate(), Currency.JPY.name(), 1_000_000).insert();
        ArrayIterate.forEach(Currency.values(), currency -> {
            if(!currency.equals(currency.JPY)) new Balance(sessionId, session.getCurrentDate(), currency.name(), 0.d).insert();
        });
        return session;
    }

    private static int getId() {
        try {
            AggregateList aggregateData = new AggregateList(SessionFinder.all());
            aggregateData.addAggregateAttribute("max", SessionFinder.id().max());
            return aggregateData.get(0).getAttributeAsInt("max") + 1;
        } catch (Exception e) {
            return 0;
        }
    }

    public static Session next(NextRequest nextRequest) {
        Session session = SessionFinder.findByPrimaryKey(nextRequest.getSessionId());
        if(session.isIsComplete()) {
            throw new IllegalStateException("Session is complete");
        }

        Date currentDate = session.getCurrentDate();
        LocalDate currentDateAsLocalDate = DateUtil.toLocalDate(currentDate);
        LocalDate nextDateAsLocalDate = DateUtil.nextBusinessDate(currentDateAsLocalDate);
        Date nextDate = DateUtil.toDate(nextDateAsLocalDate);

        BalanceList currentBalances = BalanceFinder.findMany(BalanceFinder.sessionId().eq(session.getId()).and(BalanceFinder.date().eq(currentDate)));
        Map<String, Balance> currencyToNewBalance = Iterate.toMap(currentBalances, balance -> balance.getCurrency(), balance -> new Balance(session.getId(), nextDate, balance.getCurrency(), balance.getAmount()));
        RateMatrix rateMatrix = RateMatrix.newWith(currentDate);

        session.setCurrentDate(nextDate);

        List<ExchangeRequest> exchangeRequests = nextRequest.getExchangeRequests();
        if(nextDate.equals(session.getEndDate()) || nextDate.after(session.getEndDate())) {
            session.setIsComplete(true);
        }
        for (ExchangeRequest exchangeRequest: exchangeRequests) {
            String currencyFrom = exchangeRequest.getCurrencyFrom();
            String currencyTo = exchangeRequest.getCurrencyTo();
            double amount = exchangeRequest.getAmount();
            double rate = rateMatrix.getRate(currencyFrom, currencyTo);
            Balance balanceFrom = currencyToNewBalance.computeIfAbsent(currencyFrom, (c) -> new Balance(session.getId(), nextDate, currencyFrom, 0));
            double newAmountForCurrencyFrom = balanceFrom.getAmount() - amount;
            if(newAmountForCurrencyFrom < 0)
                throw new IllegalStateException("Balance amount cannot be negative");
            balanceFrom.setAmount(newAmountForCurrencyFrom);
            Balance balanceTo = currencyToNewBalance.computeIfAbsent(currencyTo, (c) -> new Balance(session.getId(), nextDate, currencyTo, 0));
            balanceTo.setAmount(balanceTo.getAmount() + amount * rate);
        }
        session.setCurrentDate(nextDate);
        session.setJpyAmount(calculateJpyAmount(currencyToNewBalance, rateMatrix));
        new BalanceList(currencyToNewBalance.values()).insertAll();
        return session;
    }

    private static double calculateJpyAmount(Map<String, Balance> currencyToNewBalance, RateMatrix rateMatrix) {
        return MapIterate.collectValues(currencyToNewBalance, (currency, balance) -> {
            if(currency.equals("JPY")) {
                return balance.getAmount();
            } else {
                return balance.getAmount() * rateMatrix.getRate(balance.getCurrency(), "JPY");
            }
        }).sumOfDouble(d -> d);
    }

    public static Session getSession(int sessionId) {
        Session session = SessionFinder.findByPrimaryKey(sessionId);
        return session;
    }

    public static SessionList getSessions(String userId) {
        SessionList sessions = SessionFinder.findMany(SessionFinder.userId().eq(userId));
        return sessions;
    }
}
