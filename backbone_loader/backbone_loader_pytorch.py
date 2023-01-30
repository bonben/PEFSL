print("importing torch")
import torch
import numpy as np

from backbone_loader.backbone_pytorch.model import get_model#.resnet12 import ResNet12

print("torch imported")


def load_model_weights(
    model, path, device=None, verbose=False, raise_error_incomplete=True
):
    """
    load the weight given by the path
    if the weight is not correct, raise an errror
    if the weight is not correct, may have no loading at all
        args:
            model(torch.nn.Module) : model on wich the weights should be loaded
            path(...) : a file-like object (path of the weights)
            device(torch.device) : the device on wich the weights should be loaded (optional)
    """
    pretrained_dict = torch.load(path, map_location=device)
    model_dict = model.state_dict()
    # pretrained_dict = {k: v for k, v in pretrained_dict.items() if k in model_dict}
    new_dict = {}
    for k, weight in pretrained_dict.items():
        if k in model_dict:
            if verbose:
                print(f"loading weight name : {k}", flush=True)

            # bn : keep precision (low cost associated)
            # does this work for the fpga ?
            if "bn" in k:
                new_dict[k] = weight.to(torch.float16)
            else:
                new_dict[k] = weight.to(torch.float16)
        else:
            if raise_error_incomplete:
                raise TypeError("the weights does not correspond to the same model")
            print("weight with name : {k} not loaded (not in model)")
    model_dict.update(new_dict)
    model.load_state_dict(model_dict)
    print("Model loaded!")


class TorchBatchModelWrapper:
    """
    Wrapps a torch model to input/output ndarray
    """
    def __init__(self,model_name,weights,device="cpu"):
        self.model=get_model(model_name,weights,device=device)
        self.device=device
    
    def __call__(self,img):
        """
        return the features from an img
        args :
            - img(np.ndarray) : represent a batch of image (channel last convention)
        """

        assert len(img.shape)==4

        self.model.eval()

        #convertion to tensor with channel first convention
        img=np.transpose(img,(0,3,1,2))

        img=torch.from_numpy(img)   
        img = img.to(self.device)

        with torch.no_grad():
            _, features = self.model(img)
        return features.cpu().numpy()
