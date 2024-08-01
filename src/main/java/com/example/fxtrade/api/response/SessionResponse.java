package com.example.fxtrade.api.response;

import com.example.fxtrade.models.Balance;
import com.example.fxtrade.models.BalanceFinder;
import com.example.fxtrade.models.BalanceList;
import com.example.fxtrade.models.Session;
import com.example.fxtrade.utils.reladomo.DateUtil;
import org.eclipse.collections.api.factory.Maps;
import org.eclipse.collections.api.multimap.Multimap;
import org.eclipse.collections.impl.utility.Iterate;

import java.time.LocalDate;
import java.util.Map;

public class SessionResponse {
    private final int sessionId;
    private final boolean isComplete;
    private final LocalDate startDate;
    private final LocalDate endDate;
    private final double jpyBalance;
    private final String scenario;
    private final Map<LocalDate, Map<String, Double>> dateToBalances;

    public SessionResponse(int sessionId, boolean isComplete, LocalDate startDate, LocalDate endDate, double jpyBalance, String scenario, Map<LocalDate, Map<String, Double>> dateToBalances) {
        this.sessionId = sessionId;
        this.isComplete = isComplete;
        this.startDate = startDate;
        this.endDate = endDate;
        this.jpyBalance = jpyBalance;
        this.scenario = scenario;
        this.dateToBalances = dateToBalances;
    }

    public static SessionResponse newWith(Session session) {
        BalanceList balances = BalanceFinder.findMany(BalanceFinder.sessionId().eq(session.getId()));
        Multimap<LocalDate, Balance> dateBalanceMutableMultimap = Iterate.groupBy(balances, balance -> DateUtil.toLocalDate(balance.getDate()));
        Map<LocalDate, Map<String, Double>> dateToBalances = Maps.mutable.empty();

        dateBalanceMutableMultimap.forEachKeyMultiValues((date, balancesOnDate) -> {
            Map<String, Double> currencyToBalance = Iterate.toMap(balancesOnDate, Balance::getCurrency, Balance::getAmount);
            dateToBalances.put(date, currencyToBalance);
        });
        return new SessionResponse(session.getId(), session.isIsComplete(), DateUtil.toLocalDate(session.getStartDate()), DateUtil.toLocalDate(session.getEndDate()), session.getJpyAmount(), session.getScenario(), dateToBalances);
    }

    public int getSessionId() {
        return sessionId;
    }

    public Map<LocalDate, Map<String, Double>> getDateToBalances() {
        return dateToBalances;
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

    public double getJpyBalance() {
        return jpyBalance;
    }

    public String getScenario() {
        return scenario;
    }
}
