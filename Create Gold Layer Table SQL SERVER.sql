IF DB_ID('HardwareStoreRetail') IS NULL
    CREATE DATABASE HardwareStoreRetail;
GO

USE HardwareStoreRetail;
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'bronze')
    EXEC('CREATE SCHEMA bronze');
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'silver')
    EXEC('CREATE SCHEMA silver');
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'gold')
    EXEC('CREATE SCHEMA gold');
GO

DROP TABLE IF EXISTS gold.mastercat;
GO

CREATE TABLE gold.mastercat (
    product_code      INT,
    full_description  VARCHAR(50),
    prod_status       VARCHAR(50),
    total_qty         DECIMAL(18,2),
    minimum_stock     INT,
    maximum_stock     INT,
    stock_value       DECIMAL(18,2),
    last_full_check   DATE,
    last_sale_date    DATE,
    days_last_sold    INT,
    stock_supplier    VARCHAR(50),
    supplier_name     VARCHAR(50),
    standard_cost     DECIMAL(18,2),
    avg_unit          VARCHAR(50),
    avg_cost          DECIMAL(18,2),
    last_purch_price  DECIMAL(18,2),
    pur_net_cost      DECIMAL(18,2),
    sl_level          VARCHAR(50),
    list_price        DECIMAL(18,2),
    base              DECIMAL(18,2),
    retail            DECIMAL(18,2),
    mu_pct_from_base  DECIMAL(18,2),
    gp_pct_from_avg   DECIMAL(18,2),
    pct_base_v_avg    DECIMAL(18,2),
    pct_base_v_list   DECIMAL(18,2),
    pct_base_v_nett   DECIMAL(18,2),
    class             VARCHAR(50),
    lyr_num_demands   INT,
    age_status        VARCHAR(50),
    omc               VARCHAR(50),
    date_modified     DATE
);
GO