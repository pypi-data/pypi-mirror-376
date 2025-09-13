WARMUP = 0.05
IDLING = 0.40
ANNEALING = 0.30

WARMUP_START_LR_FACTOR = 0.01
ANNEALING_LR_MIN_FACTOR = 0.2
DECAY_LR_MIN_FACTOR = 0.005


def config_helper(total_iters: int, max_lr: float, verbose: bool = False):
    warmup_iters = int(total_iters * WARMUP)
    lr_idling_iters = int(total_iters * IDLING)
    annealing_iters = int(total_iters * ANNEALING)
    decay_iters = total_iters - (warmup_iters + lr_idling_iters + annealing_iters)

    warmup_start_lr = max_lr * WARMUP_START_LR_FACTOR
    annealing_lr_min = max_lr * ANNEALING_LR_MIN_FACTOR
    decay_lr_min = max_lr * DECAY_LR_MIN_FACTOR

    if verbose:
        print(f"[LearningRate-Scheduler] Total iterations: {total_iters}")
        print(f"[LearningRate-Scheduler] Warmup iterations: {warmup_iters}")
        print(f"[LearningRate-Scheduler] LR idling iterations: {lr_idling_iters}")
        print(f"[LearningRate-Scheduler] Annealing iterations: {annealing_iters}")
        print(f"[LearningRate-Scheduler] Decay iterations: {decay_iters}")
        print(f"[LearningRate-Scheduler] Max LR: {max_lr}")
        print(f"[LearningRate-Scheduler] Warmup start LR: {warmup_start_lr}")
        print(f"[LearningRate-Scheduler] Annealing LR min: {annealing_lr_min}")
        print(f"[LearningRate-Scheduler] Decay LR min: {decay_lr_min}")

    return {
        "warmup_iters": warmup_iters,
        "lr_idling_iters": lr_idling_iters,
        "annealing_iters": annealing_iters,
        "decay_iters": decay_iters,
        "max_lr": max_lr,
        "warmup_start_lr": warmup_start_lr,
        "annealing_lr_min": annealing_lr_min,
        "decay_lr_min": decay_lr_min,
    }
