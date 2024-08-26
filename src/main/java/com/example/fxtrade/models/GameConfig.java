package com.example.fxtrade.models;

import com.example.fxtrade.models.enums.GameType;
import com.example.fxtrade.utils.reladomo.DateUtil;
import org.eclipse.collections.api.factory.Lists;
import org.eclipse.collections.api.factory.Sets;
import org.eclipse.collections.impl.utility.ArrayIterate;

import java.time.LocalDate;
import java.util.List;
import java.util.Set;

public enum GameConfig {
    TEST0(LocalDate.of(2016, 1, 4), LocalDate.of(2016, 1, 11), 0, GameType.ANY),
    TEST1(LocalDate.of(2017, 1, 4), LocalDate.of(2017, 1, 11), 10., GameType.ANY),
    PROD0(LocalDate.of(2016, 1, 4), LocalDate.of(2016, 12, 31), 10., GameType.PROD),
    PROD1(LocalDate.of(2017, 1, 4), LocalDate.of(2017, 12, 31), 10., GameType.PROD);
    private LocalDate dateFrom;
    private LocalDate dateTo;
    private double commission;
    private GameType gameType;

    GameConfig(LocalDate dateFrom, LocalDate dateTo, double commission, GameType gameType) {
        this.dateFrom = dateFrom;
        this.dateTo = dateTo;
        this.commission = commission;
        this.gameType = gameType;
    }

    public LocalDate getDateFrom() {
        return dateFrom;
    }

    public LocalDate getDateTo() {
        return dateTo;
    }

    public double getCommission() {
        return commission;
    }

    public GameType getGameType() {
        return gameType;
    }

    public Set<LocalDate> getBusinessDates() {
        LocalDate startDate = this.getDateFrom();
        LocalDate endDate = this.getDateTo();
        Set<LocalDate> dates = Sets.mutable.empty();
        for (LocalDate date = startDate; date.isEqual(endDate) || date.isBefore(endDate); date = DateUtil.nextBusinessDate(date)) {
            dates.add(date);
        }
        return dates;
    }

    public static Set<LocalDate> getHiddenDatesForRates() {
        return ArrayIterate.select(GameConfig.values(), config -> config.getGameType().equals(GameType.PROD))
                .flatCollect(GameConfig::getBusinessDates, Sets.mutable.empty());
    }
}
