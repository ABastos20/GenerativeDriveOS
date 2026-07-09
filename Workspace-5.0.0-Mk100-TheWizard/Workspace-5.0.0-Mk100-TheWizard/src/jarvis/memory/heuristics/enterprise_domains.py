"""Enterprise and consulting domain mappings.

Covers enterprise architecture, digital transformation, system integration,
cloud platforms, and NTT DATA-specific contexts.
"""

from __future__ import annotations

from typing import Dict

# Keyword-based classification for enterprise & consulting
ENTERPRISE_KEYWORD_MAP: Dict[str, str] = {
    # Enterprise Architecture
    "enterprise architecture": "enterprise.architecture",
    "togaf": "enterprise.architecture",
    "zachman framework": "enterprise.architecture",
    "ea ": "enterprise.architecture",
    "solution architecture": "enterprise.architecture",
    "business architecture": "enterprise.architecture",
    "application architecture": "enterprise.architecture",

    # Consulting & Delivery
    "management consulting": "enterprise.consulting",
    "digital transformation": "enterprise.consulting",
    "business process": "enterprise.consulting",
    "change management": "enterprise.consulting",
    "project management": "enterprise.consulting",
    "agile delivery": "enterprise.consulting",
    "scrum": "enterprise.consulting",
    "safe ": "enterprise.consulting",

    # System Integration
    "system integration": "enterprise.integration",
    "enterprise integration": "enterprise.integration",
    "esb ": "enterprise.integration",
    "enterprise service bus": "enterprise.integration",
    "api gateway": "enterprise.integration",
    "microservices": "enterprise.integration",
    "service mesh": "enterprise.integration",
    "rest api": "enterprise.integration",
    "graphql": "enterprise.integration",

    # Cloud Platforms
    "cloud architecture": "enterprise.cloud",
    "cloud migration": "enterprise.cloud",
    "aws ": "enterprise.cloud",
    "amazon web services": "enterprise.cloud",
    "azure": "enterprise.cloud",
    "microsoft azure": "enterprise.cloud",
    "gcp ": "enterprise.cloud",
    "google cloud platform": "enterprise.cloud",
    "multi-cloud": "enterprise.cloud",
    "hybrid cloud": "enterprise.cloud",
    "cloud native": "enterprise.cloud",
    "kubernetes": "enterprise.cloud",
    "k8s ": "enterprise.cloud",

    # Digital Transformation
    "digital transformation": "enterprise.digital_transformation",
    "digitalization": "enterprise.digital_transformation",
    "digital strategy": "enterprise.digital_transformation",
    "innovation": "enterprise.digital_transformation",
    "disruption": "enterprise.digital_transformation",

    # NTT DATA Specific
    "ntt data": "ntt_data.projects",
    "ntt ": "ntt_data.projects",
    "ntt data emeal": "ntt_data.projects",
    "client project": "ntt_data.projects",
    "delivery framework": "ntt_data.methodologies",
    "ntt methodology": "ntt_data.methodologies",

    # Data & Analytics
    "data warehouse": "enterprise.data",
    "data lake": "enterprise.data",
    "etl ": "enterprise.data",
    "data pipeline": "enterprise.data",
    "business intelligence": "enterprise.data",
    "bi ": "enterprise.data",
    "analytics platform": "enterprise.data",
}
