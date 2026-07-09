"""Development and infrastructure domain mappings.

Covers software development frameworks, infrastructure tools, databases,
containers, orchestration, and DevOps tooling.

This includes domains from the original CHAVAO_DOMAIN_MAP related to dev/infra.
"""

from __future__ import annotations

from typing import Dict

# Keyword-based classification for development & infrastructure
DEV_INFRA_KEYWORD_MAP: Dict[str, str] = {
    # Development Frameworks (from old CHAVAO_DOMAIN_MAP)
    "spring boot": "dev.spring_boot",
    "spring framework": "dev.spring_boot",
    "django": "dev.python",
    "flask": "dev.python",
    "fastapi": "dev.python",
    "react": "dev.frontend",
    "vue": "dev.frontend",
    "angular": "dev.frontend",
    "nodejs": "dev.nodejs",
    "node.js": "dev.nodejs",

    # Container & Orchestration (from old CHAVAO_DOMAIN_MAP)
    "docker": "infra.docker",
    "docker compose": "infra.docker",
    "docker-compose": "infra.docker",
    "kubernetes": "infra.kubernetes",
    "k8s": "infra.kubernetes",
    "helm": "infra.kubernetes",
    "container": "infra.docker",

    # Databases (from old CHAVAO_DOMAIN_MAP)
    "postgresql": "infra.postgres",
    "postgres ": "infra.postgres",
    "mysql": "infra.sql",
    "mariadb": "infra.sql",
    "sqlite": "infra.sql",
    "mongodb": "infra.nosql",
    "redis": "infra.redis",
    "cassandra": "infra.nosql",

    # Vector Databases (from old CHAVAO_DOMAIN_MAP)
    "qdrant": "infra.qdrant",
    "pinecone": "infra.vector_db",
    "weaviate": "infra.vector_db",
    "milvus": "infra.vector_db",
    "vector database": "infra.vector_db",

    # Message Queues & Streaming
    "kafka": "infra.messaging",
    "rabbitmq": "infra.messaging",
    "message queue": "infra.messaging",
    "pubsub": "infra.messaging",
    "redis stream": "infra.messaging",

    # CI/CD & DevOps
    "ci/cd": "infra.cicd",
    "continuous integration": "infra.cicd",
    "continuous deployment": "infra.cicd",
    "github actions": "infra.cicd",
    "gitlab ci": "infra.cicd",
    "jenkins": "infra.cicd",
    "terraform": "infra.iac",
    "ansible": "infra.iac",
    "infrastructure as code": "infra.iac",

    # Monitoring & Observability
    "prometheus": "infra.monitoring",
    "grafana": "infra.monitoring",
    "datadog": "infra.monitoring",
    "new relic": "infra.monitoring",
    "elk stack": "infra.monitoring",
    "elasticsearch": "infra.monitoring",
    "kibana": "infra.monitoring",
    "logstash": "infra.monitoring",

    # Web Servers & Proxies
    "nginx": "infra.webserver",
    "apache": "infra.webserver",
    "haproxy": "infra.proxy",
    "envoy": "infra.proxy",
    "traefik": "infra.proxy",

    # Programming Languages
    "python": "dev.python",
    "java": "dev.java",
    "javascript": "dev.javascript",
    "typescript": "dev.typescript",
    "golang": "dev.go",
    " go ": "dev.go",
    "rust": "dev.rust",
    "c++": "dev.cpp",
}
