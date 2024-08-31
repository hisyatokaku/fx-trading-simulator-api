package com.example.fxtrade.models;

import com.example.fxtrade.models.enums.GameType;
import com.example.fxtrade.utils.reladomo.DateUtil;
import org.eclipse.collections.api.factory.Sets;
import org.eclipse.collections.impl.utility.ArrayIterate;

import java.time.LocalDate;
import java.util.Set;

public enum GameConfig {
    TEST0(LocalDate.of(2016, 1, 4), LocalDate.of(2016, 1, 11), 0, GameType.ANY),
    TEST1(LocalDate.of(2017, 1, 4), LocalDate.of(2017, 1, 11), 0.001, GameType.ANY),
    Jan_Mar_2016_without_commission(LocalDate.of(2016, 1, 4), LocalDate.of(2016, 3, 30), 0, GameType.ANY),
    Jan_Mar_2016_with_commission(LocalDate.of(2016, 1, 4), LocalDate.of(2016, 3, 30), 0.001, GameType.ANY),
    Jun_Aug_2016_without_commission(LocalDate.of(2016, 6, 1), LocalDate.of(2016, 8, 31), 0, GameType.ANY),
    Jun_Aug_2016_with_commission(LocalDate.of(2016, 6, 1), LocalDate.of(2016, 8, 31), 0.001, GameType.ANY),
    Feb_Apr_2017_without_commission(LocalDate.of(2017, 2, 1), LocalDate.of(2017, 4, 28), 0, GameType.ANY),
    Feb_Apr_2017_wit_commission(LocalDate.of(2017, 2, 1), LocalDate.of(2017, 4, 28), 0.001, GameType.ANY),
    Jun_Aug_2017_without_commission(LocalDate.of(2017, 6, 1), LocalDate.of(2017, 8, 31), 0, GameType.PROD),
    Jun_Aug_2017_with_commission(LocalDate.of(2017, 6, 1), LocalDate.of(2017, 8, 31), 0.001, GameType.PROD);
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
