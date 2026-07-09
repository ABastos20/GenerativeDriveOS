"""Banking, finance, and economics domain mappings.

Covers financial systems, banking infrastructure, trading, risk management,
regulatory compliance, blockchain, and economic theory.
"""

from __future__ import annotations

from typing import Dict

# Keyword-based classification for finance & economics
FINANCE_KEYWORD_MAP: Dict[str, str] = {
    # Banking Systems
    "core banking": "finance.banking",
    "banking system": "finance.banking",
    "retail banking": "finance.banking",
    "investment banking": "finance.banking",
    "private banking": "finance.banking",
    "commercial bank": "finance.banking",
    "central bank": "finance.banking",
    "banco central": "finance.banking",
    "banco de portugal": "finance.banking",
    "european central bank": "finance.banking",
    "ecb ": "finance.banking",
    "bce ": "finance.banking",

    # Payment Systems
    "payment system": "finance.payments",
    "payment processing": "finance.payments",
    "swift ": "finance.payments",
    "sepa ": "finance.payments",
    "clearing house": "finance.payments",
    "settlement system": "finance.payments",
    "real-time payments": "finance.payments",
    "instant payments": "finance.payments",
    "card processing": "finance.payments",
    "merchant acquiring": "finance.payments",
    "pagamento": "finance.payments",

    # Trading & Markets
    "trading system": "finance.trading",
    "algorithmic trading": "finance.trading",
    "high frequency trading": "finance.trading",
    "hft ": "finance.trading",
    "order book": "finance.trading",
    "market making": "finance.trading",
    "stock exchange": "finance.trading",
    "derivatives trading": "finance.trading",
    "forex trading": "finance.trading",
    "commodity trading": "finance.trading",

    # Risk Management
    "risk management": "finance.risk",
    "credit risk": "finance.risk",
    "market risk": "finance.risk",
    "operational risk": "finance.risk",
    "value at risk": "finance.risk",
    "var ": "finance.risk",
    "stress test": "finance.risk",
    "scenario analysis": "finance.risk",
    "risk model": "finance.risk",

    # Regulatory & Compliance
    "basel ": "finance.compliance",
    "basel ii": "finance.compliance",
    "basel iii": "finance.compliance",
    "basel iv": "finance.compliance",
    "dodd-frank": "finance.compliance",
    "mifid": "finance.compliance",
    "mifir": "finance.compliance",
    "psd2": "finance.compliance",
    "emir ": "finance.compliance",
    "aml ": "finance.compliance",
    "anti-money laundering": "finance.compliance",
    "kyc ": "finance.compliance",
    "know your customer": "finance.compliance",
    "financial regulation": "finance.compliance",
    "compliance framework": "finance.compliance",

    # Blockchain & Crypto
    "blockchain": "finance.blockchain",
    "cryptocurrency": "finance.blockchain",
    "bitcoin": "finance.blockchain",
    "ethereum": "finance.blockchain",
    "smart contract": "finance.blockchain",
    "distributed ledger": "finance.blockchain",
    "dlt ": "finance.blockchain",
    "defi ": "finance.blockchain",
    "decentralized finance": "finance.blockchain",
    "crypto asset": "finance.blockchain",

    # Economics - Macro
    "macroeconomics": "economics.macro",
    "monetary policy": "economics.macro",
    "fiscal policy": "economics.macro",
    "inflation": "economics.macro",
    "deflation": "economics.macro",
    "interest rate": "economics.macro",
    "gdp ": "economics.macro",
    "pib ": "economics.macro",
    "unemployment": "economics.macro",
    "business cycle": "economics.macro",
    "recession": "economics.macro",

    # Economics - Micro
    "microeconomics": "economics.micro",
    "supply and demand": "economics.micro",
    "market equilibrium": "economics.micro",
    "price elasticity": "economics.micro",
    "consumer behavior": "economics.micro",
    "firm behavior": "economics.micro",

    # Economics - Trade & Energy
    "international trade": "economics.trade",
    "trade agreement": "economics.trade",
    "tariff": "economics.trade",
    "import export": "economics.trade",
    "supply chain": "economics.trade",
    "energy economics": "economics.energy",
    "energy market": "economics.energy",
    "energy pricing": "economics.energy",
    "renewable economics": "economics.energy",
}
