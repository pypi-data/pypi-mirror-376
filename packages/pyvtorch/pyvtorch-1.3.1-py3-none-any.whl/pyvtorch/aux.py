import os
import tqdm
import numpy as np
import torch

from pyvtools.text import find_numbers

#%% LOGGING

def print_debug(*args, debug:bool=False):
    if debug: print(*args)

class Logger:

    def __init__(self, debug:bool=False):
        self.debug=debug
    
    def log(self, *args):
        if self.debug: print(*args)

class LevelsLogger:

    def __init__(self, debug:int=0):
        self.debug = debug

    def info(self, *args):
        if self.debug>=1: print(*args)

    def log(self, *args):
        if self.debug>=2: print(*args)

    def detail(self, *args):
        if self.debug>=3: print(*args)

#%% CUDA/GPU SUPPORT

def get_device(pick_last=True, debug=False):
    if torch.cuda.is_available():
        # CUDA is available, use the last CUDA device (assume the first one is used by the system)
        devices = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
        if len(devices) > 1: 
            if pick_last: 
                torch.cuda.set_device( len(devices)-1 )
                print_debug("GPUs", devices, "(last is selected)", debug=debug)
            else:
                print_debug("GPUs", devices, "(first is selected", debug=debug)
        else: print_debug("GPU", devices[0], debug=debug)
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        # CUDA is not available, but MPS is available (Apple Silicon GPUs), use MPS device
        print_debug("MPS", debug=debug)
        return torch.device("mps")
    else:
        # Neither CUDA nor MPS is available, use the CPU
        print_debug("CPU", debug=debug)
        return torch.device("cpu")

def get_visible_device_numbers():
    """Returns physical GPU id numbers of visible devices"""
    try:
        visible_devices = find_numbers(os.environ["CUDA_VISIBLE_DEVICES"])
    except KeyError:
        visible_devices = list(range(torch.cuda.device_count()))
    return visible_devices

def get_device_number(device=None):
    """Returns physical GPU id number"""
    visible_devices = get_visible_device_numbers()
    if device is None:
        cuda_number = torch.cuda.current_device()
    else:
        cuda_number = torch.cuda._utils._get_device_index(device, optional=True)
    return visible_devices[cuda_number]

#%% MODEL UTILITIES

def extract_model_properties(model, requires_grad=True):

    if requires_grad:
        params = dict({k: p for k, p in model.named_parameters() if p.requires_grad})
    else:
        params = dict({k: p for k, p in model.named_parameters()})
    n_params = np.sum([p.numel() for p in params.values()])

    all_layers = []
    for k in params.keys():
        layer = k.split("weight")[0].split("bias")[0]
        if layer[-1]==".": layer = layer[:-1]
        all_layers.append(layer)
    
    layers = []
    for l in all_layers: 
        if l in all_layers and l not in layers: layers.append(l)

    included = []
    new_params = {}
    for l in layers[::-1]: # reverse order is needed coz some layer names are included in others
        these_params = {}
        for k, p in params.items():
            if l in k and k not in included: 
                these_params.update({k: p})
                included.append(k)
        new_params.update({l: these_params})
    params = {l: {k:p for k, p in zip(list(pars.keys())[::-1], list(pars.values())[::-1])} 
                  for l, pars in zip(list(new_params.keys())[::-1], list(new_params.values())[::-1])}
    
    return layers, params, n_params

def load_weights_and_check(model, state_dict, verbose=False):

    # Load checkpoint into the model
    old_params = [np.array(p.detach().cpu().numpy()) for p in model.parameters()] # Numpy array, instead of tensors
    model.load_state_dict(state_dict)
    new_params = [np.array(p.detach().cpu().numpy()) for p in model.parameters()] # Numpy array, instead of tensors
    n_changed = np.sum([np.sum(o!=n) for o, n in zip(old_params, new_params)])
    n_params = np.sum([np.prod(p.shape) for p in old_params])
    fraction_changed = round(n_changed/n_params, 4)
    if verbose:
        print("> Have the model parameters changed?", n_changed!=0)
        print("> Which fraction of them changed?", f"{fraction_changed*100:.2f}%")
    if fraction_changed!=1: raise ValueError("Loading incomplete: parameters have not changed")

    return model

#%% DATASET STATISTICS

def calculate_stats(n_samples, data_example_loader, paired=False):

    stats = {}
    all_x_min, all_x_max = [], []
    all_x_mean, all_x_sqs_mean = [], []
    if paired:
        all_y_min, all_y_max = [], []
        all_y_mean, all_y_sqs_mean = [], []

    for index in tqdm.tqdm(range(n_samples)):
        example = data_example_loader(index)
        if paired: x, y = example
        else: x = example
        all_x_min.append(float(x.min()))
        all_x_max.append(float(x.max()))
        all_x_mean.append(np.array(*[torch.mean(x, axis=(1,2)).detach().cpu()]))
        all_x_sqs_mean.append(np.array(*[torch.mean(x**2, axis=(1,2)).detach().cpu()]))
        if paired:
            all_y_min.append(float(y.min()))
            all_y_max.append(float(y.max()))
            all_y_mean.append(np.array(*[torch.mean(y, axis=(1,2)).detach().cpu()]))
            all_y_sqs_mean.append(np.array(*[torch.mean(y**2, axis=(1,2)).detach().cpu()]))
    
    x_shape = x.shape
    stats["x_shape"] = x_shape
    stats["x_dim"] = x.ndim
    del x
    if paired:
        y_shape = y.shape
        stats["y_shape"] = y_shape
        stats["y_dim"] = y.ndim
        del y    
    
    stats["all_x_min"] = np.array(all_x_min)
    stats["all_x_max"] = np.array(all_x_max)
    stats["all_x_mean"] = np.array(all_x_mean)
    stats["all_stds_x"] = np.sqrt( np.array(all_x_sqs_mean) - stats["all_x_mean"]**2 )

    stats["x_min"] = np.min(all_x_min); stats["x_max"] = np.max(all_x_max)
    stats["x_mean"] = np.mean(all_x_mean, axis=0)
    stats["x_std"] = np.sqrt( np.mean(all_x_sqs_mean, axis=0) - stats["x_mean"]**2 )

    if paired:

        stats["all_y_min"] = np.array(all_y_min)
        stats["all_y_max"] = np.array(all_y_max)
        stats["all_y_mean"] = np.array(all_y_mean)
        stats["all_stds_y"] = np.sqrt( np.array(all_y_sqs_mean) - stats["all_y_mean"]**2 )

        stats["y_min"] = np.min(all_y_min); stats["y_max"] = np.max(all_y_max)
        stats["y_mean"] = np.mean(all_y_mean, axis=0)
        stats["y_std"] = np.sqrt( np.mean(all_y_sqs_mean, axis=0) - stats["y_mean"]**2 )
        
    return stats