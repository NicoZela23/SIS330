import io
from PIL import Image
import torchvision.transforms as transforms

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

async def transform_image(file):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert('RGB')
    return transform(image)