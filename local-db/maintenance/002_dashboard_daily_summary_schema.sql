-- Manual, SQL-owned schema for the Operational Executive Dashboard cache.
--
-- This file is intentionally outside local-db/init, is not a Django migration,
-- and is never run automatically. Execute it manually only after reviewing the
-- target database and source-data refresh process.

CREATE TABLE IF NOT EXISTS dashboard_daily_summary (
    target_date DATE NOT NULL,
    inbound_users INT UNSIGNED NOT NULL DEFAULT 0,
    approved_users INT UNSIGNED NOT NULL DEFAULT 0,
    first_deposit_users INT UNSIGNED NOT NULL DEFAULT 0,
    repeat_deposit_users INT UNSIGNED NOT NULL DEFAULT 0,
    first_trade_users INT UNSIGNED NOT NULL DEFAULT 0,
    repeat_trade_users INT UNSIGNED NOT NULL DEFAULT 0,
    dormant_users INT UNSIGNED NOT NULL DEFAULT 0,
    trade_count INT UNSIGNED NOT NULL DEFAULT 0,
    trading_users INT UNSIGNED NOT NULL DEFAULT 0,
    total_volume_idr DECIMAL(38, 20) NOT NULL DEFAULT 0,
    revenue_idr DECIMAL(38, 20) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (target_date)
) ENGINE=InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;

-- Verify the schema after manual execution.
SHOW COLUMNS FROM dashboard_daily_summary;
SHOW INDEX FROM dashboard_daily_summary;
