package com.example.fxtrade.manager;

import com.example.fxtrade.models.GameConfig;
import com.example.fxtrade.models.Session;
import com.example.fxtrade.models.Trader;
import com.example.fxtrade.models.TraderFinder;
import com.example.fxtrade.models.enums.GameType;
import com.example.fxtrade.utils.reladomo.DateUtil;
import org.eclipse.collections.api.factory.Lists;

import java.time.LocalDate;
import java.util.List;

public class GameConfigGenerator {
    public static void setUpSession(Session session, String userId, String scenario) {
        GameConfig gameConfig = GameConfig.valueOf(scenario);
        Trader trader = TraderFinder.findByPrimaryKey(userId);
        if(trader == null) {
            throw new IllegalArgumentException("User id is invalid");
        }
        if(gameConfig.getGameType() == GameType.PROD && !trader.getType().equals("prod")) {
            throw new IllegalArgumentException("User id is not authorized to run production scenario");
        }

        session.setUserId(userId);
        session.setStartDate(DateUtil.toDate(gameConfig.getDateFrom()));
        session.setEndDate(DateUtil.toDate(gameConfig.getDateTo()));
        session.setCurrentDate(DateUtil.toDate(gameConfig.getDateFrom()));
        session.setCommissionRate(gameConfig.getCommission());
        session.setScenario(scenario);
    }

    public static List<LocalDate> getDates(String scenario) {
        GameConfig gameConfig = GameConfig.valueOf(scenario);
        LocalDate startDate = gameConfig.getDateFrom();
        LocalDate endDate = gameConfig.getDateTo();
        List<LocalDate> dates = Lists.mutable.empty();
        for (LocalDate date = startDate; date.isEqual(endDate) || date.isBefore(endDate); date = DateUtil.nextBusinessDate(date)) {
            dates.add(date);
        }
        return dates;
    }
}
