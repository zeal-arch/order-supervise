-- ==============================================
-- Order Supervisor Database Schema
-- ==============================================

-- 1. Supervisor Templates
CREATE TABLE IF NOT EXISTS supervisors (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_instruction TEXT NOT NULL,
    available_tools JSONB NOT NULL DEFAULT '[]'::jsonb,
    default_wake_delay_seconds INTEGER NOT NULL DEFAULT 3600,
    wake_sensitivity VARCHAR(32) NOT NULL DEFAULT 'balanced',
    model_name VARCHAR(64) DEFAULT 'gpt-4o-mini',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Order Supervisor Runs
CREATE TABLE IF NOT EXISTS runs (
    id VARCHAR(64) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    supervisor_id VARCHAR(64) REFERENCES supervisors(id),
    workflow_id VARCHAR(128) NOT NULL UNIQUE,
    run_id VARCHAR(128),
    status VARCHAR(32) NOT NULL DEFAULT 'INITIALIZING',
    order_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    current_memory JSONB NOT NULL DEFAULT '{}'::jsonb,
    additional_instructions JSONB NOT NULL DEFAULT '[]'::jsonb,
    next_wake_at TIMESTAMP WITH TIME ZONE,
    last_wake_reason VARCHAR(64),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    final_output JSONB
);

-- 3. Events Timeline
CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(64) PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    source VARCHAR(64) NOT NULL DEFAULT 'simulator',
    requires_wake BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Agent Activities (Tools executed)
CREATE TABLE IF NOT EXISTS activities (
    id VARCHAR(64) PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    activity_type VARCHAR(64) NOT NULL,
    reasoning TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'SUCCESS',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for rapid lookup
CREATE INDEX IF NOT EXISTS idx_runs_order_id ON runs(order_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_activities_run_id ON activities(run_id);
CREATE INDEX IF NOT EXISTS idx_activities_created_at ON activities(created_at);
