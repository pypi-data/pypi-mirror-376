# Changelog

All notable changes to the tumor-detection-segmentation package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-09-11

### Added
- **PyPI Distribution**: Package now available on PyPI as `tumor-detection-segmentation`
- **First-class Python Package**: Complete package structure with proper imports and APIs
- **High-level Inference API**: `load_model()`, `run_inference()`, `save_mask()`, `generate_overlays()`
- **Configuration Management**: `load_recipe_config()` and `load_dataset_config()` utilities
- **Device Auto-detection**: Automatic CUDA/CPU/ROCm hardware detection
- **CLI Tools**: `tumor-detect-train` and `tumor-detect-infer` command-line interfaces
- **MONAI Dataset Integration**: Built-in Medical Segmentation Decathlon (MSD) support
- **Multi-modal AI Models**: UNETR, SegResNet, DiNTS implementations
- **Docker Deployment**: Complete containerized platform with web GUI
- **MLflow Integration**: Experiment tracking and model management
- **MONAI Label Server**: Interactive annotation with 3D Slicer compatibility
- **Advanced Training Features**: Mixed precision, test-time augmentation, overlay generation
- **Comprehensive Testing**: Unit, integration, and performance tests
- **Professional Documentation**: User guides, developer docs, API reference

### Changed
- **Project Organization**: Clean structure with organized subdirectories
- **Modern Build System**: Migrated to `hatchling` with `pyproject.toml`
- **Enhanced CI/CD**: Ruff/Black/Mypy linting, security scanning, SBOM generation

### Dependencies
- **Core**: PyTorch 1.12+, MONAI 1.3+, nibabel, numpy, scipy
- **Optional Extras**:
  - `[clinical]`: DICOM processing, FHIR compliance, report generation
  - `[gui]`: Streamlit, Plotly, Dash for web interfaces
  - `[api]`: FastAPI, Uvicorn for REST API services
  - `[dev]`: pytest, black, ruff, mypy for development
  - `[all]`: All optional dependencies

### Installation
```bash
# Basic installation
pip install tumor-detection-segmentation

# With clinical features
pip install tumor-detection-segmentation[clinical]

# Complete installation with all features
pip install tumor-detection-segmentation[all]

# Development installation
git clone https://github.com/hkevin01/tumor-detection-segmentation.git
cd tumor-detection-segmentation
pip install -e .[dev]
```

### Usage
```python
import tumor_detection

# Load model and run inference
model = tumor_detection.load_model("model.pth", "config.json")
prediction = tumor_detection.run_inference(model, "brain_scan.nii.gz")
tumor_detection.save_mask(prediction, "output_mask.nii.gz")
```

## [1.0.0] - 2025-09-01

### Added
- Initial release with core tumor detection and segmentation functionality
- Basic training and inference scripts
- Docker support
- MONAI integration
- Web GUI prototype

---

## Release Notes

### v2.0.0 Highlights

This major release transforms the project into a production-ready Python package available on PyPI. Key improvements:

- **Easy Installation**: `pip install tumor-detection-segmentation`
- **Professional APIs**: High-level functions for common tasks
- **Modular Design**: Optional dependencies for different use cases
- **Clinical Ready**: DICOM processing, FHIR compliance, report generation
- **Developer Friendly**: Modern tooling, comprehensive testing, detailed docs

### Upgrade Guide

For existing users, the new package provides backward compatibility while adding powerful new APIs. The Docker deployment remains unchanged, but you can now also install and use the package directly in your Python environment.

### Community

- **Documentation**: https://github.com/hkevin01/tumor-detection-segmentation/docs
- **Issues**: https://github.com/hkevin01/tumor-detection-segmentation/issues
- **Discussions**: https://github.com/hkevin01/tumor-detection-segmentation/discussions

### Citation

```bibtex
@software{tumor_detection_segmentation_2025,
  title={Medical Imaging AI Platform for Tumor Detection and Segmentation},
  author={Medical Imaging AI Team},
  year={2025},
  url={https://github.com/hkevin01/tumor-detection-segmentation},
  version={2.0.0}
}
```
