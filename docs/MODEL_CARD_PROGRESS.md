# Model Card: Physical Progress Vision Architecture

## Model Details
- **Model Name:** PhysicalProgressEstimator
- **Model Version:** 1.0.0-interface
- **Architecture:** Multi-head Structural Component Detector (YOLO/ResNet/ViT compatible interface)
- **Status:** Interface specified; marked `MODEL_NOT_TRAINED` until domain-specific annotated construction drone/ground dataset is mounted.

## Intended Use
- Detect visible structural milestones (e.g. `foundation`, `columns`, `walls`, `roof`, `asphalt`, `markings`) from georeferenced inspection photos to infer observed physical progress percentage.

## Integrity Standard
- If no verified field photograph exists for a project, the system outputs:
  `observed_progress: null`
  `observed_progress_status: NOT_AVAILABLE`
- The system NEVER manufactures fake confidence or synthesizes mock percentage detections.

## Disclaimer
"AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."
