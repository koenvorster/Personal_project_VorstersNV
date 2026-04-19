"""
VorstersNV Multi-Agent Orchestrator
Coördineert meerdere AI-agents in gedefinieerde workflows.
"""
import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from .agent_runner import AgentRunner, RetryConfig, get_runner

logger = logging.getLogger(__name__)

# Herroepingsdrempel voor fraude-blocking (75+ = blokkeren)
FRAUD_BLOCK_THRESHOLD = 75

# Zoekwoorden die een retour-vraag aangeven in klantberichten
_RETOUR_KEYWORDS = re.compile(
    r"\b(retour\w*|terugsturen|terugzenden|teruggeven|ruilen|ruillen|"
    r"defect|kapot|beschadigd|verkeerd product|niet goed|niet wat ik|"
    r"terugbetaling|refund|geld terug)\b",
    re.IGNORECASE,
)

# Zoekwoorden die directe escalatie vereisen
_ESCALATIE_KEYWORDS = re.compile(
    r"\b(advocaat|rechtbank|consumentenombudsman|oplichters|aanklacht|"
    r"juridisch|discrimin|bedreiging|fraude|chargeback)\b",
    re.IGNORECASE,
)


@dataclass
class OrchestratorStep:
    """Een stap in een orchestratie-workflow."""
    agent_name: str
    description: str
    context_key: str = ""       # Sleutel om output op te slaan in context
    required: bool = True       # Als False, ga door ook bij fout
    condition_key: str = ""     # Sla stap over als context[condition_key] ontbreekt
    skip_if_blocked: bool = False  # Sla stap over als context["fraud_blocked"] == True


@dataclass
class ParallelStep:
    """Meerdere agent-stappen die parallel uitgevoerd worden."""
    steps: list[OrchestratorStep]
    description: str


@dataclass
class OrchestratorResult:
    """Resultaat van een orchestratie-workflow."""
    workflow_name: str
    steps_completed: int
    steps_total: int
    outputs: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    success: bool = True
    fraud_blocked: bool = False
    fraud_score: int | None = None
    escalatie_vereist: bool = False


def _parse_fraud_score(agent_output: str) -> int | None:
    """
    Parseer de risicoscore uit de JSON-output van fraude_detectie_agent.

    Retourneert de score als integer (0-100), of None als parsing mislukt.
    """
    try:
        # Zoek JSON-blok in de output (agent kan tekst voor/na JSON hebben)
        match = re.search(r"\{.*\}", agent_output, re.DOTALL)
        if match:
            data = json.loads(match.group())
            score = data.get("risicoscore")
            if isinstance(score, (int, float)):
                return int(score)
    except (json.JSONDecodeError, AttributeError):
        pass
    logger.warning("Kon fraudescore niet parseren uit output: %.100s...", agent_output)
    return None


def _classify_klantenservice_vraag(user_input: str, agent_output: str = "") -> str:
    """
    Classificeer een klantenvraag op basis van zoekwoorden.

    Args:
        user_input: Originele vraag van de klant
        agent_output: Output van klantenservice_agent (optioneel)

    Returns:
        Categorie als string: "retour" | "escalatie" | "standaard"
    """
    tekst = user_input + " " + agent_output
    if _ESCALATIE_KEYWORDS.search(tekst):
        return "escalatie"
    if _RETOUR_KEYWORDS.search(tekst):
        return "retour"
    return "standaard"


class AgentOrchestrator:
    """
    Coördineert meerdere AI-agents in volgorde.

    Gebruik dit voor complexe workflows waarbij agents
    elkaars output als input gebruiken.
    """

    def __init__(self, runner: AgentRunner | None = None):
        self._runner = runner or get_runner()

    async def run_workflow(
        self,
        workflow_name: str,
        steps: list[OrchestratorStep],
        initial_input: str,
        shared_context: dict[str, Any] | None = None,
        retry_config: RetryConfig | None = None,
    ) -> OrchestratorResult:
        """
        Voer een multi-step workflow uit.

        Args:
            workflow_name: Naam van de workflow (voor logging)
            steps: Lijst van te uitvoeren stappen
            initial_input: Initiële input voor de eerste agent
            shared_context: Gedeelde context beschikbaar voor alle stappen
            retry_config: Retry-instellingen (standaard: 3 pogingen)

        Returns:
            OrchestratorResult met alle outputs en eventuele fouten
        """
        context = dict(shared_context or {})
        result = OrchestratorResult(
            workflow_name=workflow_name,
            steps_total=len(steps),
            steps_completed=0,
        )
        current_input = initial_input

        logger.info("Orchestrator start workflow '%s' met %d stappen", workflow_name, len(steps))

        for i, step in enumerate(steps):
            # Sla stap over als conditie-sleutel ontbreekt in context
            if step.condition_key and step.condition_key not in context:
                logger.info(
                    "Stap %d/%d overgeslagen (conditie '%s' niet aanwezig)",
                    i + 1, len(steps), step.condition_key,
                )
                result.steps_total -= 1
                continue

            # Sla stap over als fraude geblokkeerd is
            if step.skip_if_blocked and context.get("fraud_blocked"):
                logger.warning(
                    "Stap %d/%d '%s' overgeslagen — fraude geblokkeerd",
                    i + 1, len(steps), step.agent_name,
                )
                result.steps_total -= 1
                continue

            logger.info(
                "Stap %d/%d: agent='%s' – %s",
                i + 1, len(steps), step.agent_name, step.description,
            )
            try:
                output, interaction_id = await self._runner.run_agent_with_retry(
                    agent_name=step.agent_name,
                    user_input=current_input,
                    context=context,
                    retry_config=retry_config,
                )

                result.steps_completed += 1

                # Sla output op in context voor volgende stap
                if step.context_key:
                    context[step.context_key] = output

                # Output van deze stap wordt input van de volgende
                current_input = output

                if step.context_key:
                    result.outputs[step.context_key] = output
                else:
                    result.outputs[f"stap_{i + 1}"] = output

                logger.info("Stap %d voltooid (%d tekens)", i + 1, len(output))

                # Na fraude-check: parseer score en stel blocking in
                if step.context_key == "fraude_beoordeling":
                    score = _parse_fraud_score(output)
                    result.fraud_score = score
                    if score is not None and score >= FRAUD_BLOCK_THRESHOLD:
                        context["fraud_blocked"] = True
                        result.fraud_blocked = True
                        logger.warning(
                            "Fraude geblokkeerd — score %d >= drempel %d voor order '%s'",
                            score, FRAUD_BLOCK_THRESHOLD, context.get("order_id", "?"),
                        )

            except Exception as exc:
                error_msg = f"Stap {i + 1} ({step.agent_name}): {exc}"
                logger.error("Orchestrator fout: %s", error_msg)
                result.errors.append(error_msg)

                if step.required:
                    result.success = False
                    logger.error("Verplichte stap mislukt – workflow gestopt")
                    break
                else:
                    logger.warning("Optionele stap mislukt – workflow gaat door")

        logger.info(
            "Workflow '%s' klaar: %d/%d stappen, succes=%s, fraude_blocked=%s",
            workflow_name,
            result.steps_completed,
            result.steps_total,
            result.success,
            result.fraud_blocked,
        )
        return result

    # ─────────────────────────────────────────────
    # PIPELINE 1: Product publicatie
    # ─────────────────────────────────────────────

    async def run_product_pipeline(
        self,
        product_naam: str,
        categorie: str,
        kenmerken: list[str],
        prijs: float,
        doelgroep: str = "algemeen",
        tone_of_voice: str = "vriendelijk",
        primair_zoekwoord: str = "",
        btw_percentage: int = 21,
        retry_config: RetryConfig | None = None,
    ) -> OrchestratorResult:
        """
        Pipeline: beschrijving genereren → SEO optimaliseren → content team notificeren.

        Stap 1: product_beschrijving_agent — schrijft JSON-output met titel, beschrijving, tags
        Stap 2: seo_agent — optimaliseert metatags en structured data (optioneel)
        Stap 3: email_template_agent — notificeert content manager (optioneel)
        """
        steps = [
            OrchestratorStep(
                agent_name="product_beschrijving_agent",
                description="Productbeschrijving genereren (JSON output)",
                context_key="productbeschrijving",
            ),
            OrchestratorStep(
                agent_name="seo_agent",
                description="SEO-optimalisatie toepassen",
                context_key="seo_output",
                required=False,
            ),
            OrchestratorStep(
                agent_name="email_template_agent",
                description="Content team notificeren over nieuw product",
                context_key="notificatie_email",
                required=False,
            ),
        ]
        initial_input = (
            f"Schrijf een complete productbeschrijving voor '{product_naam}'. "
            f"Categorie: {categorie}. "
            f"Kenmerken: {', '.join(kenmerken)}. "
            f"Doelgroep: {doelgroep}. "
            f"Primair zoekwoord: {primair_zoekwoord or product_naam}."
        )
        return await self.run_workflow(
            workflow_name="product_pipeline",
            steps=steps,
            initial_input=initial_input,
            shared_context={
                "product_naam": product_naam,
                "categorie": categorie,
                "prijs": prijs,
                "btw_percentage": btw_percentage,
                "doelgroep": doelgroep,
                "tone_of_voice": tone_of_voice,
                "primair_zoekwoord": primair_zoekwoord or product_naam,
                "email_type": "backorder",  # hergebruik als interne notificatie
                "klant_voornaam": "Content Team",
                "is_transactioneel": "true",
            },
            retry_config=retry_config,
        )

    # ─────────────────────────────────────────────
    # PIPELINE 2: Order verwerking
    # ─────────────────────────────────────────────

    async def run_order_pipeline(
        self,
        order_id: str,
        klant_id: str,
        klant_voornaam: str,
        klant_email: str,
        orderwaarde: float,
        betaalmethode: str,
        producten: list[dict[str, Any]],
        bezorgadres: str,
        mollie_payment_id: str = "",
        account_leeftijd_dagen: int = 0,
        eerdere_chargebacks: int = 0,
        ip_type: str = "residential",
        adressen_gelijk: bool = True,
        retry_config: RetryConfig | None = None,
    ) -> OrchestratorResult:
        """
        Pipeline: fraude-check → (conditioneel) order verwerken → e-mail bevestiging → voorraad signaal.

        Stap 1: fraude_detectie_agent — risicoscore (JSON). Score ≥ 75 → blokkeer pipeline.
        Stap 2: order_verwerking_agent — verwerk order (OVERGESLAGEN bij fraude-blokkering)
        Stap 3: email_template_agent — orderbevestiging naar klant (OVERGESLAGEN bij fraude-blokkering)
        Stap 4: voorraad_advies_agent — signaal voor stockupdate na verwerking (optioneel)
        """
        steps = [
            OrchestratorStep(
                agent_name="fraude_detectie_agent",
                description="Fraude-risico beoordelen",
                context_key="fraude_beoordeling",
            ),
            OrchestratorStep(
                agent_name="order_verwerking_agent",
                description="Order valideren en verwerken",
                context_key="order_verwerking",
                skip_if_blocked=True,
            ),
            OrchestratorStep(
                agent_name="email_template_agent",
                description="Orderbevestiging genereren voor klant",
                context_key="bevestigings_email",
                required=False,
                skip_if_blocked=True,
            ),
            OrchestratorStep(
                agent_name="voorraad_advies_agent",
                description="Voorraadsignaal na orderverwerking",
                context_key="voorraad_signaal",
                required=False,
                skip_if_blocked=True,
            ),
        ]
        initial_input = (
            f"Beoordeel order {order_id} op fraude. "
            f"Orderwaarde: €{orderwaarde:.2f}. "
            f"Betaalmethode: {betaalmethode}. "
            f"Account leeftijd: {account_leeftijd_dagen} dagen. "
            f"Eerdere chargebacks: {eerdere_chargebacks}."
        )
        return await self.run_workflow(
            workflow_name="order_pipeline",
            steps=steps,
            initial_input=initial_input,
            shared_context={
                "order_id": order_id,
                "klant_id": klant_id,
                "klant_voornaam": klant_voornaam,
                "klant_email": klant_email,
                "orderwaarde": orderwaarde,
                "betaalmethode": betaalmethode,
                "bezorgadres": bezorgadres,
                "mollie_payment_id": mollie_payment_id,
                "account_leeftijd_dagen": account_leeftijd_dagen,
                "eerdere_chargebacks": eerdere_chargebacks,
                "ip_type": ip_type,
                "adressen_gelijk": str(adressen_gelijk).lower(),
                "email_type": "orderbevestiging",
                "is_transactioneel": "true",
                "event_type": "order.paid",
                "nieuwe_status": "BETAALD",
                "vorige_status": "BEVESTIGD",
            },
            retry_config=retry_config,
        )

    # ─────────────────────────────────────────────
    # PIPELINE 3: Klantenservice
    # ─────────────────────────────────────────────

    async def run_klantenservice_pipeline(
        self,
        klant_vraag: str,
        klant_naam: str,
        klant_email: str,
        klant_id: str = "",
        klant_nummer: str = "",
        order_id: str = "",
        orderdatum: str = "",
        ontvangstdatum: str = "",
        orderwaarde: float = 0.0,
        retry_config: RetryConfig | None = None,
    ) -> OrchestratorResult:
        """
        Pipeline: triage → routeer naar retour-subworkflow, standaard antwoord, of escalatie.

        Stap 1: klantenservice_agent — initiele reactie + triage (altijd)
        Stap 2a (retour):   retour_verwerking_agent (als retour-intent gedetecteerd)
        Stap 2b (retour):   email_template_agent — retourbevestiging
        Stap 2c (escalatie): flag escalatie_vereist = True (geen extra agent)

        Routing is keyword-gebaseerd op klant_vraag + klantenservice output.
        """
        shared_context: dict[str, Any] = {
            "klant_naam": klant_naam,
            "klant_voornaam": klant_naam.split()[0] if klant_naam else "klant",
            "klant_email": klant_email,
            "klant_id": klant_id,
            "klant_nummer": klant_nummer,
            "klant_vraag": klant_vraag,
            "order_id": order_id,
            "orderdatum": orderdatum,
            "ontvangstdatum": ontvangstdatum,
            "orderwaarde": orderwaarde,
            "kanaal": "chat",
            "prioriteit": "normaal",
            "is_transactioneel": "true",
        }

        # Stap 1: klantenservice triage
        triage_steps = [
            OrchestratorStep(
                agent_name="klantenservice_agent",
                description="Klantvraag beantwoorden en categoriseren",
                context_key="klantenservice_antwoord",
            ),
        ]
        result = await self.run_workflow(
            workflow_name="klantenservice_triage",
            steps=triage_steps,
            initial_input=klant_vraag,
            shared_context=shared_context,
            retry_config=retry_config,
        )

        if not result.success:
            return result

        # Categorie bepalen op basis van klant_vraag + agent output
        klantenservice_output = result.outputs.get("klantenservice_antwoord", "")
        categorie = _classify_klantenservice_vraag(klant_vraag, klantenservice_output)
        result.outputs["vraag_categorie"] = categorie
        logger.info("Klantenservice triage: categorie='%s'", categorie)

        if categorie == "escalatie":
            result.escalatie_vereist = True
            result.outputs["escalatie_reden"] = (
                "Juridische of agressieve taal gedetecteerd — menselijke medewerker vereist."
            )
            logger.warning(
                "Klantenservice escalatie vereist voor klant '%s'", klant_naam,
            )

        elif categorie == "retour" and order_id:
            # Stap 2: retour sub-workflow
            shared_context.update({
                "retour_reden": "niet_verwacht",  # standaard; klant kan preciseren
                "email_type": "retourbevestiging",
                "datum_yyyymmdd": "",
            })
            retour_steps = [
                OrchestratorStep(
                    agent_name="retour_verwerking_agent",
                    description="Retouraanvraag verwerken",
                    context_key="retour_beoordeling",
                ),
                OrchestratorStep(
                    agent_name="email_template_agent",
                    description="Retourbevestiging sturen",
                    context_key="retour_email",
                    required=False,
                ),
            ]
            retour_result = await self.run_workflow(
                workflow_name="klantenservice_retour",
                steps=retour_steps,
                initial_input=klantenservice_output,
                shared_context=shared_context,
                retry_config=retry_config,
            )
            # Merge retour outputs in hoofdresultaat
            result.outputs.update(retour_result.outputs)
            result.steps_completed += retour_result.steps_completed
            result.steps_total += retour_result.steps_total
            result.errors.extend(retour_result.errors)
            if not retour_result.success:
                result.success = False

        result.workflow_name = "klantenservice_pipeline"
        return result

    # ─────────────────────────────────────────────
    # PIPELINE 4: Checkout
    # ─────────────────────────────────────────────

    async def run_checkout_pipeline(
        self,
        order_id: str,
        klant_naam: str,
        klant_email: str,
        klant_land: str,
        cart_items: list[dict[str, Any]],
        totaal_incl: float,
        btw_bedrag: float,
        betaalmethode: str,
        betaal_url: str,
        retry_config: RetryConfig | None = None,
    ) -> OrchestratorResult:
        """
        Pipeline: checkout-begeleiding → orderbevestigingsmail.

        Stap 1: checkout_begeleiding_agent — valideer checkout-context en geef klantfeedback (optioneel)
        Stap 2: email_template_agent — stuur orderbevestiging incl. betaallink

        Gebruik deze pipeline nadat de order succesvol aangemaakt is in de DB
        en de Mollie-betaallink beschikbaar is.
        """
        steps = [
            OrchestratorStep(
                agent_name="checkout_begeleiding_agent",
                description="Checkout-context valideren en klant begeleiden",
                context_key="checkout_status",
                required=False,
            ),
            OrchestratorStep(
                agent_name="email_template_agent",
                description="Orderbevestiging + betaallink versturen",
                context_key="bevestigings_email",
                required=False,
            ),
        ]
        cart_samenvatting = ", ".join(
            f"{i.get('naam', 'artikel')} x{i.get('aantal', 1)}" for i in cart_items
        )
        initial_input = (
            f"Checkout voltooid voor order {order_id}. "
            f"Klant: {klant_naam} ({klant_email}). "
            f"Totaal: €{totaal_incl:.2f} incl. BTW. "
            f"Betaalmethode: {betaalmethode}."
        )
        return await self.run_workflow(
            workflow_name="checkout_pipeline",
            steps=steps,
            initial_input=initial_input,
            shared_context={
                "order_id": order_id,
                "klant_naam": klant_naam,
                "klant_voornaam": klant_naam.split()[0] if klant_naam else "klant",
                "klant_email": klant_email,
                "klant_land": klant_land,
                "totaal_incl": totaal_incl,
                "btw_bedrag": btw_bedrag,
                "totaal_excl": round(totaal_incl - btw_bedrag, 2),
                "betaalmethode": betaalmethode,
                "betaal_url": betaal_url,
                "cart_samenvatting": cart_samenvatting,
                "checkout_stap": "bevestiging",
                "fout_code": "",
                "fout_details": "",
                "aantal_pogingen": 0,
                "email_type": "orderbevestiging",
                "is_transactioneel": "true",
                "aanspreking": "informeel",
            },
            retry_config=retry_config,
        )

    # ─────────────────────────────────────────────
    # PIPELINE 5: Betaling mislukt
    # ─────────────────────────────────────────────

    async def run_payment_failed_pipeline(
        self,
        order_id: str,
        betaling_id: str,
        klant_naam: str,
        klant_email: str,
        klant_land: str,
        bedrag: float,
        betaalmethode: str,
        mollie_status: str,
        mollie_fout_code: str = "",
        aantal_pogingen: int = 1,
        retry_config: RetryConfig | None = None,
    ) -> OrchestratorResult:
        """
        Pipeline: betaling_status_agent → (conditioneel) email betaling_mislukt.

        Stap 1: betaling_status_agent — diagnosticeer fout, geef alternatieve methoden
        Stap 2: email_template_agent — stuur betaling_mislukt e-mail met nieuwe betaallink (optioneel)

        Wordt getriggerd door Mollie webhook: payment.failed / payment.expired / payment.cancelled.
        """
        steps = [
            OrchestratorStep(
                agent_name="betaling_status_agent",
                description="Betalingsfout diagnosticeren en alternatieven voorstellen",
                context_key="betaling_diagnose",
            ),
            OrchestratorStep(
                agent_name="email_template_agent",
                description="Betaling mislukt e-mail sturen met herbetalingsopties",
                context_key="betaling_mislukt_email",
                required=False,
            ),
        ]
        initial_input = (
            f"Betaling mislukt voor order {order_id}. "
            f"Betaling-ID: {betaling_id}. "
            f"Mollie-status: {mollie_status}. "
            f"Fout: {mollie_fout_code or 'onbekend'}. "
            f"Methode: {betaalmethode}. "
            f"Bedrag: €{bedrag:.2f}. "
            f"Poging {aantal_pogingen}/3."
        )
        return await self.run_workflow(
            workflow_name="payment_failed_pipeline",
            steps=steps,
            initial_input=initial_input,
            shared_context={
                "order_id": order_id,
                "betaling_id": betaling_id,
                "klant_naam": klant_naam,
                "klant_voornaam": klant_naam.split()[0] if klant_naam else "klant",
                "klant_email": klant_email,
                "klant_land": klant_land,
                "bedrag": bedrag,
                "betaalmethode": betaalmethode,
                "mollie_status": mollie_status,
                "mollie_fout_code": mollie_fout_code,
                "aantal_pogingen": aantal_pogingen,
                "email_type": "betaling_mislukt",
                "is_transactioneel": "true",
                "aanspreking": "informeel",
            },
            retry_config=retry_config,
        )

    # ─────────────────────────────────────────────
    # Parallelle uitvoering
    # ─────────────────────────────────────────────

    async def run_parallel(
        self,
        parallel_step: ParallelStep,
        shared_input: str,
        shared_context: dict[str, Any] | None = None,
        retry_config: RetryConfig | None = None,
    ) -> dict[str, str]:
        """
        Voer meerdere agent-stappen tegelijk uit (parallel).

        Args:
            parallel_step: De parallel-stap definitie
            shared_input: Gedeelde input voor alle agents
            shared_context: Gedeelde context voor alle agents
            retry_config: Retry-instellingen

        Returns:
            Dict van context_key → output voor elke sub-stap
        """
        context = dict(shared_context or {})
        logger.info(
            "Parallel uitvoering gestart: '%s' (%d agents)",
            parallel_step.description,
            len(parallel_step.steps),
        )

        async def _run_one(step: OrchestratorStep) -> tuple[str, str]:
            output, _ = await self._runner.run_agent_with_retry(
                agent_name=step.agent_name,
                user_input=shared_input,
                context=context,
                retry_config=retry_config,
            )
            return step.context_key or step.agent_name, output

        results = await asyncio.gather(
            *[_run_one(s) for s in parallel_step.steps],
            return_exceptions=True,
        )

        outputs: dict[str, str] = {}
        for step, res in zip(parallel_step.steps, results):
            if isinstance(res, Exception):
                logger.error("Parallelle stap '%s' mislukt: %s", step.agent_name, res)
                if step.required:
                    raise res
            else:
                key_out, output = res
                outputs[key_out] = output
                logger.info("Parallelle stap '%s' klaar (%d tekens)", step.agent_name, len(output))

        return outputs

    # ─────────────────────────────────────────────
    # Legacy methoden (backwards compatibility)
    # ─────────────────────────────────────────────

    async def run_product_publishing_workflow(
        self,
        product_naam: str,
        categorie: str,
        kenmerken: list[str],
        doelgroep: str = "algemeen",
    ) -> OrchestratorResult:
        """Legacy alias — gebruik run_product_pipeline."""
        return await self.run_product_pipeline(
            product_naam=product_naam,
            categorie=categorie,
            kenmerken=kenmerken,
            prijs=0.0,
            doelgroep=doelgroep,
        )

    async def run_order_fulfillment_workflow(
        self,
        order_id: str,
        klant_naam: str,
        klant_email: str,
        producten: list[dict],
    ) -> OrchestratorResult:
        """Legacy alias — gebruik run_order_pipeline."""
        return await self.run_order_pipeline(
            order_id=order_id,
            klant_id="",
            klant_voornaam=klant_naam,
            klant_email=klant_email,
            orderwaarde=0.0,
            betaalmethode="onbekend",
            producten=producten,
            bezorgadres="",
        )

    async def run_order_with_fraud_check_workflow(
        self,
        order_id: str,
        klant_naam: str,
        klant_email: str,
        klant_id: str,
        orderwaarde: float,
        betaalmethode: str,
        producten: list[dict],
        bezorgadres: str,
        klant_metadata: dict[str, Any] | None = None,
    ) -> OrchestratorResult:
        """Legacy alias — gebruik run_order_pipeline."""
        meta = klant_metadata or {}
        return await self.run_order_pipeline(
            order_id=order_id,
            klant_id=klant_id,
            klant_voornaam=klant_naam,
            klant_email=klant_email,
            orderwaarde=orderwaarde,
            betaalmethode=betaalmethode,
            producten=producten,
            bezorgadres=bezorgadres,
            account_leeftijd_dagen=meta.get("account_leeftijd_dagen", 0),
            eerdere_chargebacks=meta.get("eerdere_chargebacks", 0),
        )

    async def run_retour_workflow(
        self,
        retour_id: str,
        order_id: str,
        klant_naam: str,
        klant_email: str,
        retour_reden: str,
        producten: list[dict],
        orderdatum: str,
        ontvangstdatum: str,
        retry_config: RetryConfig | None = None,
    ) -> OrchestratorResult:
        """
        Workflow: retour beoordelen → e-mail sturen → order updaten.

        Stap 1: retour_verwerking_agent — beoordeel en verwerk de retouraanvraag
        Stap 2: email_template_agent — genereer retourbevestiging
        Stap 3: order_verwerking_agent — update orderstatus
        """
        steps = [
            OrchestratorStep(
                agent_name="retour_verwerking_agent",
                description="Retouraanvraag beoordelen en verwerken",
                context_key="retour_beoordeling",
            ),
            OrchestratorStep(
                agent_name="email_template_agent",
                description="Retourbevestiging genereren",
                context_key="retour_email",
                required=False,
            ),
            OrchestratorStep(
                agent_name="order_verwerking_agent",
                description="Orderstatus en voorraad bijwerken",
                context_key="order_update",
            ),
        ]
        initial_input = (
            f"Verwerk retouraanvraag {retour_id} voor order {order_id}. "
            f"Klant: {klant_naam} ({klant_email}). "
            f"Reden: {retour_reden}. Producten: {producten}."
        )
        return await self.run_workflow(
            workflow_name="retour_verwerking",
            steps=steps,
            initial_input=initial_input,
            shared_context={
                "retour_id": retour_id,
                "order_id": order_id,
                "klant_naam": klant_naam,
                "klant_voornaam": klant_naam.split()[0] if klant_naam else klant_naam,
                "klant_email": klant_email,
                "retour_reden": retour_reden,
                "orderdatum": orderdatum,
                "ontvangstdatum": ontvangstdatum,
                "email_type": "retourbevestiging",
                "is_transactioneel": "true",
                "event_type": "order.returned",
                "nieuwe_status": "RETOUR_OPEN",
                "vorige_status": "AFGELEVERD",
            },
            retry_config=retry_config,
        )

    async def run_voorraad_rapport_workflow(
        self,
        magazijn: str = "hoofdmagazijn",
        retry_config: RetryConfig | None = None,
    ) -> OrchestratorResult:
        """
        Workflow: analyseer voorraad → schrijf inkoopadvies e-mail.

        Stap 1: voorraad_advies_agent — genereer gedetailleerd besteladvies
        Stap 2: email_template_agent — schrijf inkoopadvies als e-mail voor inkoper
        """
        import datetime

        steps = [
            OrchestratorStep(
                agent_name="voorraad_advies_agent",
                description="Voorraadniveaus analyseren en besteladvies genereren",
                context_key="voorraad_rapport",
            ),
            OrchestratorStep(
                agent_name="email_template_agent",
                description="Inkoopadvies e-mail schrijven",
                context_key="inkoop_email",
                required=False,
            ),
        ]
        initial_input = (
            f"Genereer een volledig voorraad-rapport en besteladvies voor magazijn '{magazijn}'."
        )
        return await self.run_workflow(
            workflow_name="voorraad_rapport",
            steps=steps,
            initial_input=initial_input,
            shared_context={
                "datum": datetime.date.today().isoformat(),
                "magazijn": magazijn,
                "email_type": "backorder",
                "tone_of_voice": "formeel",
                "is_transactioneel": "true",
                "klant_voornaam": "Inkoper",
            },
            retry_config=retry_config,
        )


_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    """Geef de singleton AgentOrchestrator terug."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
