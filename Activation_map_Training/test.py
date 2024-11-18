from torch.utils.data import Dataset, DataLoader
import torch
import os
from torchvision import transforms
from PIL import Image
import numpy as np
from skimage import io
import random
import matplotlib.pyplot as plt
import torchvision
from torch import nn
from tqdm.notebook import tqdm
from IPython import display
import sys
import cv2

class CAM(nn.Module):
    def __init__(self):
        super(CAM, self).__init__()
        self.net = torchvision.models.resnet18(pretrained=True)
        self.net.fc = nn.Linear(in_features=512, out_features=4, bias=False)
    
    def forward(self, x):
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

# Initialize model and transformations
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
net = CAM().to(device)
net.load_state_dict(torch.load('Activation_map_Training\model_for_cam.pth'))
net.eval()

# Define the image transformation for each frame
transform = transforms.Compose([
    transforms.Resize((344, 512)),
    transforms.ToTensor(),
])

# Define a real-time processing function
def process_frame(frame, label=2):
    # Convert OpenCV frame (BGR format) to PIL image and apply transformations
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB
    pil_image = Image.fromarray(frame_rgb)
    input_tensor = transform(pil_image).unsqueeze(0).to(device)  # Transform and add batch dimension
    
    with torch.no_grad():
        # Forward pass through the model
        conv, _ = net(input_tensor)
        
        # Generate CAM
        cam = (net.net.fc.weight[label][:, None, None].abs() * conv[0].abs()).sum(0)
        cam = cam.cpu().numpy()
        cam -= cam.min()
        cam /= cam.max()
        cam = (cam * 255).astype(np.uint8)
        
        # Resize CAM to match frame size
        h, w = frame.shape[:2]
        cam_resized = cv2.resize(cam, (w, h))
        
        # Apply heatmap
        heatmap = cv2.applyColorMap(cam_resized, cv2.COLORMAP_JET)
        
        # Blend heatmap with original frame
        blended_frame = cv2.addWeighted(frame, 0.6, heatmap, 0.4, 0)
        
        return blended_frame


# Open a video feed or receive images in real-time
cap = cv2.VideoCapture(0)  # Use 0 for the default camera

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Process each frame in real-time
    heatmap_frame = process_frame(frame)
    
    # Display the heatmap (for testing, can be removed in deployment)
    cv2.imshow("Real-Time Heatmap", heatmap_frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
