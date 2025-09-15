from .base_agent import BaseAgent
from torchvision import models, transforms
from PIL import Image
import torch

class PerceptionAgent(BaseAgent):
    def __init__(self):
        super().__init__("PerceptionAgent")
        self.model = models.resnet18(weights="IMAGENET1K_V1")
        self.model.eval()
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406],
                                 [0.229, 0.224, 0.225])
        ])
        from torchvision.models import ResNet18_Weights
        self.labels = ResNet18_Weights.IMAGENET1K_V1.meta["categories"]

    def process(self, data: dict) -> dict:
        path = data.get("image")
        if not path:
            return {"reasoning": "No image provided"}
        img = Image.open(path).convert("RGB")
        x = self.transform(img).unsqueeze(0)
        with torch.no_grad():
            logits = self.model(x)
        idx = logits.argmax().item()
        return {"label": self.labels[idx]}
