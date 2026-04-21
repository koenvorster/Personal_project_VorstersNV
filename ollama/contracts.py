"""
VorstersNV Typed Domain Contracts
Lingua franca tussen agents in skill chains — vervangt ongestructureerde strings.

Elk contract heeft:
  - to_prompt_input()     → str voor injectie in agent prompt
  - from_agent_output()   → instantie vanuit agent JSON output
  - validate()            → bool + lijst van validatiefouten

Gebruik:
    contract = OrderAnalysisContract(order_id="ORD-2024-1234", ...)
    prompt_ctx = contract.to_prompt_input()

    result_contract = FraudAssessmentContract.from_agent_output(agent_output)
    is_valid, errors = result_contract.validate()
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Base Contract
# ─────────────────────────────────────────────

@dataclass
class BaseContract:
    """Basis contract — alle domain contracts erven hiervan."""
    contract_version: str = "1.0"
    agent_name: str = ""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_prompt_input(self) -> str:
        """Serialiseer contract naar prompt-injecteerbare string."""
        raise NotImplementedError

    @classmethod
    def from_agent_output(cls, output: str) -> "BaseContract":
        """Deserialiseer agent JSON output naar contract instantie."""
        raise NotImplementedError

    def validate(self) -> tuple[bool, list[str]]:
        """
        Valideer contract integriteit.

        Returns:
            (is_valid, lijst_van_fouten)
        """
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        """Serialiseer contract naar dict."""
        raise NotImplementedError

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any] | None:
        """Extraheer eerste JSON object uit tekst."""
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None


# ─────────────────────────────────────────────
# Order Analysis Contract
# ─────────────────────────────────────────────

@dataclass
class OrderAnalysisContract(BaseContract):
    """
    Input contract voor order analyse agents.
    Gebouwd vanuit ruwe order data, doorgegeven aan fraude en verificatie agents.
    """
    order_id: str = ""
    customer_id: str = ""
    order_value: float = 0.0
    payment_method: str = ""
    delivery_country: str = "BE"
    billing_country: str = "BE"
    customer_age_days: int = 0
    previous_orders: int = 0
    uses_vpn: bool = False
    items_count: int = 0
    payment_status: str = ""

    def to_prompt_input(self) -> str:
        return (
            f"## Order Analyse Context\n"
            f"- Order ID: {self.order_id}\n"
            f"- Klant ID: {self.customer_id}\n"
            f"- Orderwaarde: €{self.order_value:.2f}\n"
            f"- Betaalmethode: {self.payment_method}\n"
            f"- Bezorgland/Facturatieland: {self.delivery_country}/{self.billing_country}\n"
            f"- Klantaccount leeftijd: {self.customer_age_days} dagen\n"
            f"- Vorige bestellingen: {self.previous_orders}\n"
            f"- VPN/Proxy gedetecteerd: {self.uses_vpn}\n"
            f"- Aantal artikelen: {self.items_count}\n"
            f"- Betalingsstatus: {self.payment_status}\n"
            f"- trace_id: {self.trace_id}"
        )

    @classmethod
    def from_agent_output(cls, output: str) -> "OrderAnalysisContract":
        data = cls._extract_json(output) or {}
        return cls(
            order_id=data.get("order_id", ""),
            customer_id=data.get("customer_id", ""),
            order_value=float(data.get("order_value", 0)),
            payment_method=data.get("payment_method", ""),
            delivery_country=data.get("delivery_country", "BE"),
            billing_country=data.get("billing_country", "BE"),
            customer_age_days=int(data.get("customer_age_days", 0)),
            previous_orders=int(data.get("previous_orders", 0)),
            uses_vpn=bool(data.get("uses_vpn", False)),
            items_count=int(data.get("items_count", 0)),
            payment_status=data.get("payment_status", ""),
        )

    def validate(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not self.order_id:
            errors.append("order_id is verplicht")
        if self.order_value <= 0:
            errors.append("order_value moet groter zijn dan 0")
        if not self.payment_method:
            errors.append("payment_method is verplicht")
        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "order_value": self.order_value,
            "payment_method": self.payment_method,
            "delivery_country": self.delivery_country,
            "billing_country": self.billing_country,
            "customer_age_days": self.customer_age_days,
            "previous_orders": self.previous_orders,
            "uses_vpn": self.uses_vpn,
            "items_count": self.items_count,
            "payment_status": self.payment_status,
            "trace_id": self.trace_id,
        }


# ─────────────────────────────────────────────
# Fraud Assessment Contract
# ─────────────────────────────────────────────

_VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
_VALID_ACTIONS = {"ALLOW", "REVIEW", "BLOCK"}


@dataclass
class FraudAssessmentContract(BaseContract):
    """
    Output contract van fraude detectie agents.
    Bevat de complete fraude beoordeling inclusief rationale en aanbeveling.
    """
    order_id: str = ""
    risk_score: int = 0           # 0-100
    risk_level: str = "LOW"       # LOW | MEDIUM | HIGH | CRITICAL
    rationale: list[str] = field(default_factory=list)
    recommended_action: str = "ALLOW"  # ALLOW | REVIEW | BLOCK
    requires_human: bool = False
    confidence: float = 0.0       # 0.0-1.0
    model_used: str = ""

    def __post_init__(self) -> None:
        # Automatisch requires_human afleiden op basis van risk_score
        if self.risk_score >= 75 and not self.requires_human:
            self.requires_human = True

    def to_prompt_input(self) -> str:
        rationale_str = "\n".join(f"  - {r}" for r in self.rationale)
        return (
            f"## Fraude Beoordeling\n"
            f"- Order ID: {self.order_id}\n"
            f"- Risicoscore: {self.risk_score}/100\n"
            f"- Risiconiveau: {self.risk_level}\n"
            f"- Aanbeveling: {self.recommended_action}\n"
            f"- Menselijke review vereist: {self.requires_human}\n"
            f"- Betrouwbaarheid: {self.confidence:.0%}\n"
            f"- Rationale:\n{rationale_str}\n"
            f"- trace_id: {self.trace_id}"
        )

    @classmethod
    def from_agent_output(cls, output: str) -> "FraudAssessmentContract":
        data = cls._extract_json(output) or {}
        risk_score = int(data.get("risk_score", 0))
        return cls(
            order_id=data.get("order_id", ""),
            risk_score=risk_score,
            risk_level=data.get("risk_level", _score_to_level(risk_score)),
            rationale=data.get("rationale", []),
            recommended_action=data.get("recommended_action", "ALLOW"),
            requires_human=bool(data.get("requires_human", risk_score >= 75)),
            confidence=float(data.get("confidence", 0.0)),
            model_used=data.get("model_used", ""),
        )

    def validate(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not self.order_id:
            errors.append("order_id is verplicht")
        if not (0 <= self.risk_score <= 100):
            errors.append(f"risk_score {self.risk_score} moet tussen 0 en 100 zijn")
        if self.risk_level not in _VALID_RISK_LEVELS:
            errors.append(f"risk_level '{self.risk_level}' ongeldig — kies uit {_VALID_RISK_LEVELS}")
        if self.recommended_action not in _VALID_ACTIONS:
            errors.append(f"recommended_action '{self.recommended_action}' ongeldig — kies uit {_VALID_ACTIONS}")
        if not self.rationale:
            errors.append("rationale mag niet leeg zijn")
        if not (0.0 <= self.confidence <= 1.0):
            errors.append(f"confidence {self.confidence} moet tussen 0.0 en 1.0 zijn")
        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "rationale": self.rationale,
            "recommended_action": self.recommended_action,
            "requires_human": self.requires_human,
            "confidence": self.confidence,
            "model_used": self.model_used,
            "trace_id": self.trace_id,
        }


# ─────────────────────────────────────────────
# Content Generation Contract
# ─────────────────────────────────────────────

@dataclass
class ContentGenerationContract(BaseContract):
    """
    Contract voor product content generatie agents.
    Bevat gegenereerde tekst + SEO metadata + compliance velden.
    """
    product_id: str = ""
    product_name: str = ""
    titel: str = ""
    beschrijving: str = ""
    seo_keywords: list[str] = field(default_factory=list)
    btw_categorie: str = "21%"   # 6% of 21%
    voldoet_aan_voedselwet: bool = False
    taal: str = "nl"
    word_count: int = 0
    review_verdict: str = ""     # APPROVED | CHANGES_REQUESTED

    def to_prompt_input(self) -> str:
        keywords_str = ", ".join(self.seo_keywords) if self.seo_keywords else "—"
        return (
            f"## Content Generatie Context\n"
            f"- Product ID: {self.product_id}\n"
            f"- Product naam: {self.product_name}\n"
            f"- Taal: {self.taal}\n"
            f"- BTW categorie: {self.btw_categorie}\n"
            f"- Gegenereerde titel: {self.titel or '(nog niet gegenereerd)'}\n"
            f"- SEO keywords: {keywords_str}\n"
            f"- Woordenaantal: {self.word_count}\n"
            f"- trace_id: {self.trace_id}"
        )

    @classmethod
    def from_agent_output(cls, output: str) -> "ContentGenerationContract":
        data = cls._extract_json(output) or {}
        beschrijving = data.get("beschrijving", "")
        return cls(
            product_id=data.get("product_id", ""),
            product_name=data.get("product_name", ""),
            titel=data.get("titel", ""),
            beschrijving=beschrijving,
            seo_keywords=data.get("seo_keywords", []),
            btw_categorie=data.get("btw_categorie", "21%"),
            voldoet_aan_voedselwet=bool(data.get("voldoet_aan_voedselwet", False)),
            taal=data.get("taal", "nl"),
            word_count=len(beschrijving.split()) if beschrijving else 0,
            review_verdict=data.get("review_verdict", ""),
        )

    def validate(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not self.titel:
            errors.append("titel is verplicht")
        if len(self.titel) > 100:
            errors.append(f"titel te lang ({len(self.titel)} tekens) — max 100")
        if not self.beschrijving:
            errors.append("beschrijving is verplicht")
        if len(self.beschrijving) < 50:
            errors.append(f"beschrijving te kort ({len(self.beschrijving)} tekens) — min 50")
        if not self.seo_keywords:
            errors.append("seo_keywords mag niet leeg zijn")
        if self.btw_categorie not in ("6%", "21%"):
            errors.append(f"btw_categorie '{self.btw_categorie}' ongeldig — kies 6% of 21%")
        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "titel": self.titel,
            "beschrijving": self.beschrijving,
            "seo_keywords": self.seo_keywords,
            "btw_categorie": self.btw_categorie,
            "voldoet_aan_voedselwet": self.voldoet_aan_voedselwet,
            "taal": self.taal,
            "word_count": self.word_count,
            "review_verdict": self.review_verdict,
            "trace_id": self.trace_id,
        }


# ─────────────────────────────────────────────
# Hulpfuncties
# ─────────────────────────────────────────────

def _score_to_level(score: int) -> str:
    """Converteer numerieke risicoscore naar risiconiveau string."""
    if score < 40:
        return "LOW"
    if score < 75:
        return "MEDIUM"
    if score < 90:
        return "HIGH"
    return "CRITICAL"
