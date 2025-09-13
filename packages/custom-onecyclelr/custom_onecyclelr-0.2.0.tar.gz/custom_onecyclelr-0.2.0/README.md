
# OneCycle Learning Rate Scheduler

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI - Version](https://img.shields.io/pypi/v/custom-onecyclelr)](https://pypi.org/project/custom-onecyclelr/)

A custom implementation of the OneCycle learning rate scheduler for PyTorch.

## Features
- Customized version of the OneCycleLR algorithm with four distinct phases: warmup, idling, annealing, and decay.
- Flexibility in defining various hyperparameters such as:
  - Warmup iterations and type (linear or exponential)
  - Idling period duration
  - Annealing phase duration and minimum learning rate
  - Decay phase duration and minimum learning rate
- Compatibility with any PyTorch optimizer

## Installation

```bash
pip install custom-onecyclelr
```

## Usage

Here's an example of how to integrate the scheduler into your training loop:

```python
import torch
from custom_onecyclelr import scheduler

# Initialize model and optimizer
model = YourModel()
optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)

# Create the OneCycleLR scheduler with desired parameters
scheduler_instance = scheduler.OneCycleLr(
    optimizer,
    warmup_iters=6,  # Number of iterations for the warmup phase
    lr_idling_iters=8,  # Number of iterations where learning rate remains at max
    annealing_iters=56,  # Cosine annealing phase duration
    decay_iters=100,  # Linear decay phase duration
    max_lr=0.01,
    annealing_lr_min=0.001,
    decay_lr_min=0.0001,
    warmup_start_lr=0.0001,
    warmup_type="exp"  # "linear" or "exp"
)

# You can also use the config_helper function to simplify the configuration (works best for higher total iterations)
# from custom_onecyclelr import config
# scheduler_instance = scheduler.OneCycleLr(
#     optimizer,
#     config.config_helper(200, 0.008)
# )

# Training loop
for epoch in range(total_epochs):
    for inputs, targets in dataloader:
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        scheduler_instance.step()

```

## Visualization

![Visualization-img](https://github.com/AidinHamedi/Custom-OneCycleLr-Pytorch/blob/master/doc/vis/onecycle_lr_schedule.png?raw=true)

You can visualize how the learning rate changes over iterations by running:

```bash
python examples/vis.py
```

This will generate a plot showing the different phases of the learning rate schedule.

## License

This project is licensed under MIT License - see [LICENSE](LICENSE) for details.
