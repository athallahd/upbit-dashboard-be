-- Optional, manual performance indexes for Operational Executive Dashboard.
--
-- Inspected on the local reporter database on 2026-08-10:
--   * member_additional_info already has (state, updated_at, member_uuid)
--   * user_info already has an index on created_at and a unique member_uuid
--   * deposit_base is missing (target_date, member_id)
--   * trade_base is missing the two date-and-participant composite indexes
--
-- Run each statement only once, after checking SHOW INDEX FROM <table>.
-- These statements are intentionally not part of local-db/init and are never
-- applied by Django migrations because the reporting source tables are unmanaged.

CREATE INDEX idx_deposit_base_date_member
    ON deposit_base (target_date, member_id);

CREATE INDEX idx_trade_base_date_buyer
    ON trade_base (trade_date, b_customer_code);

CREATE INDEX idx_trade_base_date_seller
    ON trade_base (trade_date, s_customer_code);
