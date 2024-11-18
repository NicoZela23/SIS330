# models/ai_model.py
import torch
import torch.nn as nn
import torchvision
from typing import Tuple

class CAM(nn.Module):
    def __init__(self):
        super(CAM, self).__init__()
        self.net = torchvision.models.resnet18(pretrained=True)
        self.net.fc = nn.Linear(in_features=512, out_features=4, bias=False)
    
    def forward(self, x) -> Tuple[torch.Tensor, torch.Tensor]:
        x = self.net.conv1(x)
        x = self.net.bn1(x)
        x = self.net.relu(x)
        x = self.net.maxpool(x)
        x = self.net.layer1(x)
        x = self.net.layer2(x)
        x = self.net.layer3(x)
        x = self.net.layer4(x)
        conv_features = x
        x = self.net.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.net.fc(x)
        return conv_features, x