package com.example.fxtrade.utils.reladomo;

import com.example.fxtrade.FxTradeApplication;
import com.example.fxtrade.models.*;
import org.eclipse.collections.api.RichIterable;
import org.eclipse.collections.api.factory.Lists;
import org.eclipse.collections.api.list.MutableList;
import org.eclipse.collections.api.map.MutableMap;
import org.eclipse.collections.api.multimap.Multimap;
import org.eclipse.collections.impl.tuple.Tuples;
import org.eclipse.collections.impl.utility.ArrayIterate;
import org.eclipse.collections.impl.utility.Iterate;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.time.DayOfWeek;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.List;

public class TraderInitializer {
    public static void run() {
        InputStream resourceAsStream = FxTradeApplication.class.getClassLoader().getResourceAsStream("data/traders.csv");
        try {
            TraderFinder.findMany(TraderFinder.all()).deleteAllInBatches(1000);

            InputStreamReader isr = new InputStreamReader(resourceAsStream, "UTF-8");
            BufferedReader reader = new BufferedReader(isr);
            TraderList traders = new TraderList();
            while(reader.ready()) {
                String[] data = reader.readLine().split(",");
                Trader trader = new Trader(data[0], data[1]);
                traders.add(trader);
            }
            traders.insertAll();
        } catch (IOException e) {

        }
    }
}
