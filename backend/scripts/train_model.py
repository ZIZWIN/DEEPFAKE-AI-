# ==============================================================================
# DEEPFAKE DATASET DOWNLOAD AND PREPARATION INFORMATION
#
# 1. FaceForensics++ (FF++)
#    - Official URL: https://github.com/ondyari/FaceForensics
#    - Description: Large-scale dataset containing manipulated face videos.
#    - Download Instruction: Run the official script provided in their repo.
#
# 2. Celeb-DF (v2)
#    - Official URL: https://github.com/yuezunli/Celeb-DF-v2
#    - Description: High-quality deepfake video dataset.
#    - Download Instruction: Request access via the official form in the repo.
#
# 3. Deepfake Detection Challenge (DFDC)
#    - Official URL: https://www.kaggle.com/c/deepfake-detection-challenge
#    - Description: Large dataset sponsored by Meta and others.
#    - Download Instruction: Download using the Kaggle API or direct download.
# ==============================================================================

import os # Import os module to check directory structure and file paths.
import torch # Import PyTorch for tensor calculations, loss functions, and weights management.
import torch.nn as nn # Import PyTorch neural network modules for loss definitions.
import torch.optim as optim # Import PyTorch optimization algorithms like AdamW.
from torch.utils.data import Dataset, DataLoader # Import Dataset and DataLoader for PyTorch batch processing.
from PIL import Image # Import Pillow Image class to load training images.
import torchvision.transforms as transforms # Import torchvision transforms to apply augmentations.
import timm # Import timm library to fetch EfficientNet-B4 pre-trained model.

# Dataset path configurations (commented out per requirements):
# DATASET_PATH = "/data/ff++/frames" # FaceForensics++ frame storage path.
# DATASET_PATH = "/data/celebdf/frames" # Celeb-DF v2 frame storage path.
# DATASET_PATH = "/data/dfdc/frames" # Deepfake Detection Challenge frame storage path.

class DeepfakeDataset(Dataset): # Define the custom Dataset subclass for Deepfake frames.
    def __init__(self, root_dir: str, transform: transforms.Compose | None = None) -> None: # Initialize dataset parameters.
        self.root_dir = root_dir # Store the root directory path for images.
        self.transform = transform # Store the transform pipeline.
        self.samples = [] # Initialize empty samples list.
        
        real_dir = os.path.join(root_dir, "real") # Construct path to authentic images directory.
        if os.path.exists(real_dir): # Check if the real folder exists on the disk.
            for file in os.listdir(real_dir): # Loop over files in the real directory.
                if file.lower().endswith((".jpg", ".jpeg", ".png")): # Filter files by image extensions.
                    self.samples.append((os.path.join(real_dir, file), 0)) # Add tuple of (filepath, label 0 for real).
                    
        fake_dir = os.path.join(root_dir, "fake") # Construct path to manipulated images directory.
        if os.path.exists(fake_dir): # Check if the fake folder exists on the disk.
            for file in os.listdir(fake_dir): # Loop over files in the fake directory.
                if file.lower().endswith((".jpg", ".jpeg", ".png")): # Filter files by image extensions.
                    self.samples.append((os.path.join(fake_dir, file), 1)) # Add tuple of (filepath, label 1 for fake).

    def __len__(self) -> int: # Return the total number of samples.
        return len(self.samples) # Return sample list size.

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]: # Retrieve a specific sample by index.
        img_path, label = self.samples[idx] # Extract filepath and label from the samples list at index.
        img = Image.open(img_path).convert("RGB") # Load the image using PIL and convert it to RGB format.
        if self.transform: # If a transform pipeline is provided, apply it.
            img = self.transform(img) # Preprocess the image.
        return img, label # Return the preprocessed tensor and label.

def train() -> None: # Define the main training execution loop function.
    train_transform = transforms.Compose([ # Compose augmentation transformations for training dataset.
        transforms.Resize((224, 224)), # Resize input image to 224x224 dimensions.
        transforms.RandomHorizontalFlip(), # Randomly flip image horizontally for data augmentation.
        transforms.ColorJitter(brightness=0.2, contrast=0.2), # Jitter brightness and contrast by 0.2.
        transforms.ToTensor(), # Convert PIL Image to PyTorch Tensor format.
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]) # Normalize using ImageNet statistics.
    ]) # End transformations block.

    # Modify the dataset path as needed based on where frames are extracted:
    dataset = DeepfakeDataset(root_dir="frames", transform=train_transform) # Instantiate the custom dataset from frames folder.
    if len(dataset) == 0: # Check if dataset is empty.
        print("Warning: Dataset is empty. Place your training images under frames/real/ and frames/fake/") # Warn about empty dataset folder.
        return # Return early to prevent division by zero errors in training.

    dataloader = DataLoader(dataset, batch_size=32, shuffle=True) # Create dataloader with batch size 32 and shuffling enabled.
    model = timm.create_model("efficientnet_b4", pretrained=True, num_classes=2) # Load pre-trained EfficientNet-B4 model with 2 classes.
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu") # Check for CUDA availability and select device.
    model.to(device) # Move the neural network to target training device.
    
    criterion = nn.CrossEntropyLoss() # Define cross-entropy loss function.
    optimizer = optim.AdamW(model.parameters(), lr=1e-4) # Setup AdamW optimizer with a learning rate of 0.0001.

    print("Starting training loop for 10 epochs...") # Print startup message for training.
    for epoch in range(10): # Train for 10 epochs.
        model.train() # Put model in training mode to update batch norm and enable dropout.
        running_loss = 0.0 # Reset epoch running loss accumulator.
        for inputs, labels in dataloader: # Iterate over batch data.
            inputs, labels = inputs.to(device), labels.to(device) # Move batch data to CPU/GPU device.
            optimizer.zero_grad() # Clear gradients of optimized tensors.
            outputs = model(inputs) # Run forward pass through the model.
            loss = criterion(outputs, labels) # Calculate loss value.
            loss.backward() # Run backward pass to compute gradients.
            optimizer.step() # Update model parameter weights.
            running_loss += loss.item() * inputs.size(0) # Accumulate batch loss multiplied by batch size.
        epoch_loss = running_loss / len(dataset) # Calculate average epoch loss.
        print(f"Epoch {epoch + 1}/10 - Loss: {epoch_loss:.4f}") # Print loss for the current epoch.

    os.makedirs("weights", exist_ok=True) # Create weights directory if it doesn't already exist.
    torch.save(model.state_dict(), "weights/efficientnet_ff++.pth") # Save trained model state dictionary to weights folder.
    print("Model weights successfully saved to weights/efficientnet_ff++.pth") # Print successful save message.

if __name__ == "__main__": # Execute code when run directly as a script.
    train() # Run the training script function.
