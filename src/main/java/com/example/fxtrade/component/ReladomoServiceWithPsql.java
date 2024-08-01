package com.example.fxtrade.component;

import com.example.fxtrade.FxTradeApplication;
import com.example.fxtrade.utils.reladomo.RateInitializer;
import com.example.fxtrade.utils.reladomo.ReladomoConnectionManagerWithPostgresql;
import com.gs.fw.common.mithra.MithraManagerProvider;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.PropertySource;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.io.InputStream;

@Component
@ConditionalOnProperty(name = "feature.dbtype", havingValue = "PSQL")
public class ReladomoServiceWithPsql {
    private static final Logger LOGGER = LoggerFactory.getLogger(ReladomoServiceWithPsql.class);
    private static final String CONFIG_FILE_PATH = "reladomo/ReladomoRuntimeConfigWithPostgresql.xml";
    @Value("${db.hostUrl}")
    private String hostUrl;
    @Value("${db.port}")
    private String port;
    @Value("${db.user}")
    private String user;
    @Value("${db.password}")
    private String password;
    @Value("${db.schema}")
    private String schema;
    public ReladomoServiceWithPsql() {
    }

    @PostConstruct
    public void setup() {
        LOGGER.info("Reading reladomo config {}", CONFIG_FILE_PATH);
        ReladomoConnectionManagerWithPostgresql.setInstance(hostUrl, port, user, password, schema);

        try (InputStream is = FxTradeApplication.class.getClassLoader()
                .getResourceAsStream(CONFIG_FILE_PATH)) {
            MithraManagerProvider.getMithraManager()
                    .readConfiguration(is);
        } catch (IOException exc) {
            exc.printStackTrace();
        }

        LOGGER.info("Setting up rates");
        RateInitializer.run();
    }
}
