package com.example.fxtrade.utils.reladomo;

import com.gs.fw.common.mithra.bulkloader.BulkLoader;
import com.gs.fw.common.mithra.bulkloader.BulkLoaderException;
import com.gs.fw.common.mithra.connectionmanager.SourcelessConnectionManager;
import com.gs.fw.common.mithra.connectionmanager.XAConnectionManager;
import com.gs.fw.common.mithra.databasetype.DatabaseType;
import com.gs.fw.common.mithra.databasetype.H2DatabaseType;

import java.sql.Connection;
import java.util.TimeZone;

public class ReladomoConnectionManagerWithH2 implements SourcelessConnectionManager {

    private static ReladomoConnectionManagerWithH2 instance;
    private XAConnectionManager xaConnectionManager;

    public static synchronized SourcelessConnectionManager getInstance() {
        if (instance == null) {
            instance = new ReladomoConnectionManagerWithH2();
        }
        return instance;
    }

    private ReladomoConnectionManagerWithH2() {
        xaConnectionManager = this.createConnectionManager();
    }

    private XAConnectionManager createConnectionManager() {
        xaConnectionManager = new XAConnectionManager();
        xaConnectionManager.setDriverClassName("org.h2.Driver");
        xaConnectionManager.setJdbcConnectionString("jdbc:h2:mem:myDb");
        xaConnectionManager.setJdbcUser("sa");
        xaConnectionManager.setJdbcPassword("");
        xaConnectionManager.setPoolName("My Connection Pool");
        xaConnectionManager.setInitialSize(1);
        xaConnectionManager.setPoolSize(10);
        xaConnectionManager.initialisePool();
        return xaConnectionManager;
    }

    @Override
    public Connection getConnection() {
        return xaConnectionManager.getConnection();
    }

    @Override
    public DatabaseType getDatabaseType() {
        return H2DatabaseType.getInstance();
    }

    @Override
    public TimeZone getDatabaseTimeZone() {
        return TimeZone.getDefault();
    }

    @Override
    public String getDatabaseIdentifier() {
        return "myDb";
    }

    @Override
    public BulkLoader createBulkLoader() throws BulkLoaderException {
        return null;
    }
}
