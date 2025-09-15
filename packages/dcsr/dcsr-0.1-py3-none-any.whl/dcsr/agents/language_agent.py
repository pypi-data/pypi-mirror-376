from .base_agent import BaseAgent
from transformers import AutoTokenizer, AutoModel
import torch

class LanguageAgent(BaseAgent):
    def __init__(self, model_name="distilbert-base-uncased"):
        super().__init__("LanguageAgent")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def process(self, data: dict) -> dict:
        text = data.get("query", "")
        tokens = self.tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            embedding = self.model(**tokens).last_hidden_state.mean(dim=1).squeeze().tolist()
        return {"embedding": embedding, "tokens": self.tokenizer.convert_ids_to_tokens(tokens["input_ids"][0])}
