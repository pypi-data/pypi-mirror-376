import os
import sys
import time

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
main_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
work_dir = os.getcwd()

def init_path(config):
    "Initialize the path for the training"
    if not "DATA_PATH" in config:
        init_data_path(config)
    if not "MODEL_DIR" in config:
        init_MODEL_DIR(config)
    init_GRAPH_DIR(config)
    # init_network_refer(config)
    # init_frag_ref_path(config)
    # init_NET_DIR(config)

def init_data_path(config):
    DATA_PATH = None
    data_file = config.get('data',None)
    if not data_file.endswith('.csv'):
        data_file += ".csv"
    if os.path.exists(data_file):
        DATA_PATH = data_file
    elif os.path.exists(base_dir+"/_Data/"+data_file):
        DATA_PATH = base_dir+"/_Data/"+data_file
    elif not '/' in data_file:
        for root, dirs, files in os.walk(work_dir):
            if data_file in files:
                DATA_PATH = os.path.join(root,data_file)
                break
    if DATA_PATH is None:
        raise Exception("Data file not found")
    config["DATA_PATH"] = DATA_PATH
    return DATA_PATH
    
def init_GRAPH_DIR(config):
    if 'GRAPH_DIR' in config:
        GRAPH_DIR = config['GRAPH_DIR']
    elif os.path.exists("./_Graphs"):
        GRAPH_DIR = "./_Graphs"
    else:
        os.makedirs("./_Graphs")
        GRAPH_DIR = "./_Graphs"
    config["GRAPH_DIR"] = GRAPH_DIR
    return GRAPH_DIR
    
def init_MODEL_DIR(config):
    if 'MODEL_DIR' in config:
        MODEL_DIR = config['MODEL_DIR']
    elif os.path.exists("./_Models"):
        MODEL_DIR = "./_Models"
    else:
        os.makedirs("./_Models")
        MODEL_DIR = "./_Models"
    config["MODEL_DIR"] = MODEL_DIR
    return MODEL_DIR
    
def get_network_refer(config):
    if 'NET_REFER' in config:
        NET_REFER = config.pop('NET_REFER')
    elif os.path.exists(base_dir+"/network_refer.yaml"):
        NET_REFER = base_dir+"/network_refer.yaml"
    return NET_REFER

def get_frag_ref_path(config):
    if 'FRAG_REF' in config:
        FRAG_REF = config.pop('FRAG_REF')
    elif os.path.exists(base_dir+"/src/utils/functional_group.csv"):
        FRAG_REF = base_dir+"/src/utils/functional_group.csv"
    return FRAG_REF
    
def get_NET_DIR(config):
    if 'NET_DIR' in config:
        NET_DIR = config.pop('NET_DIR')
    elif os.path.exists(work_dir+"/networks"):
        NET_DIR = work_dir+"/networks"
    elif os.path.exists(base_dir+"/networks"):
        NET_DIR = base_dir+"/networks"
    return NET_DIR
                          
    

def check_path(config):
    "Check the path of validity for the training"
    if not os.path.exists(config['DATA_PATH']):
        raise Exception("Data Path not found")
    if not os.path.exists(config['GRAPH_DIR']):
        raise Exception("Graph Path not found")
    if not os.path.exists(config['MODEL_DIR']):
        raise Exception("Model Path not found")


def find_model_path(model_name,config=None):
    if config is None:
        MODEL_DIR = "."
    else:
        if 'MODEL_DIR' in config:
            MODEL_DIR = config['MODEL_DIR']
        else:
            MODEL_DIR = init_MODEL_DIR(config)
    for root, dirs, files in os.walk(MODEL_DIR):
        if model_name in dirs:
            MODEL_PATH = os.path.join(root,model_name)
            print("founded model:",MODEL_PATH)
            return MODEL_PATH
    raise Exception("Model not found")

def get_model_path(config, make_dir=True):
    "Provide the new model path for the training"
    if 'MODEL_DIR' in config:
        MODEL_DIR = config['MODEL_DIR']
    else:
        MODEL_DIR = init_MODEL_DIR(config)

    if config.get('MODEL_PATH',None) is not None:
        path = config['MODEL_PATH'].split('/')[-1]
        path = os.path.join(MODEL_DIR,path)
    else:
        if config.get('TRANSFER_PATH',None) is not None:
            tf_name = config['TRANSFER_PATH'].split('/')[-1]
            try:
                tf_name = "_".join(tf_name.split('_')[:-2])
            except:
                pass
            path = os.path.join(MODEL_DIR,tf_name+"~"+config['network']+"_"+config['data']+'_'+','.join(config['target']))
        else:
            path = os.path.join(MODEL_DIR,config['network']+"_"+config['data']+'_'+','.join(config['target']))
        if 'sculptor_index' in config:
            path += "_"+''.join([str(i) for i in config['sculptor_index']])
        path += "_"+time.strftime("%Y%m%d_%H%M%S")
    if not os.path.exists(path) and make_dir:
        os.makedirs(path)
    config["MODEL_PATH"] = path
    return path

def get_xyz_dir_path(config):
    "Provide the new xyz path for the training (ALIGNN)"
    if 'xyz_dir' in config:
        XYZ_DIR = config['xyz_dir']
    elif os.path.exists(work_dir+"/_XYZ"):
        XYZ_DIR = work_dir+"/_XYZ"
    else:
        os.makedirs(work_dir+"/_XYZ")
        XYZ_DIR = work_dir+"/_XYZ"
    if not os.path.exists(XYZ_DIR):
        raise Exception("XYZ Path not found")
    config["XYZ_PATH"] = XYZ_DIR
    return XYZ_DIR