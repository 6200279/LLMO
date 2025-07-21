-- LLMO Database Schema for Supabase
-- This file contains the complete database schema with RLS policies

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User Profiles Table (extends Supabase auth.users)
-- Supabase automatically creates auth.users table
-- We create a profiles table for additional user data
CREATE TABLE IF NOT EXISTS profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'agency', 'enterprise')),
    scans_remaining INTEGER DEFAULT 1,
    scans_used INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Create policies for profiles table
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Brands Table
CREATE TABLE IF NOT EXISTS brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    keywords TEXT[],
    description TEXT,
    competitors TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_domain CHECK (domain ~* '^https?://.*'),
    CONSTRAINT unique_brand_per_user UNIQUE(user_id, name, domain)
);

-- Enable RLS and create policies for brands
ALTER TABLE brands ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own brands" ON brands
    FOR ALL USING (auth.uid() = user_id);

-- Scans Table
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE NOT NULL,
    scan_type VARCHAR(50) NOT NULL CHECK (scan_type IN ('visibility', 'audit', 'simulation', 'optimization')),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Performance indexes
    INDEX idx_scans_user_id (user_id),
    INDEX idx_scans_brand_id (brand_id),
    INDEX idx_scans_status (status),
    INDEX idx_scans_created (started_at DESC)
);

-- Enable RLS and create policies for scans
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own scans" ON scans
    FOR ALL USING (auth.uid() = user_id);

-- Visibility Results Table
CREATE TABLE IF NOT EXISTS visibility_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE NOT NULL,
    overall_score INTEGER NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    gpt35_score INTEGER CHECK (gpt35_score >= 0 AND gpt35_score <= 100),
    gpt4_score INTEGER CHECK (gpt4_score >= 0 AND gpt4_score <= 100),
    claude_score INTEGER CHECK (claude_score >= 0 AND claude_score <= 100),
    mention_count INTEGER DEFAULT 0,
    competitor_comparison JSONB DEFAULT '{}',
    raw_responses JSONB DEFAULT '{}',
    recommendations JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one result per scan
    CONSTRAINT unique_visibility_result_per_scan UNIQUE(scan_id)
);

-- Audit Results Table
CREATE TABLE IF NOT EXISTS audit_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE NOT NULL,
    overall_score INTEGER NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    schema_score INTEGER CHECK (schema_score >= 0 AND schema_score <= 100),
    meta_score INTEGER CHECK (meta_score >= 0 AND meta_score <= 100),
    content_score INTEGER CHECK (content_score >= 0 AND content_score <= 100),
    technical_score INTEGER CHECK (technical_score >= 0 AND technical_score <= 100),
    recommendations JSONB DEFAULT '[]',
    technical_details JSONB DEFAULT '{}',
    audit_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one result per scan
    CONSTRAINT unique_audit_result_per_scan UNIQUE(scan_id)
);

-- Simulation Results Table
CREATE TABLE IF NOT EXISTS simulation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE NOT NULL,
    prompt_text TEXT NOT NULL,
    response_text TEXT NOT NULL,
    brand_mentioned BOOLEAN DEFAULT FALSE,
    mention_context TEXT,
    sentiment_score DECIMAL(3,2) CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    competitor_mentions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for results tables
ALTER TABLE visibility_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_results ENABLE ROW LEVEL SECURITY;

-- Create policies using joins to ensure users only see their own results
CREATE POLICY "Users can view own visibility results" ON visibility_results
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM scans 
            WHERE scans.id = visibility_results.scan_id 
            AND scans.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own visibility results" ON visibility_results
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM scans 
            WHERE scans.id = visibility_results.scan_id 
            AND scans.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view own audit results" ON audit_results
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM scans 
            WHERE scans.id = audit_results.scan_id 
            AND scans.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own audit results" ON audit_results
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM scans 
            WHERE scans.id = audit_results.scan_id 
            AND scans.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view own simulation results" ON simulation_results
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM scans 
            WHERE scans.id = simulation_results.scan_id 
            AND scans.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own simulation results" ON simulation_results
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM scans 
            WHERE scans.id = simulation_results.scan_id 
            AND scans.user_id = auth.uid()
        )
    );

-- LLM Response Cache Table
CREATE TABLE IF NOT EXISTS llm_response_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    response_data JSONB NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    prompt_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    access_count INTEGER DEFAULT 1,
    
    -- Performance indexes
    INDEX idx_cache_key (cache_key),
    INDEX idx_cache_expires (expires_at),
    INDEX idx_cache_model (model_name),
    INDEX idx_cache_hash (prompt_hash)
);

-- Cache table doesn't need RLS as it's system-wide

-- Create function to update scan progress (for real-time updates)
CREATE OR REPLACE FUNCTION update_scan_progress()
RETURNS TRIGGER AS $$
BEGIN
    -- Notify Supabase Realtime subscribers
    PERFORM pg_notify('scan_progress', json_build_object(
        'scan_id', NEW.id,
        'progress', NEW.progress,
        'status', NEW.status,
        'user_id', NEW.user_id
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for scan progress updates
DROP TRIGGER IF EXISTS scan_progress_trigger ON scans;
CREATE TRIGGER scan_progress_trigger
    AFTER UPDATE ON scans
    FOR EACH ROW
    WHEN (OLD.progress IS DISTINCT FROM NEW.progress OR OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION update_scan_progress();

-- Function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM llm_response_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at columns
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_brands_updated_at BEFORE UPDATE ON brands
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to handle new user registration
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (id, first_name, last_name)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'first_name', ''),
        COALESCE(NEW.raw_user_meta_data->>'last_name', '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new user registration
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_brands_user_id ON brands(user_id);
CREATE INDEX IF NOT EXISTS idx_brands_domain ON brands(domain);
CREATE INDEX IF NOT EXISTS idx_scans_user_status ON scans(user_id, status);
CREATE INDEX IF NOT EXISTS idx_scans_brand_created ON scans(brand_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_visibility_results_scan_id ON visibility_results(scan_id);
CREATE INDEX IF NOT EXISTS idx_audit_results_scan_id ON audit_results(scan_id);
CREATE INDEX IF NOT EXISTS idx_simulation_results_scan_id ON simulation_results(scan_id);

-- Create view for scan summaries (useful for dashboard)
CREATE OR REPLACE VIEW scan_summaries AS
SELECT 
    s.id,
    s.user_id,
    s.brand_id,
    b.name as brand_name,
    b.domain,
    s.scan_type,
    s.status,
    s.progress,
    s.started_at,
    s.completed_at,
    CASE 
        WHEN s.scan_type = 'visibility' THEN vr.overall_score
        WHEN s.scan_type = 'audit' THEN ar.overall_score
        ELSE NULL
    END as overall_score,
    s.metadata
FROM scans s
LEFT JOIN brands b ON s.brand_id = b.id
LEFT JOIN visibility_results vr ON s.id = vr.scan_id
LEFT JOIN audit_results ar ON s.id = ar.scan_id;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;