-- ============================================================================
-- CRASH GAME ANALYTICS DATABASE SCHEMA
-- For: Aviator (Spribe), Aviatrix (Aviatrix Labs), JetX (SmartSoft)
-- Purpose: Complete round history, analytics, and training data logging
-- ============================================================================

-- Create ENUM types for better data integrity
CREATE TYPE game_type AS ENUM ('aviator', 'aviatrix', 'jetx');
CREATE TYPE vm_provider AS ENUM ('vastai', 'runpod', 'digitalocean', 'aws', 'gcp', 'local');
CREATE TYPE strategy_type AS ENUM ('compound_1.33x', 'martingale', 'custom', 'fixed_stake', 'kelly_criterion');
CREATE TYPE round_outcome AS ENUM ('WIN', 'LOSS', 'SKIP', 'ERROR');
CREATE TYPE error_type AS ENUM (
    'bet_failed', 'no_multiplier', 'early_crash', 'ocr_error',
    'network_drop', 'timeout', 'insufficient_balance', 'unknown'
);

-- ============================================================================
-- SECTION 1: BOT / VM IDENTIFICATION TABLE
-- ============================================================================
CREATE TABLE bot_vm_registration (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(50) UNIQUE NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    vm_name VARCHAR(100) NOT NULL,
    vm_provider vm_provider NOT NULL,
    region VARCHAR(50) NOT NULL,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    strategy_name strategy_type NOT NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    -- Configuration
    initial_balance DECIMAL(15, 2),
    base_stake DECIMAL(15, 2),
    max_stake DECIMAL(15, 2),

    CONSTRAINT positive_balance CHECK (initial_balance > 0),
    CONSTRAINT positive_stake CHECK (base_stake > 0 AND max_stake >= base_stake)
);

-- ============================================================================
-- SECTION 2: PLATFORM & GAME DETAILS TABLE
-- ============================================================================
CREATE TABLE game_platform_config (
    id SERIAL PRIMARY KEY,
    game_name game_type NOT NULL,
    platform_code VARCHAR(50) NOT NULL,
    platform_url VARCHAR(255),
    round_external_id_format VARCHAR(100),
    currency VARCHAR(10) DEFAULT 'USD',

    -- RTP and game characteristics
    house_edge_percent DECIMAL(5, 2),
    min_multiplier DECIMAL(10, 2) DEFAULT 1.0,
    max_multiplier DECIMAL(10, 2) DEFAULT 1000.0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    UNIQUE (game_name, platform_code)
);

-- ============================================================================
-- MAIN ROUNDS TABLE - COMPLETE ROUND HISTORY
-- ============================================================================
CREATE TABLE crash_game_rounds (
    id BIGSERIAL PRIMARY KEY,

    -- Bot / VM Identification
    bot_id VARCHAR(50) NOT NULL REFERENCES bot_vm_registration(bot_id),
    session_id VARCHAR(100) NOT NULL,

    -- Platform & Game Details
    game_name game_type NOT NULL,
    platform_code VARCHAR(50) NOT NULL,
    round_external_id VARCHAR(100),
    currency VARCHAR(10),

    -- SECTION 3: ROUND TIMING
    round_number BIGINT NOT NULL,
    round_start_timestamp TIMESTAMP NOT NULL,
    round_end_timestamp TIMESTAMP,
    duration_seconds DECIMAL(10, 3),
    processing_time_ms INTEGER,

    -- SECTION 4: STAKE & STRATEGY
    stake_value DECIMAL(15, 2) NOT NULL,
    stake_before_update DECIMAL(15, 2),
    stake_after_update DECIMAL(15, 2),
    strategy_name strategy_type NOT NULL,
    target_multiplier DECIMAL(10, 4),
    manual_override_flag BOOLEAN DEFAULT FALSE,
    stake_placement_result VARCHAR(50), -- success/fail

    -- SECTION 5: MULTIPLIERS
    crash_multiplier_detected DECIMAL(10, 4),
    cashout_multiplier DECIMAL(10, 4),
    final_multiplier DECIMAL(10, 4),
    multiplier_source VARCHAR(50), -- 'ocr', 'api', 'manual'

    -- SECTION 6: FINANCIALS
    cashout_amount DECIMAL(15, 2),
    profit_loss_amount DECIMAL(15, 2),
    running_balance_before DECIMAL(15, 2),
    running_balance_after DECIMAL(15, 2),
    expected_profit DECIMAL(15, 2),
    variance_from_strategy DECIMAL(15, 2),
    roi_percent DECIMAL(10, 4),

    -- SECTION 7: OCR / DETECTION LOGS
    ocr_raw_text TEXT,
    ocr_cleaned_value DECIMAL(10, 4),
    multiplier_detection_confidence DECIMAL(5, 4),
    cashout_detection_confidence DECIMAL(5, 4),
    ocr_timeout_flag BOOLEAN DEFAULT FALSE,
    screenshot_reference_id VARCHAR(100),

    -- SECTION 8: OUTCOME & ERRORS
    round_outcome round_outcome,
    error_type error_type,
    error_description TEXT,
    recovery_action_taken VARCHAR(255),
    retry_count INTEGER DEFAULT 0,

    -- SECTION 9: METADATA (JSONB for flexibility)
    metadata JSONB,

    -- Record management
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT positive_stake CHECK (stake_value > 0),
    CONSTRAINT valid_multipliers CHECK (
        (crash_multiplier_detected IS NULL OR crash_multiplier_detected >= 1.0) AND
        (cashout_multiplier IS NULL OR cashout_multiplier >= 1.0) AND
        (final_multiplier IS NULL OR final_multiplier >= 1.0)
    ),
    CONSTRAINT valid_confidence CHECK (
        (multiplier_detection_confidence >= 0 AND multiplier_detection_confidence <= 1) AND
        (cashout_detection_confidence >= 0 AND cashout_detection_confidence <= 1)
    ),
    CONSTRAINT valid_balance CHECK (
        running_balance_before > 0 AND running_balance_after > 0
    )
);

-- ============================================================================
-- SECTION 10: INDEXES FOR PERFORMANCE
-- ============================================================================

-- Timestamp indexes
CREATE INDEX idx_crash_rounds_start_ts ON crash_game_rounds(round_start_timestamp DESC);
CREATE INDEX idx_crash_rounds_end_ts ON crash_game_rounds(round_end_timestamp DESC);

-- Bot and session indexes
CREATE INDEX idx_crash_rounds_bot_session ON crash_game_rounds(bot_id, session_id, round_number);

-- Game and platform indexes
CREATE INDEX idx_crash_rounds_game_platform ON crash_game_rounds(game_name, platform_code);

-- Strategy and outcome indexes
CREATE INDEX idx_crash_rounds_strategy_outcome ON crash_game_rounds(strategy_name, round_outcome);

-- Composite index for analytics queries
CREATE INDEX idx_crash_rounds_analytics ON crash_game_rounds(
    bot_id,
    round_start_timestamp DESC,
    round_outcome,
    profit_loss_amount
);

-- JSON metadata search
CREATE INDEX idx_crash_rounds_metadata ON crash_game_rounds USING GIN(metadata);

-- ============================================================================
-- ANALYTICS TABLE 1: ROUND MULTIPLIER DATA
-- For training and signal generation: roundid, multiplier, timestamp
-- ============================================================================
CREATE TABLE analytics_round_multipliers (
    id BIGSERIAL PRIMARY KEY,

    -- Core training fields
    round_id BIGINT NOT NULL REFERENCES crash_game_rounds(id) ON DELETE CASCADE,
    round_external_id VARCHAR(100),
    multiplier DECIMAL(10, 4) NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    -- Additional context for ML
    bot_id VARCHAR(50) NOT NULL,
    game_name game_type NOT NULL,
    platform_code VARCHAR(50),

    -- Multiplier characteristics
    is_crash_multiplier BOOLEAN DEFAULT FALSE,
    is_cashout_multiplier BOOLEAN DEFAULT FALSE,
    max_in_round BOOLEAN DEFAULT FALSE,

    -- Confidence and quality
    ocr_confidence DECIMAL(5, 4),
    data_quality_score DECIMAL(5, 4),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- For fast aggregation queries
    date_bucket DATE GENERATED ALWAYS AS (DATE(timestamp)) STORED
);

-- Indexes for analytics table 1
CREATE INDEX idx_analytics_multipliers_round ON analytics_round_multipliers(round_id);
CREATE INDEX idx_analytics_multipliers_timestamp ON analytics_round_multipliers(timestamp DESC);
CREATE INDEX idx_analytics_multipliers_bot_game ON analytics_round_multipliers(bot_id, game_name);
CREATE INDEX idx_analytics_multipliers_date_bucket ON analytics_round_multipliers(date_bucket DESC);
CREATE INDEX idx_analytics_multipliers_multiplier ON analytics_round_multipliers(multiplier);

-- ============================================================================
-- ANALYTICS TABLE 2: ROUND SIGNALS & PREDICTIONS
-- For ML feature generation and pattern detection
-- ============================================================================
CREATE TABLE analytics_round_signals (
    id BIGSERIAL PRIMARY KEY,

    -- Link to main round
    round_id BIGINT NOT NULL REFERENCES crash_game_rounds(id) ON DELETE CASCADE,
    round_number BIGINT NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    -- Bot context
    bot_id VARCHAR(50) NOT NULL,
    game_name game_type NOT NULL,

    -- Signal features (pre-computed for ML)
    signal_type VARCHAR(100), -- 'pre_flight', 'early_flight', 'peak_approaching', 'crash_imminent'
    confidence_score DECIMAL(5, 4),
    signal_strength DECIMAL(5, 4),

    -- Timing signals
    time_to_crash_predicted_ms INTEGER,
    volatility_measure DECIMAL(10, 6),
    momentum_score DECIMAL(5, 4),

    -- Pattern recognition
    pattern_match_type VARCHAR(100), -- 'exponential', 'linear', 'accelerating', 'anomaly'
    similar_rounds_count INTEGER,

    -- Outcome tracking
    signal_correctness BOOLEAN, -- Was prediction correct?
    actual_multiplier DECIMAL(10, 4),
    prediction_error DECIMAL(10, 4),

    -- Feature vector (JSON for complex data)
    feature_vector JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_bucket DATE GENERATED ALWAYS AS (DATE(timestamp)) STORED
);

-- Indexes for analytics table 2
CREATE INDEX idx_analytics_signals_round ON analytics_round_signals(round_id);
CREATE INDEX idx_analytics_signals_timestamp ON analytics_round_signals(timestamp DESC);
CREATE INDEX idx_analytics_signals_bot_game ON analytics_round_signals(bot_id, game_name);
CREATE INDEX idx_analytics_signals_signal_type ON analytics_round_signals(signal_type);
CREATE INDEX idx_analytics_signals_confidence ON analytics_round_signals(confidence_score DESC);
CREATE INDEX idx_analytics_signals_pattern ON analytics_round_signals(pattern_match_type);

-- ============================================================================
-- ANALYTICS TABLE 3: ROUND OUTCOME & STATISTICS
-- Denormalized table for fast reporting and aggregation
-- ============================================================================
CREATE TABLE analytics_round_outcomes (
    id BIGSERIAL PRIMARY KEY,

    -- Link to main round
    round_id BIGINT NOT NULL REFERENCES crash_game_rounds(id) ON DELETE CASCADE,
    round_number BIGINT NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    -- Bot context
    bot_id VARCHAR(50) NOT NULL,
    game_name game_type NOT NULL,
    platform_code VARCHAR(50),
    strategy_name strategy_type,

    -- Outcome
    outcome round_outcome NOT NULL,
    profit_loss DECIMAL(15, 2),
    roi_percent DECIMAL(10, 4),

    -- Statistical metrics
    bet_amount DECIMAL(15, 2),
    winnings DECIMAL(15, 2),
    loss_amount DECIMAL(15, 2),

    -- Multiplier data
    target_multiplier DECIMAL(10, 4),
    actual_multiplier DECIMAL(10, 4),
    multiplier_error DECIMAL(10, 4),
    hit_target BOOLEAN,

    -- Streaks
    win_streak_length INTEGER,
    loss_streak_length INTEGER,

    -- Classification
    outcome_category VARCHAR(50), -- 'big_win', 'small_win', 'small_loss', 'catastrophic_loss'

    -- Timing
    duration_seconds DECIMAL(10, 3),
    date_bucket DATE GENERATED ALWAYS AS (DATE(timestamp)) STORED,
    hour_bucket INTEGER GENERATED ALWAYS AS (EXTRACT(HOUR FROM timestamp)) STORED,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for analytics table 3
CREATE INDEX idx_analytics_outcomes_round ON analytics_round_outcomes(round_id);
CREATE INDEX idx_analytics_outcomes_timestamp ON analytics_round_outcomes(timestamp DESC);
CREATE INDEX idx_analytics_outcomes_bot_game ON analytics_round_outcomes(bot_id, game_name);
CREATE INDEX idx_analytics_outcomes_outcome ON analytics_round_outcomes(outcome);
CREATE INDEX idx_analytics_outcomes_date ON analytics_round_outcomes(date_bucket DESC, bot_id);
CREATE INDEX idx_analytics_outcomes_strategy ON analytics_round_outcomes(strategy_name, outcome);

-- ============================================================================
-- SUPPORTING TABLES FOR DATA QUALITY
-- ============================================================================

-- OCR validation logs
CREATE TABLE ocr_validation_logs (
    id BIGSERIAL PRIMARY KEY,
    round_id BIGINT REFERENCES crash_game_rounds(id) ON DELETE CASCADE,
    bot_id VARCHAR(50) NOT NULL,

    raw_ocr_text TEXT NOT NULL,
    cleaned_value DECIMAL(10, 4),
    confidence DECIMAL(5, 4),
    validation_status VARCHAR(50),

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ocr_round ON ocr_validation_logs(round_id);
CREATE INDEX idx_ocr_timestamp ON ocr_validation_logs(timestamp DESC);

-- Error logs
CREATE TABLE error_logs (
    id BIGSERIAL PRIMARY KEY,
    round_id BIGINT REFERENCES crash_game_rounds(id) ON DELETE CASCADE,
    bot_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(100),

    error_type error_type NOT NULL,
    error_message TEXT,
    error_trace TEXT,
    recovery_action VARCHAR(255),

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_error_round ON error_logs(round_id);
CREATE INDEX idx_error_type ON error_logs(error_type);
CREATE INDEX idx_error_timestamp ON error_logs(timestamp DESC);

-- Session logs
CREATE TABLE session_logs (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    game_name game_type NOT NULL,

    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds DECIMAL(10, 3),

    initial_balance DECIMAL(15, 2),
    final_balance DECIMAL(15, 2),
    total_profit_loss DECIMAL(15, 2),
    total_roi_percent DECIMAL(10, 4),

    total_rounds INTEGER,
    winning_rounds INTEGER,
    losing_rounds INTEGER,
    win_rate DECIMAL(5, 4),

    largest_win DECIMAL(15, 2),
    largest_loss DECIMAL(15, 2),
    average_win DECIMAL(15, 2),
    average_loss DECIMAL(15, 2),

    status VARCHAR(50), -- active, completed, error, interrupted
    notes TEXT
);

CREATE INDEX idx_session_bot ON session_logs(bot_id);
CREATE INDEX idx_session_start ON session_logs(start_time DESC);

-- ============================================================================
-- MATERIALIZED VIEW FOR QUICK AGGREGATIONS
-- ============================================================================
CREATE MATERIALIZED VIEW mv_daily_bot_stats AS
SELECT
    DATE(cgr.round_start_timestamp) as report_date,
    cgr.bot_id,
    cgr.game_name,
    COUNT(*) as total_rounds,
    COUNT(CASE WHEN cgr.round_outcome = 'WIN' THEN 1 END) as wins,
    COUNT(CASE WHEN cgr.round_outcome = 'LOSS' THEN 1 END) as losses,
    COALESCE(COUNT(CASE WHEN cgr.round_outcome = 'WIN' THEN 1 END)::DECIMAL / NULLIF(COUNT(*), 0), 0) as win_rate,
    SUM(cgr.profit_loss_amount) as total_profit_loss,
    AVG(cgr.profit_loss_amount) as avg_profit_loss,
    MIN(cgr.profit_loss_amount) as min_profit,
    MAX(cgr.profit_loss_amount) as max_profit,
    STDDEV(cgr.profit_loss_amount) as std_dev_profit
FROM crash_game_rounds cgr
GROUP BY DATE(cgr.round_start_timestamp), cgr.bot_id, cgr.game_name;

CREATE INDEX idx_mv_daily_stats_date_bot ON mv_daily_bot_stats(report_date DESC, bot_id);

-- ============================================================================
-- STORED PROCEDURES FOR COMMON OPERATIONS
-- ============================================================================

-- Function to log a round with automatic calculations
CREATE OR REPLACE FUNCTION log_crash_game_round(
    p_bot_id VARCHAR,
    p_session_id VARCHAR,
    p_game_name game_type,
    p_platform_code VARCHAR,
    p_stake_value DECIMAL,
    p_crash_multiplier DECIMAL,
    p_cashout_multiplier DECIMAL,
    p_outcome round_outcome,
    p_metadata JSONB DEFAULT NULL
) RETURNS BIGINT AS $$
DECLARE
    v_round_id BIGINT;
    v_running_balance DECIMAL;
    v_prev_balance DECIMAL;
    v_profit_loss DECIMAL;
BEGIN
    -- Get previous balance
    SELECT running_balance_after INTO v_prev_balance
    FROM crash_game_rounds
    WHERE bot_id = p_bot_id AND session_id = p_session_id
    ORDER BY round_number DESC LIMIT 1;

    -- Default to initial balance if first round
    IF v_prev_balance IS NULL THEN
        SELECT initial_balance INTO v_prev_balance
        FROM bot_vm_registration WHERE bot_id = p_bot_id;
    END IF;

    -- Calculate profit/loss
    IF p_outcome = 'WIN' THEN
        v_profit_loss := (p_cashout_multiplier - 1) * p_stake_value;
    ELSE
        v_profit_loss := -p_stake_value;
    END IF;

    v_running_balance := v_prev_balance + v_profit_loss;

    -- Insert round
    INSERT INTO crash_game_rounds (
        bot_id, session_id, game_name, platform_code,
        round_number, round_start_timestamp, round_end_timestamp,
        stake_value, crash_multiplier_detected, cashout_multiplier,
        final_multiplier, round_outcome,
        profit_loss_amount,
        running_balance_before, running_balance_after,
        metadata
    ) VALUES (
        p_bot_id, p_session_id, p_game_name, p_platform_code,
        (SELECT COALESCE(MAX(round_number), 0) + 1
         FROM crash_game_rounds
         WHERE bot_id = p_bot_id AND session_id = p_session_id),
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
        p_stake_value, p_crash_multiplier, p_cashout_multiplier,
        COALESCE(p_cashout_multiplier, p_crash_multiplier), p_outcome,
        v_profit_loss,
        v_prev_balance, v_running_balance,
        p_metadata
    ) RETURNING id INTO v_round_id;

    RETURN v_round_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_bot_vm_registration_update BEFORE UPDATE ON bot_vm_registration
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_crash_game_rounds_update BEFORE UPDATE ON crash_game_rounds
FOR EACH ROW EXECUTE FUNCTION update_timestamp();
