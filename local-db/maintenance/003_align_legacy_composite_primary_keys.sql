-- Align existing local legacy tables with their Django CompositePrimaryKey
-- mappings. This is manual maintenance SQL: it is not a Django migration and
-- is not run by any container initializer.
--
-- Preconditions verified on the local database before execution:
--   * member_id is NOT NULL on both tables.
--   * there are no duplicate (identifier, member_id) pairs.
--   * neither table is referenced by an inbound foreign key.

ALTER TABLE deposit_base
    DROP PRIMARY KEY,
    ADD PRIMARY KEY (deposit_id, member_id);

ALTER TABLE withdraw_base
    DROP PRIMARY KEY,
    ADD PRIMARY KEY (withdraw_id, member_id);

-- Post-change verification.
SHOW KEYS FROM deposit_base WHERE Key_name = 'PRIMARY';
SHOW KEYS FROM withdraw_base WHERE Key_name = 'PRIMARY';
