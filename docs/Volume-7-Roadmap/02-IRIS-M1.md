# IRIS M1

## Purpose
Define the IRIS M1 model specification — the first fine-tuned model optimized specifically for IRIS use cases, personality, and privacy requirements.

## Responsibilities
- Define model architecture and training data requirements
- Specify fine-tuning objectives and datasets
- Establish quality benchmarks and acceptance criteria
- Guide deployment and optimization strategy

## Design Goals
- **Optimized**: Fine-tuned for IRIS-specific use cases
- **Efficient**: Runs on consumer hardware (8GB+ VRAM)
- **Personality-aligned**: Trained to match IRIS modes and tone
- **Privacy-aware**: Trained to route privacy-sensitive queries correctly

## Architecture
```
Base Model (LLaMA 3.2 8B) → Fine-tuning → IRIS M1
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                              ▼
             Supervised Fine-Tuning          RLHF / DPO
                     │                              │
                     └──────────────┬──────────────┘
                                    ▼
                            IRIS M1 Model
```

## Components

### Base Model Selection
| Criteria | Target |
|----------|--------|
| Architecture | LLaMA 3.2 8B |
| License | Open (MIT or similar) |
| Context window | 128K tokens |
| Language | English (primary) |
| Hardware | 8GB+ VRAM, 16GB+ RAM |

### Training Objectives
- **Personality alignment**: Consistent with 5 IRIS modes
- **Privacy awareness**: Recognize sensitive topics
- **Tool use**: Proper function calling for skills
- **Memory-aware**: Reference past context naturally
- **Safety**: Refuse harmful requests

### Datasets
- **Synthetic**: Generated conversation data for each mode
- **Tool use**: Function calling examples
- **Personality**: Mode-specific dialogue pairs
- **Safety**: Harmful request refusal training

## Data Flow
Base Model → Data Preparation → SFT → RLHF → Evaluation → Quantization → Deployment

## Public Interfaces
- `GET /models/m1/info` → M1 model metadata
- `POST /models/m1/download` → Download M1 model
- `GET /models/m1/benchmark` → M1 benchmark results

## Configuration
- Model path: `~/.iris/models/iris-m1/`
- Quantization: `q4_k_m` (default, 4-bit)
- Minimum hardware: 8GB VRAM, 16GB RAM

## Dependencies
- Base model (LLaMA 3.2 8B or equivalent)
- Training infrastructure (GPU cluster)
- Fine-tuning framework (Axolotl, Unsloth)
- Evaluation framework

## Security Considerations
- Training data is curated to remove PII
- Model is tested for harmful outputs before release
- Model weights are checksum-verified after download
- Safety guardrails are applied at inference layer

## Failure Recovery
- Training divergence → restore from checkpoint
- Quality regression → revert to base model
- Hardware requirement too high → explore smaller base

## Future Improvements
- M1.1: Incorporate user feedback
- M1.2: Multi-lingual support
- M1.3: Reduced quantization loss

## Engineering Notes
Fine-tuning quality depends on data quality. Invest in synthetic data generation pipeline.

## Acceptance Criteria
- M1 outperforms base model on IRIS-specific benchmarks
- Model runs on target hardware (8GB VRAM)
- Personality alignment is measurably better
- No regression on general capabilities
- Model passes safety evaluation suite

## References
- Volume-7-Roadmap/03-Foundation-Model.md
- Volume-4-Infrastructure/01-Model-Registry.md
- Volume-4-Infrastructure/02-Model-Benchmark-System.md
