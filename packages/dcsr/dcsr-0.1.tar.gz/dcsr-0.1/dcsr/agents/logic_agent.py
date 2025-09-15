from .base_agent import BaseAgent
import sympy as sp

class LogicAgent(BaseAgent):
    def __init__(self):
        super().__init__("LogicAgent")

    def process(self, data: dict) -> dict:
        query = data.get("query", "")
        try:
            expr = sp.sympify(query)
            result = expr.evalf()
            return {"reasoning": "Symbolic evaluation", "result": str(result)}
        except Exception:
            return {"reasoning": "No symbolic match", "result": None}
