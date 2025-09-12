# Data Directory

This directory contains medical imaging datasets for tumor detection and segmentation.

## ⚠️ IMPORTANT: Medical Data Privacy

**NEVER commit patient data to version control!**

This directory is included in `.gitignore` to prevent accidental commits of sensitive medical information.

## Structure

```
data/
├── raw/                    # Original DICOM files
│   ├── train/             # Training dataset
│   ├── validation/        # Validation dataset
│   └── test/              # Test dataset
├── processed/             # Preprocessed data
│   ├── train/
│   ├── validation/
│   └── test/
└── annotations/           # Ground truth labels
    ├── train/
    ├── validation/
    └── test/
```

## Data Format

- **Input**: DICOM files (.dcm)
- **Labels**: NIfTI format (.nii.gz) or DICOM SEG
- **Metadata**: JSON files with study information

## Dataset Requirements

### Training Data
- Minimum 100 studies for initial training
- Balanced dataset with positive/negative cases
- Multiple imaging modalities (CT, MRI) recommended

### Validation Data
- 20-30% of total dataset
- Representative of real-world distribution
- Independent from training data

### Test Data
- Hold-out dataset for final evaluation
- Never used during training or hyperparameter tuning

## Data Preprocessing

The system automatically handles:
- DICOM metadata extraction
- Image normalization and resampling
- Data augmentation for training
- Format conversion for ML pipelines

## Adding New Data

1. Place DICOM files in appropriate subdirectories
2. Ensure proper anonymization (PHI removal)
3. Verify data integrity with validation scripts
4. Update dataset configuration in `config.json`

## Privacy and Compliance

- All data must be properly anonymized
- Follow HIPAA guidelines for medical data
- Implement data use agreements as required
- Regular audits of data access and usage

## Data Sources

Document approved data sources:
- [ ] Internal hospital systems
- [ ] Public datasets (TCIA, etc.)
- [ ] Research collaborations
- [ ] Synthetic data generation

For questions about data management, contact the project maintainers.
