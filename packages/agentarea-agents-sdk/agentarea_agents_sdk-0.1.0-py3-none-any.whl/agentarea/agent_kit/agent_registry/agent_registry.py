"""In-memory agent registry implementation."""

import uuid

from ..interfaces import IAgentRegistry


class InMemoryAgentRegistry(IAgentRegistry):
    """In-memory implementation of agent registry."""

    def __init__(self):
        self._entities: dict[uuid.UUID, dict] = {}
        self._capability_index: dict[
            str, list[uuid.UUID]
        ] = {}  # For efficient capability-based lookup for agents

    def register_agent(
        self,
        agent_id: uuid.UUID,
        name: str,
        instruction: str,
        network_id: uuid.UUID | None = None,
        capabilities: list[str] = None,
    ) -> bool:
        """Register a new agent or update existing."""
        entity_data = {
            "type": "agent",
            "id": agent_id,
            "name": name,
            "instruction": instruction,
            "network_id": network_id,
            "capabilities": capabilities or [],
            "role": None,  # Can be derived from capabilities or set explicitly
        }
        self._entities[agent_id] = entity_data

        # Update capability index for agents only
        for cap in capabilities or []:
            if cap not in self._capability_index:
                self._capability_index[cap] = []
            if agent_id not in self._capability_index[cap]:
                self._capability_index[cap].append(agent_id)

        return True

    def get_agent(self, agent_id: uuid.UUID) -> dict | None:
        """Get agent details by ID."""
        entity = self._entities.get(agent_id)
        if entity and entity["type"] == "agent":
            return entity
        return None

    def list_agents(
        self,
        role: str | None = None,
        network_id: uuid.UUID | None = None,
        task_filter: str | None = None,
    ) -> list[dict]:
        """List registered agents, optionally filtered by role, network, or task."""
        entities = [e for e in self._entities.values() if e["type"] == "agent"]
        if network_id:
            entities = [e for e in entities if e.get("network_id") == network_id]
        if role:
            entities = [e for e in entities if role in e["capabilities"]]
        if task_filter:
            # Simple keyword filter: match task_filter in capabilities or instruction
            entities = [
                e
                for e in entities
                if task_filter.lower() in " ".join(e["capabilities"] + [e["instruction"]]).lower()
            ]
        return entities

    def unregister_agent(self, agent_id: uuid.UUID) -> bool:
        """Unregister an agent."""
        entity = self._entities.get(agent_id)
        if entity and entity["type"] == "agent":
            for cap in entity["capabilities"]:
                if cap in self._capability_index:
                    self._capability_index[cap] = [
                        aid for aid in self._capability_index[cap] if aid != agent_id
                    ]
            del self._entities[agent_id]
            return True
        return False

    def get_agent_for_task(
        self, task_description: str, enable_dynamic_discovery: bool = False
    ) -> dict | None:
        """Get an entity (agent or network) suitable for the task, with optional dynamic discovery."""
        if enable_dynamic_discovery:
            # For dynamic: Use simple keyword matching to find best entity
            keywords = task_description.lower().split()
            best_entity = None
            best_match_count = 0
            for entity in self.list_entities(task_filter=task_description):
                # For networks, match on name or assume networks have capabilities (extend later)
                if entity["type"] == "network":
                    # Simple: match on name
                    match_count = sum(1 for kw in keywords if kw in entity["name"].lower())
                else:
                    # Match on capabilities and instruction
                    entity_text = " ".join(
                        entity["capabilities"] + [entity.get("instruction", "")]
                    ).lower()
                    match_count = sum(1 for kw in keywords if kw in entity_text)
                if match_count > best_match_count:
                    best_match_count = match_count
                    best_entity = entity
            return (
                best_entity
                if best_entity
                else list(reversed(list(self._entities.values())))[0]
                if self._entities
                else None
            )
        else:
            # Static: Find agent with matching capabilities using partial matching
            keywords = task_description.lower().split()
            for kw in keywords:
                for cap in self._capability_index:
                    if kw in cap or cap in kw:
                        agent_id = self._capability_index[cap][0]
                        return self.get_agent(agent_id)
            return None

    def register_network(
        self, network_id: uuid.UUID, agents: list[uuid.UUID], orchestrator_id: uuid.UUID
    ) -> bool:
        """Register a network of agents."""
        entity_data = {
            "type": "network",
            "id": network_id,
            "agents": agents,
            "orchestrator_id": orchestrator_id,
            "name": f"Network {network_id}",  # Default name
            "capabilities": [],  # Can derive from members
        }
        self._entities[network_id] = entity_data
        return True

    def get_network(self, network_id: uuid.UUID) -> dict | None:
        """Get network details by ID."""
        entity = self._entities.get(network_id)
        if entity and entity["type"] == "network":
            return entity
        return None

    def list_entities(
        self,
        role: str | None = None,
        network_id: uuid.UUID | None = None,
        task_filter: str | None = None,
    ) -> list[dict]:
        """List all registered entities (agents and networks), optionally filtered."""
        entities = list(self._entities.values())
        if network_id:
            entities = [
                e
                for e in entities
                if e.get("network_id") == network_id
                or e["type"] == "network"
                and e["id"] == network_id
            ]
        if role:
            entities = [e for e in entities if role in e["capabilities"]]
        if task_filter:
            task_keywords = task_filter.lower().split()
            entities = [
                e
                for e in entities
                if any(
                    kw in (e["name"] + " " + e.get("instruction", "")).lower()
                    for kw in task_keywords
                )
            ]
        return entities
