#!/usr/bin/env python3
"""
Interactieve agent-test CLI voor VorstersNV.
Test agents lokaal zonder de volledige applicatie te starten.
Gebruik: python scripts/test_agent.py --agent klantenservice_agent
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ollama.agent_runner import AgentRunner
from ollama.prompt_iterator import PromptIterator


async def interactive_chat(agent_name: str, runner: AgentRunner):
    """Start een interactief gesprek met een agent."""
    agent = runner.get(agent_name)
    if not agent:
        print(f"Agent '{agent_name}' niet gevonden.")
        print(f"Beschikbaar: {runner.list_agents()}")
        return

    iterator = PromptIterator(agent_name)
    history = []

    print(f"\n=== Agent: {agent_name} (model: {agent.model}) ===")
    print("Type 'stop' om te stoppen, 'feedback' om beoordeling te geven\n")

    last_interaction_id = None

    while True:
        try:
            user_input = input("U: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue
        if user_input.lower() == "stop":
            break
        if user_input.lower() == "feedback" and last_interaction_id:
            try:
                rating = int(input("Beoordeling (1-5): "))
                notes = input("Opmerkingen (optioneel): ")
                iterator.add_feedback(last_interaction_id, rating, notes)
                print("Feedback opgeslagen!")
            except ValueError:
                print("Ongeldige beoordeling")
            continue

        history.append({"role": "user", "content": user_input})

        print("Agent: ", end="", flush=True)
        response = await agent.chat(history)
        print(response)
        print()

        history.append({"role": "assistant", "content": response})

        # Log de interactie
        last_interaction_id = iterator.log_interaction(user_input, response)

    # Toon statistieken
    stats = iterator.analyse_feedback()
    print(f"\n=== Sessie statistieken voor {agent_name} ===")
    for key, value in stats.items():
        print(f"  {key}: {value}")


async def main():
    parser = argparse.ArgumentParser(description="Test een VorstersNV AI-agent")
    parser.add_argument(
        "--agent",
        required=True,
        help="Agent naam (bijv. klantenservice_agent)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Toon alle beschikbare agents",
    )
    args = parser.parse_args()

    runner = AgentRunner()

    if args.list:
        print("Beschikbare agents:")
        for name in runner.list_agents():
            print(f"  - {name}")
        return

    await interactive_chat(args.agent, runner)


if __name__ == "__main__":
    asyncio.run(main())
