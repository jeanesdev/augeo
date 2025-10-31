"""Pydantic schemas package."""

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RefreshResponse,
    UserCreate,
    UserPublic,
    UserRegisterResponse,
)
from app.schemas.consent import (
    ConsentAcceptRequest,
    ConsentAuditLogResponse,
    ConsentHistoryResponse,
    ConsentResponse,
    ConsentStatusResponse,
    DataDeletionRequest,
    DataExportRequest,
)
from app.schemas.cookies import (
    CookieConsentRequest,
    CookieConsentResponse,
    CookieConsentStatusResponse,
    CookieConsentUpdateRequest,
)
from app.schemas.legal_documents import (
    LegalDocumentCreateRequest,
    LegalDocumentListResponse,
    LegalDocumentPublicResponse,
    LegalDocumentResponse,
    LegalDocumentUpdateRequest,
)

__all__ = [
    # Auth
    "LoginRequest",
    "LoginResponse",
    "LogoutRequest",
    "MessageResponse",
    "RefreshRequest",
    "RefreshResponse",
    "UserCreate",
    "UserPublic",
    "UserRegisterResponse",
    # Consent
    "ConsentAcceptRequest",
    "ConsentAuditLogResponse",
    "ConsentHistoryResponse",
    "ConsentResponse",
    "ConsentStatusResponse",
    "DataDeletionRequest",
    "DataExportRequest",
    # Cookies
    "CookieConsentRequest",
    "CookieConsentResponse",
    "CookieConsentStatusResponse",
    "CookieConsentUpdateRequest",
    # Legal Documents
    "LegalDocumentCreateRequest",
    "LegalDocumentListResponse",
    "LegalDocumentPublicResponse",
    "LegalDocumentResponse",
    "LegalDocumentUpdateRequest",
]
