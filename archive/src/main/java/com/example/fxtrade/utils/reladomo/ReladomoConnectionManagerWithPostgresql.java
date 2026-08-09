package com.example.fxtrade.utils.reladomo;

import com.gs.fw.common.mithra.bulkloader.BulkLoader;
import com.gs.fw.common.mithra.bulkloader.BulkLoaderException;
import com.gs.fw.common.mithra.connectionmanager.SourcelessConnectionManager;
import com.gs.fw.common.mithra.connectionmanager.XAConnectionManager;
import com.gs.fw.common.mithra.databasetype.DatabaseType;
import com.gs.fw.common.mithra.databasetype.PostgresDatabaseType;

import java.sql.Connection;
import java.util.TimeZone;

public class ReladomoConnectionManagerWithPostgresql implements SourcelessConnectionManager {

    private static ReladomoConnectionManagerWithPostgresql instance;
    private XAConnectionManager xaConnectionManager;

    private ReladomoConnectionManagerWithPostgresql(String hostUrl, String port, String user, String password, String schema) {
        xaConnectionManager = this.createConnectionManager(hostUrl, port, user, password, schema);
    }

    public static SourcelessConnectionManager getInstance() {
        if (instance == null) {
            throw new RuntimeException("Instance should be initialized before getting it");
        }
        return instance;
    }

    public static ReladomoConnectionManagerWithPostgresql setInstance(String hostUrl, String port, String user, String password, String schema) {
        instance = new ReladomoConnectionManagerWithPostgresql(hostUrl, port, user, password, schema);
        return instance;
    }

    private XAConnectionManager createConnectionManager(String hostUrl, String port, String user, String password, String schema) {
        xaConnectionManager = new XAConnectionManager();
        xaConnectionManager.setDriverClassName("org.postgresql.Driver");
        xaConnectionManager.setJdbcConnectionString("jdbc:postgresql://" + hostUrl + ":" + port +"/" + schema);
        xaConnectionManager.setJdbcUser(user);
        xaConnectionManager.setJdbcPassword(password);
        xaConnectionManager.setPoolName("Fxtrade");
        xaConnectionManager.setInitialSize(1);
        xaConnectionManager.setPoolSize(10);
        xaConnectionManager.setDefaultSchemaName(schema);
        xaConnectionManager.initialisePool();
        return xaConnectionManager;
    }

    @Override
    public Connection getConnection() {
        return xaConnectionManager.getConnection();
    }

    @Override
    public DatabaseType getDatabaseType() {
        return PostgresDatabaseType.getInstance();
    }

    @Override
    public TimeZone getDatabaseTimeZone() {
        return TimeZone.getDefault();
    }

    @Override
    public String getDatabaseIdentifier() {
        return "fxtrade";
    }

    @Override
    public BulkLoader createBulkLoader() throws BulkLoaderException {
        return null;
    }
}
