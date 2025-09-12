# Models Directory

This directory contains trained model checkpoints and related files.

## Structure

```
models/
├── checkpoints/           # Training checkpoints
│   ├── unet_v1/          # UNet model versions
│   ├── swin_transformer/ # Swin Transformer models
│   └── ensemble/         # Ensemble models
├── final/                # Production-ready models
│   ├── tumor_detection_v1.pth
│   ├── tumor_segmentation_v1.pth
│   └── model_metadata.json
├── experiments/          # Experimental models
└── pretrained/          # Pre-trained base models
```

## Model Types

### Tumor Detection Models
- **UNet 3D**: Primary segmentation architecture
- **Swin Transformer**: Vision transformer for medical imaging
- **Ensemble Models**: Combined predictions from multiple models

### Model Formats
- **PyTorch (.pth)**: Native PyTorch format
- **ONNX (.onnx)**: Cross-platform deployment
- **TorchScript (.pt)**: Optimized for production

## Model Metadata

Each model includes:
- Training configuration
- Performance metrics
- Dataset information
- Version history
- Deployment instructions

## Model Versioning

Format: `{model_type}_v{major}.{minor}.{patch}`

Example:
- `tumor_detection_v1.0.0` - Initial release
- `tumor_detection_v1.1.0` - Improved accuracy
- `tumor_detection_v2.0.0` - Architecture change

## Performance Benchmarks

### Current Best Models

| Model | Dice Score | Sensitivity | Specificity | Inference Time |
|-------|------------|-------------|-------------|----------------|
| UNet 3D v1.0 | 0.85 | 0.89 | 0.92 | 2.3s |
| Swin-T v1.0 | 0.87 | 0.91 | 0.94 | 3.1s |
| Ensemble v1.0 | 0.89 | 0.93 | 0.95 | 5.8s |

## Usage

### Loading Models in Code

```python
import torch
from src.inference.inference import TumorPredictor

# Load production model
predictor = TumorPredictor('models/final/tumor_detection_v1.pth')

# Load specific checkpoint
model = torch.load('models/checkpoints/unet_v1/epoch_50.pth')
```

### Configuration

Update `config.json` to specify model paths:

```json
{
  "model_path": "models/final/tumor_detection_v1.pth",
  "model_type": "unet_3d",
  "model_version": "1.0.0"
}
```

## Model Training

### Training New Models

```bash
# Train from scratch
python src/training/train.py --config config.json

# Resume from checkpoint
python src/training/train.py --resume models/checkpoints/unet_v1/epoch_30.pth
```

### Model Evaluation

```bash
# Evaluate on test set
python src/evaluation/evaluate.py --model models/final/tumor_detection_v1.pth
```

## Deployment

### Production Deployment
1. Validate model performance on test set
2. Convert to optimized format (TorchScript/ONNX)
3. Update production configuration
4. Deploy with proper monitoring

### Model Serving
- REST API via FastAPI backend
- Real-time inference through web interface
- Batch processing for research workflows

## Model Registry

Track all models with:
- Performance metrics
- Training parameters
- Data provenance
- Validation results
- Deployment history

## Security

- Models are excluded from version control due to size
- Use secure model storage for production
- Implement model signing and verification
- Regular security audits of model artifacts

## Model Lifecycle

1. **Development**: Experimental training and validation
2. **Testing**: Comprehensive evaluation on test sets
3. **Staging**: Pre-production validation
4. **Production**: Live deployment with monitoring
5. **Retirement**: Archival of outdated models

For questions about model management, contact the project maintainers.
