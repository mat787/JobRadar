CREATE TABLE IF NOT EXISTS offers (
    id                     TEXT PRIMARY KEY,
    title                  TEXT NOT NULL,
    company                TEXT,
    salary                 TEXT,
    url                    TEXT,
    technologies           TEXT[] NOT NULL DEFAULT '{}',
    levels                 TEXT[] NOT NULL DEFAULT '{}',
    contracts              TEXT[] NOT NULL DEFAULT '{}',
    work_modes             TEXT[] NOT NULL DEFAULT '{}',
    work_schedules         TEXT[] NOT NULL DEFAULT '{}',
    locations              TEXT[] NOT NULL DEFAULT '{}',
    published_at           TIMESTAMPTZ,
    expires_at             TIMESTAMPTZ,
    description            TEXT,
    about_project          TEXT,
    about_company          TEXT,
    team_size              TEXT,
    responsibilities       TEXT[] NOT NULL DEFAULT '{}',
    requirements           TEXT[] NOT NULL DEFAULT '{}',
    nice_to_have           TEXT[] NOT NULL DEFAULT '{}',
    technologies_optional  TEXT[] NOT NULL DEFAULT '{}',
    offered                TEXT[] NOT NULL DEFAULT '{}',
    benefits               TEXT[] NOT NULL DEFAULT '{}',
    training               TEXT[] NOT NULL DEFAULT '{}',
    development_practices  TEXT[] NOT NULL DEFAULT '{}',
    work_style             TEXT[] NOT NULL DEFAULT '{}',
    recruitment_stages     TEXT[] NOT NULL DEFAULT '{}',
    details_fetched_at     TIMESTAMPTZ,
    first_seen             TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen              TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE offers ADD COLUMN IF NOT EXISTS work_modes             TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS work_schedules         TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS locations              TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS published_at           TIMESTAMPTZ;
ALTER TABLE offers ADD COLUMN IF NOT EXISTS expires_at             TIMESTAMPTZ;
ALTER TABLE offers ADD COLUMN IF NOT EXISTS about_project          TEXT;
ALTER TABLE offers ADD COLUMN IF NOT EXISTS about_company          TEXT;
ALTER TABLE offers ADD COLUMN IF NOT EXISTS team_size              TEXT;
ALTER TABLE offers ADD COLUMN IF NOT EXISTS responsibilities       TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS requirements           TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS nice_to_have           TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS technologies_optional  TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS offered                TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS benefits               TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS training               TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS development_practices  TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS work_style             TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS recruitment_stages     TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS details_fetched_at     TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_offers_technologies ON offers USING GIN (technologies);
CREATE INDEX IF NOT EXISTS idx_offers_expires_at ON offers (expires_at);
