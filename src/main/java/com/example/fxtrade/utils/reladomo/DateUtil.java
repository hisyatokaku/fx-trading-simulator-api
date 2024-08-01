package com.example.fxtrade.utils.reladomo;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.util.Date;

public class DateUtil {
    public static Date toDate(LocalDate date) {
        return java.sql.Date.valueOf(date);
    }

    public static LocalDate toLocalDate(Date date) {
        return new java.sql.Date(date.getTime()).toLocalDate();
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
}
