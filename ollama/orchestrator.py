"""
VorstersNV Multi-Agent Orchestrator
Coördineert meerdere AI-agents in gedefinieerde workflows.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from .agent_runner import AgentRunner, get_runner

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorStep:
    """Een stap in een orchestratie-workflow."""
    agent_name: str
    description: str
    context_key: str = ""  # Sleutel om output op te slaan in context
    required: bool = True  # Als False, ga door ook bij fout
    condition_key: str = ""  # Sla stap over als context[condition_key] ontbreekt


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
    ) -> OrchestratorResult:
        """
        Voer een multi-step workflow uit.

        Args:
            workflow_name: Naam van de workflow (voor logging)
            steps: Lijst van te uitvoeren stappen
            initial_input: Initiële input voor de eerste agent
            shared_context: Gedeelde context beschikbaar voor alle stappen

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
            # Sla stap over als een conditionele context-sleutel ontbreekt
            if step.condition_key and step.condition_key not in context:
                logger.info(
                    "Stap %d/%d overgeslagen (conditie '%s' niet aanwezig)",
                    i + 1, len(steps), step.condition_key,
                )
                result.steps_total -= 1
                continue

            logger.info(
                "Stap %d/%d: agent='%s' – %s",
                i + 1, len(steps), step.agent_name, step.description,
            )
            try:
                output, interaction_id = await self._runner.run_agent(
                    agent_name=step.agent_name,
                    user_input=current_input,
                    context=context,
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
            "Workflow '%s' klaar: %d/%d stappen, succes=%s",
            workflow_name,
            result.steps_completed,
            result.steps_total,
            result.success,
        )
        return result

    async def run_product_publishing_workflow(
        self,
        product_naam: str,
        categorie: str,
        kenmerken: list[str],
        doelgroep: str = "algemeen",
    ) -> OrchestratorResult:
        """
        Workflow: genereer productbeschrijving → optimaliseer voor SEO.

        Stap 1: product_beschrijving_agent – schrijft de tekst
        Stap 2: seo_agent – optimaliseert de tekst voor zoekmachines
        """
        steps = [
            OrchestratorStep(
                agent_name="product_beschrijving_agent",
                description="Productbeschrijving genereren",
                context_key="productbeschrijving",
            ),
            OrchestratorStep(
                agent_name="seo_agent",
                description="SEO-optimalisatie toepassen",
                context_key="seo_output",
                required=False,
            ),
        ]
        initial_input = (
            f"Schrijf een professionele productbeschrijving voor '{product_naam}'. "
            f"Categorie: {categorie}. Kenmerken: {', '.join(kenmerken)}. "
            f"Doelgroep: {doelgroep}."
        )
        return await self.run_workflow(
            workflow_name="product_publicatie",
            steps=steps,
            initial_input=initial_input,
            shared_context={
                "product_naam": product_naam,
                "categorie": categorie,
                "doelgroep": doelgroep,
            },
        )

    async def run_order_fulfillment_workflow(
        self,
        order_id: str,
        klant_naam: str,
        klant_email: str,
        producten: list[dict],
    ) -> OrchestratorResult:
        """
        Workflow: verwerk order → bevestig betaling → stuur notificatie.

        Stap 1: order_verwerking_agent – valideert en verwerkt de order
        Stap 2: klantenservice_agent – stelt klantvriendelijk bevestigingsbericht op
        """
        steps = [
            OrchestratorStep(
                agent_name="order_verwerking_agent",
                description="Order valideren en verwerken",
                context_key="order_verwerking",
            ),
            OrchestratorStep(
                agent_name="klantenservice_agent",
                description="Klantbevestiging opstellen",
                context_key="klant_bevestiging",
            ),
        ]
        initial_input = (
            f"Verwerk order {order_id} voor {klant_naam} ({klant_email}). "
            f"Producten: {producten}."
        )
        return await self.run_workflow(
            workflow_name="order_fulfillment",
            steps=steps,
            initial_input=initial_input,
            shared_context={
                "order_id": order_id,
                "klant_naam": klant_naam,
                "klant_email": klant_email,
            },
        )

    async def run_parallel(
        self,
        parallel_step: ParallelStep,
        shared_input: str,
        shared_context: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """
        Voer meerdere agent-stappen tegelijk uit (parallel).

        Args:
            parallel_step: De parallel-stap definitie
            shared_input: Gedeelde input voor alle agents
            shared_context: Gedeelde context voor alle agents

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
            output, _ = await self._runner.run_agent(
                agent_name=step.agent_name,
                user_input=shared_input,
                context=context,
            )
            return step.context_key or step.agent_name, output

        results = await asyncio.gather(
            *[_run_one(s) for s in parallel_step.steps],
            return_exceptions=True,
        )

        outputs: dict[str, str] = {}
        for step, result in zip(parallel_step.steps, results):
            if isinstance(result, Exception):
                logger.error("Parallelle stap '%s' mislukt: %s", step.agent_name, result)
                if step.required:
                    raise result
            else:
                key_out, output = result
                outputs[key_out] = output
                logger.info("Parallelle stap '%s' klaar (%d tekens)", step.agent_name, len(output))

        return outputs

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
        """
        Workflow: fraude-check → order verwerking → klantbevestiging (e-mail).

        Stap 1: fraude_detectie_agent – risicobeoordeling van de order
        Stap 2: order_verwerking_agent – verwerk de order (alleen bij laag/gemiddeld risico)
        Stap 3: email_template_agent – genereer orderbevestiging voor de klant
        """
        meta = klant_metadata or {}
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
            ),
            OrchestratorStep(
                agent_name="email_template_agent",
                description="Orderbevestiging genereren",
                context_key="bevestigings_email",
                required=False,
            ),
        ]
        initial_input = (
            f"Beoordeel order {order_id} voor klant {klant_naam} ({klant_email}). "
            f"Orderwaarde: €{orderwaarde}. Betaalmethode: {betaalmethode}. "
            f"Bezorgadres: {bezorgadres}."
        )
        return await self.run_workflow(
            workflow_name="order_met_fraude_check",
            steps=steps,
            initial_input=initial_input,
            shared_context={
                "order_id": order_id,
                "klant_naam": klant_naam,
                "klant_email": klant_email,
                "klant_id": klant_id,
                "orderwaarde": orderwaarde,
                "betaalmethode": betaalmethode,
                "bezorgadres": bezorgadres,
                "email_type": "orderbevestiging",
                **meta,
            },
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
    ) -> OrchestratorResult:
        """
        Workflow: retour beoordelen → e-mail sturen → voorraad bijwerken.

        Stap 1: retour_verwerking_agent – beoordeel en verwerk de retouraanvraag
        Stap 2: email_template_agent – genereer retourbevestiging voor de klant
        Stap 3: order_verwerking_agent – update orderstatus en voorraad
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
                "klant_email": klant_email,
                "retour_reden": retour_reden,
                "orderdatum": orderdatum,
                "ontvangstdatum": ontvangstdatum,
                "email_type": "retourbevestiging",
            },
        )

    async def run_voorraad_rapport_workflow(
        self,
        magazijn: str = "hoofdmagazijn",
    ) -> OrchestratorResult:
        """
        Workflow: analyseer voorraad → schrijf inkoopadvies e-mail.

        Stap 1: voorraad_advies_agent – genereer gedetailleerd besteladvies
        Stap 2: email_template_agent – schrijf inkoopadvies als e-mail voor inkoper
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
            },
        )


_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    """Geef de singleton AgentOrchestrator terug."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
