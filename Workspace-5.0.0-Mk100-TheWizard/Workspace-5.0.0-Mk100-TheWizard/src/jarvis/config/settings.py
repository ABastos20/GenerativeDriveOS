from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# --- Models -----------------------------------------------------------------


@dataclass
class ProviderConfig:
    name: str
    type: str
    priority: int
    model: Optional[str] = None
    api_key_env: Optional[str] = None

    def api_key(self) -> Optional[str]:
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return None


@dataclass
class DocsConfig:
    root: Path = Path("docs")

    def get_jarvis_docs_dir(self) -> Path:
        return (self.root / "jarvis").resolve()


@dataclass
class WorkspaceConfig:
    root: Path = Path("/workspace")
    private_dir: str = ".jarvis"

    def private_path(self) -> Path:
        return (self.root / self.private_dir).resolve()


@dataclass
class QueryConfig:
    default_retriever: str = "semantic"
    default_weight: float = 0.7
    default_strict_mode: bool = False
    enable_expansion: bool = False
    expansion_count: int = 2
    default_grounding_level: str = "balanced"


@dataclass
class ResearchConfig:
    max_queries: int = 3
    min_queries: int = 2
    provider: str = "gemini"
    hourly_limit: int = 10
    cost_cap_usd: float = 2.0
    redis_url: Optional[str] = None


@dataclass
class IdentityConfig:
    enabled: bool = True
    provider: str = "keycloak"
    url: str = "http://keycloak:8080"
    realm: str = "jarvis"
    client_id: str = "jarvis-api"
    
    @property
    def jwks_url(self) -> str:
        return f"{self.url}/realms/{self.realm}/protocol/openid-connect/certs"



@dataclass
class Settings:
    project_name: str
    environment: str
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    docs: DocsConfig = field(default_factory=DocsConfig)
    providers: List[ProviderConfig] = field(default_factory=list)
    query: QueryConfig = field(default_factory=QueryConfig)
    research: ResearchConfig = field(default_factory=ResearchConfig)
    identity: IdentityConfig = field(default_factory=IdentityConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        project = data.get("project", {})
        workspace_data = data.get("workspace", {})
        workspace = WorkspaceConfig(
            root=Path(os.environ.get("WORKSPACE_ROOT", workspace_data.get("root", "/workspace"))),
            private_dir=os.environ.get(
                "WORKSPACE_PRIVATE_DIR", workspace_data.get("private_dir", ".jarvis")
            ),
        )
        docs_data = data.get("docs", {})
        docs = DocsConfig(
            root=Path(os.environ.get("DOCS_ROOT", docs_data.get("root", "docs"))),
        )
        query_data = data.get("query", {})
        default_retriever = query_data.get("default_retriever", "semantic")
        default_weight_raw = query_data.get("default_weight", 0.7)
        default_strict_mode_raw = query_data.get("default_strict_mode", False)
        enable_expansion_raw = query_data.get("enable_expansion", False)
        expansion_count_raw = query_data.get("expansion_count", 2)
        default_grounding_level_raw = query_data.get("default_grounding_level", "balanced")

        # Grounding level can be overridden by env var
        default_grounding_level = os.environ.get(
            "JARVIS_GROUNDING_LEVEL", default_grounding_level_raw
        ).lower()
        if default_grounding_level not in {"soft", "balanced", "strict"}:
            default_grounding_level = "balanced"

        try:
            default_weight = float(default_weight_raw)
        except (TypeError, ValueError):
            default_weight = 0.7
        if default_weight < 0.0 or default_weight > 1.0:
            default_weight = 0.7

        default_strict_mode = bool(default_strict_mode_raw)
        enable_expansion = bool(enable_expansion_raw)

        try:
            expansion_count = int(expansion_count_raw)
        except (TypeError, ValueError):
            expansion_count = 2
        # Clamp expansion_count to valid range [0, 5]
        expansion_count = max(0, min(expansion_count, 5))

        query = QueryConfig(
            default_retriever=str(default_retriever),
            default_weight=default_weight,
            default_strict_mode=default_strict_mode,
            enable_expansion=enable_expansion,
            expansion_count=expansion_count,
            default_grounding_level=default_grounding_level,
        )

        research_data = data.get("research", {})
        research = ResearchConfig(
            max_queries=int(research_data.get("max_queries", 3)),
            min_queries=int(research_data.get("min_queries", 2)),
            provider=str(research_data.get("provider", "gemini")),
            hourly_limit=int(research_data.get("hourly_limit", 10)),
            cost_cap_usd=float(research_data.get("cost_cap_usd", 2.0)),
            redis_url=research_data.get("redis_url"),
        )
        
        identity_data = data.get("identity", {})
        identity = IdentityConfig(
            enabled=bool(identity_data.get("enabled", True)),
            provider=str(identity_data.get("provider", "keycloak")),
            url=os.environ.get("KEYCLOAK_URL", identity_data.get("url", "http://keycloak:8080")),
            realm=os.environ.get("KEYCLOAK_REALM", identity_data.get("realm", "jarvis")),
        )

        providers = [
            ProviderConfig(
                name=provider["name"],
                type=provider.get("type", "free_tier"),
                priority=int(provider.get("priority", 1)),
                model=provider.get("model"),
                api_key_env=provider.get("api_key_env"),
            )
            for provider in data.get("providers", [])
        ]
        return cls(
            project_name=project.get("name", "AI Advisor"),
            environment=project.get("environment", "development"),
            workspace=workspace,
            docs=docs,
            providers=providers,
            query=query,
            research=research,
            identity=identity,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "environment": self.environment,
            "workspace": {
                "root": str(self.workspace.root),
                "private_dir": self.workspace.private_dir,
            },
            "docs": {
                "root": str(self.docs.root),
            },
            "query": {
                "default_retriever": self.query.default_retriever,
                "default_weight": self.query.default_weight,
                "default_strict_mode": self.query.default_strict_mode,
                "enable_expansion": self.query.enable_expansion,
                "expansion_count": self.query.expansion_count,
                "default_grounding_level": self.query.default_grounding_level,
            },
            "research": {
                "max_queries": self.research.max_queries,
                "min_queries": self.research.min_queries,
                "provider": self.research.provider,
                "hourly_limit": self.research.hourly_limit,
                "cost_cap_usd": self.research.cost_cap_usd,
                "redis_url": self.research.redis_url,
            },
            "identity": {
                "enabled": self.identity.enabled,
                "provider": self.identity.provider,
                "url": self.identity.url,
                "realm": self.identity.realm,
                "jwks_url": self.identity.jwks_url,
            },
            "providers": [
                {
                    "name": provider.name,
                    "type": provider.type,
                    "priority": provider.priority,
                    "model": provider.model,
                    "api_key_env": provider.api_key_env,
                }
                for provider in self.providers
            ],
        }


# --- Loading helpers --------------------------------------------------------


def _load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _load_json_like(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - configuration error
        raise ValueError(f"Invalid JSON/YAML structure in {path}: {exc}") from exc


def load_settings(
    config_path: Path = Path("config/settings.yaml"),
    dotenv_path: Path = Path(".env"),
) -> Settings:
    """
    Load settings from config/settings.yaml (JSON-compatible YAML) and optional .env.
    Falls back to settings.example.yaml if the primary file is absent.
    """

    _load_dotenv(dotenv_path)

    path = config_path
    if not path.exists():
        example = config_path.with_name("settings.example.yaml")
        if not example.exists():
            raise FileNotFoundError(f"Unable to locate configuration file at {config_path}")
        path = example

    data = _load_json_like(path)
    return Settings.from_dict(data)
