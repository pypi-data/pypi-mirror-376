from nnunetv2.training.nnUNetTrainer.variants.optimizer.nnUNetTrainerAdam import nnUNetTrainerAdam3en4
import torch

class NeuronSegBaseTrainer(nnUNetTrainerAdam3en4):
    pass

class NeuronSegBaseTrainerNoDeepSupervision(nnUNetTrainerAdam3en4):
    def __init__(
        self,
        plans: dict,
        configuration: str,
        fold: int,
        dataset_json: dict,
        device: torch.device = torch.device("cuda"),
    ):
        super().__init__(plans, configuration, fold, dataset_json, device)
        self.enable_deep_supervision = False
        
    def set_deep_supervision_enabled(self, enabled: bool):
        pass