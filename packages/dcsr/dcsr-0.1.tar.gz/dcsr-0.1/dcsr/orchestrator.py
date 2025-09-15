from .agents.language_agent import LanguageAgent
from .agents.logic_agent import LogicAgent
from .agents.perception_agent import PerceptionAgent
from .agents.action_agent import ActionAgent


class Orchestrator:
    def __init__(self):
        # built-in agents
        self.agents = {
            "language": LanguageAgent(),
            "logic": LogicAgent(),
            "perception": PerceptionAgent(),
            "action": ActionAgent(),
        }

    def add_agent(self, name: str, agent) -> None:
        """
        Register a new agent dynamically (used by addons).
        If the name already exists, it will be overwritten.
        """
        self.agents[name] = agent

    def handle_query(self, query: str = None, image: str = None, code: str = None) -> dict:
        reasoning_path = []

        for name, agent in self.agents.items():
            if not hasattr(agent, "process"):
                continue

            try:
                if query:
                    output = agent.process({"query": query})
                    reasoning_path.append((getattr(agent, "name", name), output))
                if image:
                    output = agent.process({"image": image})
                    reasoning_path.append((getattr(agent, "name", name), output))
                if code:
                    output = agent.process({"code": code})
                    reasoning_path.append((getattr(agent, "name", name), output))
            except Exception as e:
                reasoning_path.append((name, f"[ERROR] {e}"))

        return {"reasoning_path": reasoning_path}
