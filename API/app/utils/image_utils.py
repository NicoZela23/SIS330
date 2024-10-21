import io
from PIL import Image
import torchvision.transforms as transforms

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(256),
    transforms.ToTensor(),
])

async def transform_image(file):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert('RGB')
    return transform(image)
