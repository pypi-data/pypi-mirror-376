from .base_agent import BaseAgent

class ActionAgent(BaseAgent):
    def __init__(self):
        super().__init__("ActionAgent")

    def process(self, data: dict) -> dict:
        code = data.get("code", "")
        if not code:
            return {"plan": "No code to execute"}
        try:
            local_env = {}
            exec(code, {}, local_env)
            return {"plan": "Executed code", "output": local_env}
        except Exception as e:
            return {"plan": "Execution failed", "error": str(e)}
