package com.example.fxtrade.manager;

import com.example.fxtrade.models.Session;
import com.example.fxtrade.utils.reladomo.DateUtil;
import org.eclipse.collections.api.factory.Lists;
import org.eclipse.collections.api.tuple.Pair;
import org.eclipse.collections.impl.factory.Maps;
import org.eclipse.collections.impl.tuple.Tuples;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

public class GameConfigGenerator {
    private static final Map<String, Pair<LocalDate, LocalDate>> SCENARIO_TO_DATES = Maps.mutable.of(
            "test0", Tuples.pair(LocalDate.of(2016, 1, 4), LocalDate.of(2016, 1, 11)),
            "test1", Tuples.pair(LocalDate.of(2017, 1, 4), LocalDate.of(2017, 1, 11)),
            "test2", Tuples.pair(LocalDate.of(2018, 1, 4), LocalDate.of(2018, 1, 11)),
            "test3", Tuples.pair(LocalDate.of(2019, 1, 4), LocalDate.of(2019, 1, 11))
    ).withKeyValue("day2-0", Tuples.pair(LocalDate.of(2016, 1, 4), LocalDate.of(2016, 12, 31))
    ).withKeyValue("day2-1", Tuples.pair(LocalDate.of(2017, 1, 4), LocalDate.of(2017, 12, 31))
    ).withKeyValue("day2-2", Tuples.pair(LocalDate.of(2019, 1, 4), LocalDate.of(2019, 12, 31))
    ).withKeyValue("day2-3", Tuples.pair(LocalDate.of(2020, 1, 6), LocalDate.of(2020, 12, 31))
    ).withKeyValue("day3-x", Tuples.pair(LocalDate.of(2018, 1, 4), LocalDate.of(2018, 12, 31))
    ).withKeyValue("day3-y", Tuples.pair(LocalDate.of(2021, 1, 4), LocalDate.of(2021, 12, 31))
    );
    public static void setUpSession(Session session, String scenario) {
        if(!SCENARIO_TO_DATES.containsKey(scenario)) {
            throw new IllegalStateException("Scenario " + scenario + " does not exist");
        }
        Pair<LocalDate, LocalDate> dates = SCENARIO_TO_DATES.get(scenario);
        session.setStartDate(DateUtil.toDate(dates.getOne()));
        session.setEndDate(DateUtil.toDate(dates.getTwo()));
        session.setCurrentDate(DateUtil.toDate(dates.getOne()));
        session.setScenario(scenario);
    }

    public static List<LocalDate> getDates(String scenario) {
        Pair<LocalDate, LocalDate> startAndEndDates = SCENARIO_TO_DATES.get(scenario);
        LocalDate startDate = startAndEndDates.getOne();
        LocalDate endDate = startAndEndDates.getTwo();
        List<LocalDate> dates = Lists.mutable.empty();
        for (LocalDate date = startDate; date.isEqual(endDate) || date.isBefore(endDate); date = DateUtil.nextBusinessDate(date)) {
            dates.add(date);
        }
        return dates;
    }
}
