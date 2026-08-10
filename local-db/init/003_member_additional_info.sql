-- KYC source table for the Executive Dashboard.
--
-- Source: market-surveillance/data/raw/member-additional-info.csv
-- Business rule currently agreed:
--   state = 'accept' means approved.
--   updated_at is the state-change timestamp.
--
-- The table is deliberately non-destructive. Import the CSV with DBeaver after
-- running this DDL. Do not use the CSV as a runtime data source in Django.

CREATE TABLE IF NOT EXISTS member_additional_info (
    id BIGINT UNSIGNED NOT NULL,
    member_uuid CHAR(36) NULL,
    uuid CHAR(36) NULL,
    laser_number VARCHAR(191) NULL,
    education_level VARCHAR(191) NULL,
    marital_status VARCHAR(191) NULL,
    objective VARCHAR(255) NULL,
    occupation VARCHAR(255) NULL,
    position VARCHAR(191) NULL,
    range_of_income VARCHAR(191) NULL,
    job_type VARCHAR(191) NULL,
    source_of_funds VARCHAR(255) NULL,
    company_name VARCHAR(255) NULL,
    company_address VARCHAR(512) NULL,
    w9_form_id VARCHAR(191) NULL,
    w8ben_form_id VARCHAR(191) NULL,
    supported_document_1_id VARCHAR(191) NULL,
    supported_document_2_id VARCHAR(191) NULL,
    suitability_test_score DECIMAL(10, 4) NULL,
    knowledge_test_passed TINYINT UNSIGNED NULL,
    phone_number VARCHAR(32) NULL,
    state VARCHAR(32) NULL,
    created_at DATETIME(6) NULL,
    updated_at DATETIME(6) NULL,
    npwp_number VARCHAR(64) NULL,
    mother_name VARCHAR(255) NULL,
    suitability_test_at DATETIME(6) NULL,
    occupation_detail VARCHAR(255) NULL,
    company_phone_number VARCHAR(32) NULL,
    other_information TEXT NULL,

    PRIMARY KEY (id),
    KEY idx_member_additional_info_member_uuid_updated (
        member_uuid,
        updated_at
    ),
    KEY idx_member_additional_info_state_updated_member (
        state,
        updated_at,
        member_uuid
    ),
    KEY idx_member_additional_info_updated_at (updated_at)
)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;

-- Confirm the imported table structure.
SHOW COLUMNS FROM member_additional_info;

-- Basic import validation.
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT id) AS distinct_ids,
    COUNT(DISTINCT member_uuid) AS distinct_members,
    SUM(state = 'accept') AS accepted_rows,
    SUM(state = 'reject') AS rejected_rows,
    SUM(state = 'expired') AS expired_rows,
    SUM(state = 'PENDING') AS pending_rows,
    MIN(updated_at) AS earliest_state_change,
    MAX(updated_at) AS latest_state_change
FROM member_additional_info;

-- Check whether the member UUID can be joined to user_info.
SELECT
    COUNT(DISTINCT k.member_uuid) AS kyc_members,
    COUNT(DISTINCT u.member_uuid) AS matched_user_members,
    COUNT(DISTINCT CASE WHEN u.member_uuid IS NULL THEN k.member_uuid END)
        AS unmatched_kyc_members
FROM member_additional_info AS k
LEFT JOIN user_info AS u
    ON u.member_uuid = k.member_uuid;

-- Preview the rows that will be used for approval calculations.
SELECT
    member_uuid,
    state,
    updated_at
FROM member_additional_info
WHERE LOWER(TRIM(state)) = 'accept'
ORDER BY updated_at DESC
LIMIT 20;
