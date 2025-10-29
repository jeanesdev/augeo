# Data Model: Legal Documentation & Compliance

**Feature**: 005-legal-documentation
**Date**: 2025-10-28
**Status**: Design Phase

## Entity Relationship Diagram

```text
┌─────────────────────────┐
│   LegalDocument         │
├─────────────────────────┤
│ id (UUID, PK)           │
│ document_type (ENUM)    │◄─────┐
│ version (VARCHAR)       │      │
│ content (TEXT)          │      │ References
│ status (ENUM)           │      │ version
│ effective_date (DATE)   │      │
│ created_at (TIMESTAMP)  │      │
│ updated_at (TIMESTAMP)  │      │
└─────────────────────────┘      │
                                 │
┌─────────────────────────┐      │
│   UserConsent           │      │
├─────────────────────────┤      │
│ id (UUID, PK)           │      │
│ user_id (UUID, FK)      │──────┼──────► users.id
│ document_type (ENUM)    │      │
│ document_version (FK)   │──────┘
│ accepted_at (TIMESTAMP) │
│ ip_address (INET)       │
│ user_agent (TEXT)       │
│ consent_method (ENUM)   │
│ created_at (TIMESTAMP)  │
└─────────────────────────┘
         │
         │ Triggers audit log entry
         ▼
┌─────────────────────────┐
│  ConsentAuditLog        │
├─────────────────────────┤
│ id (UUID, PK)           │
│ user_id (UUID, FK)      │──────► users.id
│ event_type (ENUM)       │
│ document_type (ENUM)    │
│ document_version (STR)  │
│ timestamp (TIMESTAMP)   │
│ ip_address (INET)       │
│ user_agent (TEXT)       │
│ metadata (JSONB)        │
└─────────────────────────┘

┌─────────────────────────┐
│   CookieConsent         │
├─────────────────────────┤
│ id (UUID, PK)           │
│ user_id (UUID, FK, NULL)│──────► users.id (nullable for anonymous)
│ session_id (VARCHAR)    │       (anonymous pre-registration)
│ essential_cookies (BOOL)│
│ analytics_cookies (BOOL)│
│ marketing_cookies (BOOL)│
│ consent_timestamp (TS)  │
│ expires_at (TIMESTAMP)  │
│ created_at (TIMESTAMP)  │
│ updated_at (TIMESTAMP)  │
└─────────────────────────┘
```

## Table Definitions

### 1. legal_documents

**Purpose**: Store versioned Terms of Service and Privacy Policy documents

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| document_type | ENUM('terms_of_service', 'privacy_policy') | NOT NULL | Type of legal document |
| version | VARCHAR(20) | NOT NULL | Semantic version (e.g., "1.0", "2.1") |
| content | TEXT | NOT NULL | Full document content (Markdown) |
| status | ENUM('draft', 'published', 'archived') | NOT NULL DEFAULT 'draft' | Document lifecycle status |
| effective_date | DATE | NOT NULL | When this version takes effect |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Last update timestamp |

**Indexes**:

- `idx_legal_documents_type_version` UNIQUE (document_type, version)
- `idx_legal_documents_status` (status)
- `idx_legal_documents_effective_date` (effective_date)

**Constraints**:

- UNIQUE (document_type, version) - prevent duplicate versions
- CHECK (status IN ('draft', 'published', 'archived'))
- CHECK (version ~ '^[0-9]+\.[0-9]+$') - enforce semantic versioning format

**Business Rules**:

- Published versions are immutable (enforced in application logic)
- Only one published version per document_type at a time
- Archiving old version required before publishing new version
- Major version bump (1.x → 2.x) triggers re-acceptance requirement

---

### 2. user_consents

**Purpose**: Track user acceptance of specific legal document versions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| user_id | UUID | FOREIGN KEY → users.id, NOT NULL | User who gave consent |
| document_type | ENUM('terms_of_service', 'privacy_policy') | NOT NULL | Which document was accepted |
| document_version | VARCHAR(20) | NOT NULL | Version accepted (e.g., "1.0") |
| accepted_at | TIMESTAMP | NOT NULL DEFAULT NOW() | When consent was given |
| ip_address | INET | NULL | IP address at consent time |
| user_agent | TEXT | NULL | Browser/device info at consent time |
| consent_method | ENUM('registration', 'update_prompt', 'settings') | NOT NULL | How consent was obtained |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Record creation timestamp |

**Indexes**:

- `idx_user_consents_user_id` (user_id)
- `idx_user_consents_user_document` (user_id, document_type) - find latest consent per user
- `idx_user_consents_accepted_at` (accepted_at)

**Constraints**:

- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
- CHECK (consent_method IN ('registration', 'update_prompt', 'settings'))

**Business Rules**:

- Each (user_id, document_type) can have multiple rows (version history)
- Latest row per (user_id, document_type) represents current consent status
- Cannot delete rows (audit requirement) - only insert new versions
- All consents logged to consent_audit_log on insert

---

### 3. cookie_consents

**Purpose**: Store user cookie preferences with support for anonymous users

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| user_id | UUID | FOREIGN KEY → users.id, NULL | Authenticated user (NULL for anonymous) |
| session_id | VARCHAR(255) | NULL | Anonymous session identifier (UUID in localStorage) |
| essential_cookies | BOOLEAN | NOT NULL DEFAULT TRUE | Essential cookies always allowed |
| analytics_cookies | BOOLEAN | NOT NULL DEFAULT FALSE | Google Analytics, etc. |
| marketing_cookies | BOOLEAN | NOT NULL DEFAULT FALSE | Facebook Pixel, LinkedIn, etc. |
| consent_timestamp | TIMESTAMP | NOT NULL DEFAULT NOW() | When preferences were set |
| expires_at | TIMESTAMP | NOT NULL | Consent expiry (12 months from consent) |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Last update timestamp |

**Indexes**:

- `idx_cookie_consents_user_id` (user_id) WHERE user_id IS NOT NULL
- `idx_cookie_consents_session_id` (session_id) WHERE session_id IS NOT NULL
- `idx_cookie_consents_expires_at` (expires_at) - cleanup expired consents

**Constraints**:

- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
- CHECK (user_id IS NOT NULL OR session_id IS NOT NULL) - must have one identifier
- CHECK (expires_at > consent_timestamp)

**Business Rules**:

- Essential cookies (session, CSRF) always TRUE (cannot be disabled)
- Anonymous users identified by session_id (UUID in browser localStorage)
- On registration/login, merge anonymous consent to user_id and delete session_id record
- Expired consents (expires_at < NOW()) default to reject all non-essential
- One active record per user_id or session_id (upsert on preference change)

---

### 4. consent_audit_logs

**Purpose**: Immutable audit trail of all consent events for regulatory compliance

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| user_id | UUID | FOREIGN KEY → users.id, NULL | User involved (NULL if anonymous at time) |
| event_type | ENUM('accept', 'withdraw', 'update', 'expire') | NOT NULL | Type of consent event |
| document_type | ENUM('terms_of_service', 'privacy_policy', 'cookie_consent') | NOT NULL | What was consented to |
| document_version | VARCHAR(20) | NULL | Version if applicable (NULL for cookies) |
| timestamp | TIMESTAMP | NOT NULL DEFAULT NOW() | When event occurred |
| ip_address | INET | NULL | IP address at event time |
| user_agent | TEXT | NULL | Browser/device info |
| metadata | JSONB | NULL | Additional context (referrer, session_id, etc.) |

**Indexes**:

- `idx_consent_audit_user_id` (user_id) WHERE user_id IS NOT NULL
- `idx_consent_audit_timestamp` (timestamp DESC) - recent events first
- `idx_consent_audit_document_type` (document_type)
- `idx_consent_audit_metadata` GIN (metadata) - JSONB indexing

**Constraints**:

- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL (preserve audit even if user deleted)
- CHECK (event_type IN ('accept', 'withdraw', 'update', 'expire'))
- **IMMUTABLE**: No updates or deletes allowed (enforced by database trigger)

**Business Rules**:

- Append-only table (inserts only)
- Database trigger prevents UPDATE and DELETE operations
- Retention: Minimum 7 years for regulatory compliance
- Even deleted users' logs retained (user_id SET NULL, but metadata preserves anonymized identifier)
- JSONB metadata examples: `{"session_id": "...", "referrer": "...", "consent_details": {...}}`

---

## Validation Rules

### LegalDocument Validation

```python
class LegalDocumentCreate(BaseModel):
    document_type: Literal["terms_of_service", "privacy_policy"]
    version: str  # Must match regex: ^\d+\.\d+$
    content: str  # Min 100 chars, max 100,000 chars
    effective_date: date  # Cannot be in past (except admin override)

    @validator("version")
    def validate_version_format(cls, v):
        if not re.match(r'^\d+\.\d+$', v):
            raise ValueError("Version must be in format 'X.Y' (e.g., '1.0', '2.5')")
        return v

    @validator("content")
    def validate_content_length(cls, v):
        if len(v) < 100:
            raise ValueError("Legal document must be at least 100 characters")
        if len(v) > 100000:
            raise ValueError("Legal document cannot exceed 100,000 characters")
        return v
```

### UserConsent Validation

```python
class UserConsentCreate(BaseModel):
    document_type: Literal["terms_of_service", "privacy_policy"]
    document_version: str
    consent_method: Literal["registration", "update_prompt", "settings"]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    @validator("document_version")
    def validate_version_exists(cls, v, values):
        # Must reference existing published document version
        # Validated in service layer against legal_documents table
        return v
```

### CookieConsent Validation

```python
class CookieConsentUpdate(BaseModel):
    essential_cookies: bool = True  # Always true, cannot be disabled
    analytics_cookies: bool = False
    marketing_cookies: bool = False

    @validator("essential_cookies")
    def essential_must_be_true(cls, v):
        if not v:
            raise ValueError("Essential cookies cannot be disabled")
        return v
```

---

## State Transitions

### Legal Document Lifecycle

```text
┌───────┐
│ draft │ ──────┐
└───────┘       │
      │         │ (can edit)
      │         │
      ▼         │
┌───────────┐  │
│ published │  │ (immutable)
└───────────┘  │
      │         │
      │         │ (new version published)
      ▼         │
┌──────────┐   │
│ archived │ ◄─┘
└──────────┘
```

**Transitions**:

- draft → published: Admin publishes version (becomes active)
- published → archived: New version published, old version archived
- draft → deleted: Admin discards draft (never published)

**Rules**:

- Cannot edit published or archived documents
- Cannot have multiple published versions of same document_type
- Archiving old version required before publishing new major version

### User Consent Lifecycle

```text
┌──────────────┐
│ No consent   │
└──────────────┘
      │
      │ User accepts TOS/Privacy
      ▼
┌──────────────┐
│ Consented    │ ◄──┐
│ (v1.0)       │    │ User accepts updated version
└──────────────┘    │
      │             │
      │ New version published (major bump)
      ▼             │
┌──────────────┐    │
│ Outdated     │ ───┘
│ (v1.0 active,│
│  v2.0 needed)│
└──────────────┘
      │
      │ User logs out / deactivated if not accepted
      ▼
┌──────────────┐
│ Blocked      │
└──────────────┘
```

**Transitions**:

- No consent → Consented: User accepts during registration
- Consented → Outdated: Major version published, user's version < current
- Outdated → Consented: User accepts updated version
- Outdated → Blocked: User attempts to use app without accepting (409 Conflict)

---

## Relationships

### Foreign Keys

- `user_consents.user_id` → `users.id` (CASCADE delete - if user deleted, remove consents)
- `cookie_consents.user_id` → `users.id` (CASCADE delete)
- `consent_audit_logs.user_id` → `users.id` (SET NULL - preserve log even if user deleted)

### Logical Relationships (not enforced by FK)

- `user_consents.document_version` references `legal_documents.version`
  - Not a FK because documents can be archived but consents remain valid
  - Enforced in application logic

---

## Migration Strategy

### Alembic Migration Script Structure

```python
"""Add legal compliance tables

Revision ID: [timestamp]_add_legal_compliance
Revises: [previous_revision]
Create Date: 2025-10-28
"""

def upgrade():
    # 1. Create ENUM types
    sa.Enum('terms_of_service', 'privacy_policy', name='document_type').create(op.get_bind())
    sa.Enum('draft', 'published', 'archived', name='document_status').create(op.get_bind())
    sa.Enum('registration', 'update_prompt', 'settings', name='consent_method').create(op.get_bind())
    sa.Enum('accept', 'withdraw', 'update', 'expire', name='consent_event_type').create(op.get_bind())

    # 2. Create legal_documents table
    op.create_table('legal_documents', ...)

    # 3. Create user_consents table
    op.create_table('user_consents', ...)

    # 4. Create cookie_consents table
    op.create_table('cookie_consents', ...)

    # 5. Create consent_audit_logs table
    op.create_table('consent_audit_logs', ...)

    # 6. Create indexes
    op.create_index(...)

    # 7. Create trigger to prevent audit log modifications
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are immutable';
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER immutable_audit_log
        BEFORE UPDATE OR DELETE ON consent_audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();
    """)

    # 8. Seed initial legal documents (draft versions)
    op.execute("""
        INSERT INTO legal_documents (id, document_type, version, content, status, effective_date)
        VALUES
        (gen_random_uuid(), 'terms_of_service', '1.0', 'DRAFT: Terms of Service...', 'draft', CURRENT_DATE),
        (gen_random_uuid(), 'privacy_policy', '1.0', 'DRAFT: Privacy Policy...', 'draft', CURRENT_DATE);
    """)

def downgrade():
    # Drop in reverse order
    op.drop_table('consent_audit_logs')
    op.drop_table('cookie_consents')
    op.drop_table('user_consents')
    op.drop_table('legal_documents')
    sa.Enum(name='consent_event_type').drop(op.get_bind())
    sa.Enum(name='consent_method').drop(op.get_bind())
    sa.Enum(name='document_status').drop(op.get_bind())
    sa.Enum(name='document_type').drop(op.get_bind())
```

---

## Data Retention & Archival

### Retention Policies

| Table | Retention Period | Archival Strategy |
|-------|------------------|-------------------|
| legal_documents | Indefinite | Keep all versions (disk space minimal) |
| user_consents | Indefinite | Keep all consent history (audit requirement) |
| cookie_consents | 12 months after expiry | Delete expired consents after 1 year |
| consent_audit_logs | 7 years minimum | Partition by year, archive to cold storage |

### Cleanup Jobs

**Expired Cookie Consents** (Daily cron):

```sql
DELETE FROM cookie_consents
WHERE expires_at < NOW() - INTERVAL '1 year';
```

**Audit Log Archival** (Annually):

```sql
-- Partition audit logs older than 3 years to separate tablespace
-- Archive logs older than 7 years to Azure Blob Storage (cold storage)
```

---

## Example Queries

### Check if user needs to accept updated terms

```sql
SELECT
    ld.document_type,
    ld.version AS current_version,
    uc.document_version AS user_version,
    CASE
        WHEN split_part(ld.version, '.', 1)::int > split_part(uc.document_version, '.', 1)::int
        THEN true
        ELSE false
    END AS needs_acceptance
FROM legal_documents ld
LEFT JOIN LATERAL (
    SELECT document_version
    FROM user_consents
    WHERE user_id = :user_id
      AND document_type = ld.document_type
    ORDER BY accepted_at DESC
    LIMIT 1
) uc ON true
WHERE ld.status = 'published';
```

### Get user's consent history

```sql
SELECT
    document_type,
    document_version,
    accepted_at,
    consent_method
FROM user_consents
WHERE user_id = :user_id
ORDER BY accepted_at DESC;
```

### Get active cookie consent for user

```sql
SELECT
    essential_cookies,
    analytics_cookies,
    marketing_cookies,
    expires_at
FROM cookie_consents
WHERE user_id = :user_id
  AND expires_at > NOW()
ORDER BY consent_timestamp DESC
LIMIT 1;
```

---

## SQLAlchemy Model Relationships

```python
# models/legal_document.py
class LegalDocument(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "legal_documents"

    document_type = Column(Enum(DocumentType), nullable=False)
    version = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.DRAFT)
    effective_date = Column(Date, nullable=False)

    __table_args__ = (
        UniqueConstraint('document_type', 'version'),
        Index('idx_legal_documents_type_version', 'document_type', 'version', unique=True),
    )

# models/user_consent.py
class UserConsent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_consents"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    document_version = Column(String(20), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    consent_method = Column(Enum(ConsentMethod), nullable=False)

    # Relationships
    user = relationship("User", back_populates="consents")

    __table_args__ = (
        Index('idx_user_consents_user_document', 'user_id', 'document_type'),
    )
```
