from _typeshed import Incomplete
from datetime import datetime
from pydantic import BaseModel, UUID4 as UUID4

CLOUD_ENVS: Incomplete

class HQStageProfile(BaseModel):
    """HQStageProfile pydantic model."""
    token_id: str
    token: str
    cloud_environment: CLOUD_ENVS

class HQStageOptions(BaseModel):
    """HQStageOptions pydantic model."""
    auto_checkout: bool
    advanced_mode: bool
    offline_license: bool

class HQStageConfig(BaseModel):
    """HQStageConfig pydantic model."""
    profile: HQStageProfile
    options: HQStageOptions

class HQStageEntitlement(BaseModel):
    """HQStageEntitlement pydantic model."""
    name: str
    code: str
    packages: list[str]
    required_entitlements: list[str]

class HQStagePackage(BaseModel):
    """HQStagePackage pydantic model."""
    key: str
    installed_version: str | None
    available_versions: list[str]
    def needs_update(self) -> bool:
        """Check if package needs update."""
    def max_version(self) -> str | None:
        """Get maximum available version."""

class HQSLicenseFile(BaseModel):
    """A license file."""
    id: UUID4
    certificate: str
    includes: list[str]
    ttl: int
    expiry: datetime
    issued: datetime
