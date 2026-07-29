package com.example.fxtrade.utils.reladomo;

import com.example.fxtrade.models.RateFinder;
import com.example.fxtrade.models.RateList;

import java.sql.Timestamp;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Date;

public class DateUtil {
    public static Date toDate(LocalDate date) {
        return java.sql.Date.valueOf(date);
    }

    public static LocalDate toLocalDate(Date date) {
        return new java.sql.Date(date.getTime()).toLocalDate();
    }

    public static Timestamp toTimestamp(LocalDateTime dateTime) {
        return Timestamp.valueOf(dateTime);
    }

    public static LocalDateTime toLocalDateTime(Timestamp timestamp) {
        return timestamp.toLocalDateTime();
    }

    public static LocalDate nextBusinessDate(LocalDate date) {
        DayOfWeek dayOfWeek = date.getDayOfWeek();
        if(dayOfWeek.equals(DayOfWeek.FRIDAY)) {
            return date.plusDays(3);
        } else if(dayOfWeek.equals(DayOfWeek.SATURDAY)) {
            return date.plusDays(2);
        }
        return date.plusDays(1);
    }

    /**
     * Data-driven replacement for nextBusinessDate: the next tick is whatever
     * timestamp actually has rate data after `current`, rather than a calendar
     * calculation. This naturally skips weekends/holidays/closed-market gaps
     * because no Rate row exists for them.
     */
    public static Timestamp nextAvailableTimestamp(Timestamp current, String referenceCurrency) {
        RateList rates = RateFinder.findMany(RateFinder.date().greaterThan(current).and(RateFinder.currency().eq(referenceCurrency)));
        rates.setOrderBy(RateFinder.date().ascendingOrderBy());
        rates.setMaxObjectsToRetrieve(1);
        if (rates.isEmpty()) {
            return null;
        }
        return rates.get(0).getDate();
    }

    public static Timestamp firstAvailableTimestampOnOrAfter(Timestamp from, String referenceCurrency) {
        RateList rates = RateFinder.findMany(RateFinder.date().greaterThanEquals(from).and(RateFinder.currency().eq(referenceCurrency)));
        rates.setOrderBy(RateFinder.date().ascendingOrderBy());
        rates.setMaxObjectsToRetrieve(1);
        if (rates.isEmpty()) {
            return null;
        }
        return rates.get(0).getDate();
    }

    public static Timestamp lastAvailableTimestampOnOrBefore(Timestamp to, String referenceCurrency) {
        RateList rates = RateFinder.findMany(RateFinder.date().lessThanEquals(to).and(RateFinder.currency().eq(referenceCurrency)));
        rates.setOrderBy(RateFinder.date().descendingOrderBy());
        rates.setMaxObjectsToRetrieve(1);
        if (rates.isEmpty()) {
            return null;
        }
        return rates.get(0).getDate();
    }
}
