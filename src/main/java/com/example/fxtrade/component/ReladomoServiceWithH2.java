package com.example.fxtrade.component;

import com.example.fxtrade.FxTradeApplication;
import com.example.fxtrade.utils.reladomo.RateInitializer;
import com.example.fxtrade.utils.reladomo.ReladomoConnectionManagerWithH2;
import com.example.fxtrade.utils.reladomo.ReladomoConnectionManagerWithPostgresql;
import com.gs.fw.common.mithra.MithraManagerProvider;
import jakarta.annotation.PostConstruct;
import org.eclipse.collections.api.factory.Lists;
import org.eclipse.collections.api.list.MutableList;
import org.h2.tools.RunScript;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URL;
import java.sql.Connection;
import java.sql.SQLException;

@Component
@ConditionalOnProperty(name = "feature.dbtype", havingValue = "H2")
public class ReladomoServiceWithH2 {
    private static final Logger LOGGER = LoggerFactory.getLogger(ReladomoServiceWithH2.class);
    private static final String CONFIG_FILE_PATH = "reladomo/ReladomoRuntimeConfigWithH2.xml";
    public ReladomoServiceWithH2() {
    }

    @PostConstruct
    public void setup() {
        LOGGER.info("Reading reladomo config {}", CONFIG_FILE_PATH);
        try (InputStream is = FxTradeApplication.class.getClassLoader()
                .getResourceAsStream(CONFIG_FILE_PATH)) {
            MithraManagerProvider.getMithraManager()
                    .readConfiguration(is);
        } catch (IOException exc) {
            exc.printStackTrace();
        }

        LOGGER.info("Setting up tables in H2");
        MutableList<String> files = Lists.mutable.of("BALANCE.ddl", "RATE.ddl", "SESSION.ddl");
        try (Connection conn = ReladomoConnectionManagerWithH2.getInstance().getConnection()) {
            files.forEach(file -> {
                URL url = FxTradeApplication.class.getClassLoader().getResource("generated-db/sql/" + file);
                try {
                    BufferedReader in = new BufferedReader(new InputStreamReader(url.openStream()));
                    RunScript.execute(conn, in);
                } catch (SQLException e) {
                    throw new RuntimeException(e);
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
            });
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }

        LOGGER.info("Setting up rates");
        RateInitializer.run();
    }
}
