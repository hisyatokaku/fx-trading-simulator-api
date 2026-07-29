package com.example.fxtrade.api.response;

import com.example.fxtrade.models.Balance;
import com.example.fxtrade.models.BalanceFinder;
import com.example.fxtrade.models.BalanceList;
import com.example.fxtrade.models.Session;
import com.example.fxtrade.utils.reladomo.DateUtil;
import org.eclipse.collections.api.factory.Maps;
import org.eclipse.collections.api.multimap.Multimap;
import org.eclipse.collections.impl.utility.Iterate;

import java.time.LocalDateTime;
import java.util.Map;

public class SessionResponse {
    private final int sessionId;
    private final boolean isComplete;
    private final LocalDateTime startDate;
    private final LocalDateTime endDate;
    private final double jpyBalance;
    private final String scenario;

    public SessionResponse(int sessionId, boolean isComplete, LocalDateTime startDate, LocalDateTime endDate, double jpyBalance, String scenario, Map<LocalDateTime, Map<String, Double>> dateToBalances) {
        this.sessionId = sessionId;
        this.isComplete = isComplete;
        this.startDate = startDate;
        this.endDate = endDate;
        this.jpyBalance = jpyBalance;
        this.scenario = scenario;
    }

    public static SessionResponse newWith(Session session) {
        BalanceList balances = BalanceFinder.findMany(BalanceFinder.sessionId().eq(session.getId()));
        Multimap<LocalDateTime, Balance> dateBalanceMutableMultimap = Iterate.groupBy(balances, balance -> DateUtil.toLocalDateTime(balance.getDate()));
        Map<LocalDateTime, Map<String, Double>> dateToBalances = Maps.mutable.empty();

        dateBalanceMutableMultimap.forEachKeyMultiValues((date, balancesOnDate) -> {
            Map<String, Double> currencyToBalance = Iterate.toMap(balancesOnDate, Balance::getCurrency, Balance::getAmount);
            dateToBalances.put(date, currencyToBalance);
        });
        return new SessionResponse(session.getId(), session.isIsComplete(), DateUtil.toLocalDateTime(session.getStartDate()), DateUtil.toLocalDateTime(session.getEndDate()), session.getJpyAmount(), session.getScenario(), dateToBalances);
    }

    public int getSessionId() {
        return sessionId;
    }

    public boolean isComplete() {
        return isComplete;
    }

    public LocalDateTime getStartDate() {
        return startDate;
    }

    public LocalDateTime getEndDate() {
        return endDate;
    }

    public double getJpyBalance() {
        return jpyBalance;
    }

    public String getScenario() {
        return scenario;
    }
}
