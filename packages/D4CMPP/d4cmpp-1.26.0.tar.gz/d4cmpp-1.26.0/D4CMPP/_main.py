import yaml
import os
import traceback
import importlib
from D4CMPP.src.utils import argparser
from D4CMPP.src.utils import PATH
from D4CMPP.src.PostProcessor import PostProcessor
from D4CMPP.src.utils import module_loader, supportfile_saver

config0 = {
    "data": None,
    "target": None,
    "network": None,

    "scaler": "standard",
    "optimizer": "Adam",

    "max_epoch": 2000,
    "batch_size": 256,
    "learning_rate": 0.001,
    "weight_decay": 0.0005,
    "lr_patience": 80,
    "early_stopping_patience": 200,
    'min_lr': 1e-5,

    "device": "cuda:0",
    "pin_memory": False,

    'hidden_dim': None,
    'conv_layers':None,
    'linear_layers': None,
    'dropout': None,

    'solv_hidden_dim': None,
    'solv_conv_layers': None,
    'solv_linear_layers': None,
}


def train(**kwargs):
    """
    Train the network with the given configuration.

    Args for the training:
        (Required args for the scratch training)
        data        : str
                      the name or path of the data file as a csv file. you can omit the ".csv" extension.
        target      : list[str]
                      the name of the target column.
        network     : str
                      the ID of the network to use. Refer to the networks.yaml file for the available networks ID.
        
        (Reqired args for continuing the training)
        LOAD_PATH   : str
                      the path of the directory that contains the model to continue the training.

        (Required args for the transfer learning)
        TRANSFER_PATH: str
                      the path of the directory that contains the model to transfer the learning.
        lr_dict     : dict (optional)
                      the dictionary for the learning rate of specific layers. e.g. {'GCNs': 0.0001}
                      you can find the layer names in "model_summary.txt" in the model directory.

                                    
        (Optional args)
        explicit_h_columns: list[str]. Default= []
                        the name of the columns to be used as explicit hydrogen features for the nodes.
        scaler      : str. Default= "standard",
                      ['standard', 'minmax', 'normalizer', 'robust', 'identity']
        optimizer   : str. Default= "Adam",
                      ['Adam', 'SGD', 'RMSprop', ... supported by torch.optim]
        max_epoch   : int. Defualt= 2000,
        batch_size  : int. Default= 128,
        learning_rate: float. Defualt= 0.001,
        weight_decay: float. Default= 0.0005,
        lr_patience : int. Defualt= 80,
                      the number of epochs with no improvement after which learning rate will be reduced.
        early_stopping_patience: 200,
                      the number of epochs with no improvement after which training will be stopped
        min_lr      : float. Defult= 1e-5,
                      the minimum learning rate
        device      : str. Defualt='cuda:0'
                      ['cpu', 'cuda:0', 'cuda:1', ...]
        pin_memory  : bool. Default= False
                      If True, the data loader will copy Tensors into CUDA pinned memory before returning them.
        split_random_seed: int. Default= 42,
        save_prediction: bool. Default= True,
            
        DATA_PATH   : str. Default= None
                      the path of directory that contains the data file. If None, it will walk the subpath.
        NET_REFER   : str. Default= "{src}/network_refer.yaml"
                      the path to the network reference file. 
        MODEL_DIR   : str. Default= "./_Models"
                      the path to the directory to save the models.
        MODEL_PATH  : str. Default= None
                      the path to the directory to save the model. If None, it will be created in the MODEL_DIR.
        GRAPH_DIR  : str. Default= "./_Graphs"
                      the path to the directory to save the graphs.
        FRAG_REF    : str. Default= "{src}/utils/functional_group.csv"
                      the path to the reference file for the functional groups.

    Args for the network:
    (The following args will be varied according to the network chosen. Refer to the source code of the network for more details.
    In general, below are the common args for the network)
        hidden_dim      : int. Default= 64
                          the dimension of the hidden layers in the graph convolutional layers
        conv_layers     : int. Default= 6
                          the number of graph convolutional layers
        linear_layers   : int. Default= 3
                          the number of linear layers after the graph convolutional layers
        dropout         : float. Default= 0.1
    
    --------------------------------------------
    Example:

        train(data='data.csv', target=['target1','target2'], network='GCN',)

        train(LOAD_PATH='GCN_model_test_Abs_20240101_000000')

        train(TRANSFER_PATH='GCN_model_test_Abs_20240101_000000', data='data.csv', target=['target1','target2'], lr_dict={'GCNs': 0.0001})

        train(data='data.csv', target=['target1','target2'], network='GCN', hidden_dim=32, conv_layers=4, linear_layers=2, dropout=0.1)

    
    """
    kwargs = check_args(**kwargs)
    config = set_config(**kwargs)
    if not config.get('loaded',False):
        supportfile_saver.save_additional_files(config)
    return run(config)

def check_args(**kwargs):
    "check the arguments for the training"
    if kwargs.get('LOAD_PATH',None) is not None:
        return kwargs
    if kwargs.get('target',None) is not None:
        if type(kwargs['target']) is not list:
            raise Exception("target should be a list of strings")
        else:
            kwargs['target_dim'] = len(kwargs['target'])
    if kwargs.get('data',None) is None:
        raise Exception("data is required")
    else:
        if kwargs['data'][-4:] == '.csv':
            kwargs['data'] = kwargs['data'][:-4]
    return kwargs


def set_config(**kwargs):    
    "process the arguments and set the configuration for the training"
    config = config0.copy()
    config.update(kwargs)
    if kwargs.get('use_argparser',False):
        args = argparser.parse_args()
        config.update(vars(args))   
    config = {k: v for k, v in config.items() if v is not None}

    netrefer_loaded = False
    # overwrite the config with the loaded config if the LOAD_PATH is given
    if config.get('LOAD_PATH',None) is not None:
        config['LOAD_PATH'] = PATH.find_model_path(config['LOAD_PATH'] , config)
        config['MODEL_PATH'] = config.pop('LOAD_PATH')
        config['loaded'] = True
        with open(config['MODEL_PATH']+'/config.yaml', "r") as file:
            _config = yaml.safe_load(file)# _config = yaml.load(open(os.path.join(config['LOAD_PATH'],'config.yaml'), 'r'), Loader=yaml.FullLoader)
        _config.update(config)
        config = _config
        netrefer_loaded = True

    PATH.init_path(config)

    if config.get('TRANSFER_PATH',None) is not None:
        config['TRANSFER_PATH'] = PATH.find_model_path(config['TRANSFER_PATH'],config)

        # if the network is not given, load the network from the transfer path
        if config.get('network', None):
            net_config = load_NET_REFER(config)
            config.update(net_config)

        # load the config from the transfer path
        with open(config['TRANSFER_PATH']+'/config.yaml', "r") as file:
            _config = yaml.safe_load(file)
            _config.pop('MODEL_PATH',None)
        _config.update(config)
        config = _config
        config['MODEL_PATH'] = PATH.get_model_path(config)
        netrefer_loaded = True
        
    if not netrefer_loaded:
        net_config = load_NET_REFER(config)
        config.update(net_config)
        config['MODEL_PATH'] = PATH.get_model_path(config)

    if config.get('sculptor_index',None) is not None and type(config['sculptor_index']) is tuple:
        config['sculptor_s'] = config['sculptor_index'][0]
        config['sculptor_c'] = config['sculptor_index'][1]
        config['sculptor_a'] = config['sculptor_index'][2]
        config.pop('sculptor_index')
    PATH.check_path(config)
    return config

def load_NET_REFER(config):
    with open(PATH.get_network_refer(config), "r") as file:
        network_refer = yaml.safe_load(file)
    net_config = network_refer.get(config['network'],None)
    if net_config is None:
        err = "The network ID is not found in the network reference file.\n"
        err += "The available network IDs are: "+", ".join(network_refer.keys())
        raise Exception(err)
    return net_config


def run(config):
    "the main function to run the training"
    tf_path = config.pop('TRANSFER_PATH',None)
    is_loaded = config.pop('loaded',False)
    e=None
    if tf_path:
        print("Transfer Learning from",tf_path)
        print("Transfer Learning to",config['MODEL_PATH'])
    elif is_loaded:
        print("Continue Learning from",config['MODEL_PATH'])
    else:
        print("Training from scratch to",config['MODEL_PATH'])

    try:
        dm = module_loader.load_data_manager(config)(config)
        nm = module_loader.load_network_manager(config)(config, tf_path=tf_path, unwrapper = dm.unwrapper)
        tm = module_loader.load_train_manager(config)(config)
        dm.init_data()
        supportfile_saver.save_config(config)
        train_loaders, val_loaders, test_loaders = dm.get_Dataloaders()
        tm.train(nm, train_loaders, val_loaders)
    except Exception as e:
        print(traceback.format_exc())
        return
    if tm.train_error is not None:
        return

    pp = PostProcessor(config)
    pp.postprocess(dm, nm, tm, train_loaders, val_loaders, test_loaders)
    if e is not None:
        raise e
    return config['MODEL_PATH']

if __name__ == "__main__":
    train(**config0, use_argparser=True)