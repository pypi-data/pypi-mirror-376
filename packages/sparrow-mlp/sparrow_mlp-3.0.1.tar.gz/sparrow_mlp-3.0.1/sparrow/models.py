# sparrow/models.py

import torch
import torch.nn as nn
import torch.nn.functional as F
from .layers import MoELayer
from .config import SparrowConfig

class DynamicMLP(nn.Module):
    """
    مدل اصلی پرسپترون چندلایه دینامیک.
    """
    def __init__(self, input_size: int, output_size: int, config: SparrowConfig):
        super().__init__()
        self.config = config
        
        self.input_layer = nn.Linear(input_size, config.hidden_dim)
        self.hidden_layers = nn.ModuleList([MoELayer(config) for _ in range(config.num_hidden_layers)])
        self.layer_router = nn.Linear(config.hidden_dim, config.num_hidden_layers)
        self.output_layer = nn.Linear(config.hidden_dim, output_size)
        
        self.layer_gates_values = None
        self.total_balancing_loss = 0.0
        self.total_entropy = 0.0

    def forward(self, x):
        x = F.relu(self.input_layer(x))
        layer_gates_logits = self.layer_router(x)
        layer_gates = torch.sigmoid(layer_gates_logits)
        
        if self.training:
            self.layer_gates_values = layer_gates.mean(dim=0)
            self.total_balancing_loss = 0.0
            self.total_entropy = 0.0

        for i, layer in enumerate(self.hidden_layers):
            gate = layer_gates[:, i].unsqueeze(1)
            layer_output, balancing_loss, entropy = layer(x)
            
            if self.training:
                self.total_balancing_loss += balancing_loss
                self.total_entropy += entropy
                
            x = x + gate * layer_output
        
        return self.output_layer(x)