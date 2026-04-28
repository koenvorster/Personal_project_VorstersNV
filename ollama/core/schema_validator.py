"""
VorstersNV Agent Output Schema Validator
Valideert agent output tegen het output_schema gedeclareerd in agent YAML.
"""
import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def validate_output(
    output: str,
    schema: dict[str, Any],
    agent_name: str,
) -> dict[str, Any] | None:
    """
    Valideer agent output tegen zijn output_schema.

    Args:
        output: Ruwe tekst-output van de agent (kan JSON bevatten)
        schema: Het output_schema dict uit de agent YAML
        agent_name: Naam van de agent (voor logging)

    Returns:
        Gedeserialiseerd en gevalideerd dict als valide, None als validatie mislukt.
    """
    data = _extract_json(output)
    if data is None:
        logger.warning("Agent '%s': geen JSON gevonden in output", agent_name)
        return None

    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    # Controleer verplichte velden
    for field_name in required_fields:
        if field_name not in data:
            logger.warning(
                "Agent '%s': verplicht veld '%s' ontbreekt in output",
                agent_name, field_name,
            )
            return None

    # Type- en enum-validatie op gedeclareerde velden
    for field_name, field_schema in properties.items():
        if field_name not in data:
            continue
        value = data[field_name]
        expected_type = field_schema.get("type")
        enum_values = field_schema.get("enum")

        if expected_type == "integer" and not isinstance(value, int):
            try:
                data[field_name] = int(float(value))
                logger.debug(
                    "Agent '%s': veld '%s' gecoerceerd naar integer (%s → %d)",
                    agent_name, field_name, value, data[field_name],
                )
            except (ValueError, TypeError):
                logger.warning(
                    "Agent '%s': veld '%s' kan niet naar integer geconverteerd worden (waarde: %r)",
                    agent_name, field_name, value,
                )
                return None

        elif expected_type == "number" and not isinstance(value, (int, float)):
            try:
                data[field_name] = float(value)
            except (ValueError, TypeError):
                logger.warning(
                    "Agent '%s': veld '%s' kan niet naar number geconverteerd worden (waarde: %r)",
                    agent_name, field_name, value,
                )
                return None

        if enum_values and data[field_name] not in enum_values:
            logger.warning(
                "Agent '%s': veld '%s' waarde %r niet in toegestane waarden %s",
                agent_name, field_name, data[field_name], enum_values,
            )
            return None

    return data


def _extract_json(text: str) -> dict | None:
    """Extraheer het eerste JSON-object uit tekst (ook als er tekst omheen staat)."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None
