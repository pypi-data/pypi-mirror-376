import yaml
import os
import numpy as np
import torch
import hashlib
import pickle
import importlib

import rdkit.Chem as Chem

from D4CMPP.src.utils import PATH, module_loader

class MolAnalyzer:
    """The class for additional tasks after the training."""
    def __init__(self, model_path, save_result = False):
        """
        Args:
            model_path (str): The path to the model.
            save_result (bool): If True, every calculated result will be saved in the model_path.        
        """

        self.model_path = PATH.find_model_path(model_path)
        self.save_result = save_result 
        self.data_path = os.path.join(model_path, 'data')
        if not os.path.exists(self.data_path) and self.save_result:
            os.makedirs(self.data_path)
        
        config = yaml.load(open(os.path.join(self.model_path,'config.yaml'), 'r'), Loader=yaml.FullLoader)
        config['MODEL_PATH'] = self.model_path
        config['LOAD_PATH'] = self.model_path
        self.config = config
        self.nm = module_loader.load_network_manager(config)(config, unwrapper = None, temp= True)
        self.dm = module_loader.load_data_manager(config)(config)
        self.tm = module_loader.load_train_manager(config)(config)
        self.nm.set_unwrapper(self.dm.unwrapper)


        # load scaler
        if not os.path.exists(os.path.join(self.model_path,'scaler.pkl')):
            self.scaler = None
        else:
            with open(os.path.join(self.model_path,'scaler.pkl'), 'rb') as f:
                self.scaler = pickle.load(f)

        # the data types to save
        self.data_keys = ['prediction', ]
        self.for_pickle = ['fragments', ]

    # the function to prepare the data for the prediction
    def prepare_temp_data(self, smiles_list, solvents = None):
        if solvents is not None:
            valid_smiles = self.dm.init_temp_data(smiles_list, solvents)
        else:
             valid_smiles = self.dm.init_temp_data(smiles_list)
        temp_loader = self.dm.get_Dataloaders(temp=True)
        return temp_loader, valid_smiles
    

    # the main function to predict the target values
    def predict(self, smiles_list, solvent_list = None, dropout=False):
        if solvent_list is None:
            if type(smiles_list) is str:
                smiles_list = [smiles_list]        
            result = {}
            for smiles in smiles_list:
                score = self.load_data(smiles, 'prediction')
                if score is not None:
                    result[smiles] = score
            smiles_list = [smiles for smiles in smiles_list if smiles not in result.keys()]
        else:
            if type(smiles_list) is str:
                smiles_list = [smiles_list]        
            if type(solvent_list) is str:
                solvent_list = [solvent_list]
            result = {}
            for smiles,solvent in zip(smiles_list,solvent_list):
                score = self.load_data(smiles+"_"+solvent, 'prediction')
                if score is not None:
                    result[(smiles,solvent)] = score
            _smiles_list = [smiles for smiles,solvent in zip(smiles_list,solvent_list) if (smiles,solvent) not in result.keys()]
            _solvent_list = [solvent for smiles,solvent in zip(smiles_list,solvent_list) if (smiles,solvent) not in result.keys()]
            smiles_list = _smiles_list
            solvent_list = _solvent_list

        if len(smiles_list) > 0 :
            smiles_list, solvent_list = self.add_dummy_into_input(smiles_list, solvent_list)
            test_loader,valid_smiles = self.prepare_temp_data(smiles_list,solvent_list)
            valid_compound = valid_smiles['compound']
            valid_solvent = valid_smiles['solvent'] if 'solvent' in valid_smiles else None

            score,_,_,_ = self.tm.predict(self.nm, test_loader, dropout=dropout)
            if type(score) is torch.Tensor:
                score = score.detach().cpu().numpy()
            smiles_list, solvent_list, score = self.remove_dummy_from_output(valid_compound, valid_solvent, score)
            if len(score) > 0:
                score = self.scaler.inverse_transform(score)
            for i,smiles in enumerate(smiles_list):
                if solvent_list is not None:
                    result[(smiles,solvent_list[i])] = score[i]
                    self.save_data(smiles+"_"+solvent_list[i], {'prediction': score[i]})
                else:
                    result[smiles] = score[i]
                    self.save_data(smiles, {'prediction': score[i]})
        return result
    
    # the functions to save and load the data
    def save_data(self, smiles, data):
        if not self.save_result: return
        for k in data.keys():
            if k not in self.data_keys:
                print(f"key must be in {self.data_keys}")
            file_name = self.get_file_name(smiles, k)
            if type(data[k]) is torch.Tensor:
                data[k] = data[k].detach().cpu().numpy()
            elif not type(data[k]) is np.ndarray:
                data[k] = np.array(data[k])
            with open(os.path.join(self.data_path, file_name), 'wb') as f:
                if k in self.for_pickle:
                    pickle.dump(data[k],f)
                else:
                    np.save(f,data[k],)

    def load_data(self, smiles, key):
        if not self.save_result: return None
        file_name = self.get_file_name(smiles, key)
        if not os.path.exists(os.path.join(self.data_path, file_name)):
            return None
        try:
            with open(os.path.join(self.data_path, file_name), 'rb') as f:
                if key in self.for_pickle:
                    return pickle.load(f)
                return np.load(f)
        except:
            return None
        
    def get_file_name(self, smiles, key):
        m = hashlib.sha256()
        m.update(smiles.encode('utf-8'))
        name = m.hexdigest()
        if not key in self.data_keys:
            raise ValueError(f"key must be in {self.data_keys}")
        if key in self.for_pickle:
            return f"{name}_{self.data_keys.index(key)}.pickle"
        return f"{name}_{self.data_keys.index(key)}.np"
    
    # the functions to add and remove dummy data. this is for prevention of the error when the number of input data is only one.
    def add_dummy_into_input(self, smiles_list, solvent_list = None):        
        if len(smiles_list) ==1:
            self.dummy_added = True
            smiles_list+= ['NCCCC(=O)','c1ccccc1O']
            if solvent_list is not None:
                solvent_list+= ['CCO','CCO']
        else:
            self.dummy_added = False

        return smiles_list, solvent_list
    
    def remove_dummy_from_output(self, smiles_list, solvent_list, score):
        if self.dummy_added:
            if solvent_list is not None:
                if smiles_list[-1]=='NCCCC(=O)' and solvent_list[-1]=='CCO':
                    smiles_list = smiles_list[:-1]
                    solvent_list = solvent_list[:-1]
                    score = score[:-1]
                if smiles_list[-1]=='c1ccccc1O' and solvent_list[-1]=='CCO':
                    smiles_list = smiles_list[:-1]
                    solvent_list = solvent_list[:-1]
                    score = score[:-1]
                if smiles_list[-1]=='NCCCC(=O)' and solvent_list[-1]=='CCO':
                    smiles_list = smiles_list[:-1]
                    solvent_list = solvent_list[:-1]
                    score = score[:-1]
            else:
                if smiles_list[-1]=='NCCCC(=O)':
                    smiles_list = smiles_list[:-1]
                    score = score[:-1]
                if smiles_list[-1]=='c1ccccc1O':
                    smiles_list = smiles_list[:-1]
                    score = score[:-1]
                if smiles_list[-1]=='NCCCC(=O)':
                    smiles_list = smiles_list[:-1]
                    score = score[:-1]
        return smiles_list, solvent_list, score

class MolAnalyzer_v1p3(MolAnalyzer):
    """The class for additional tasks after the training. This is for the version 1.3 and later."""
    def __init__(self, model_path, save_result = True):
        super().__init__(model_path, save_result)
        if self.config.get('version', '1.0') < '1.3':
            raise ValueError("This class is for the version 1.3 and later. Please use MolAnalyzer instead.")

        self.molecule_columns = self.config.get('molecule_columns', ['compound'])
        self.numeric_input_columns = self.config.get('numeric_input_columns', [])

    def prepare_temp_data(self, **kwargs):

        result = self.dm.init_temp_data(**kwargs)
        temp_loader = self.dm.get_Dataloaders(temp=True)
        return temp_loader, result

    def add_dummy_into_input(self, **kwargs):
        self.dummy_added = False
        for k in kwargs.keys():
            if k in self.molecule_columns:
                smiles_list = kwargs[k]
                if len(smiles_list) ==1:
                    self.dummy_added = True
                    smiles_list+= ['c1ccccc1O']
                kwargs[k] = smiles_list
            elif k in self.numeric_input_columns:
                if len(kwargs[k]) == 1:
                    self.dummy_added = True
                    kwargs[k] += [0.0]
            else:
                raise ValueError(f"Unknown key {k}. Please provide the smiles for {self.molecule_columns} or numeric input for {self.numeric_input_columns}.")
        return kwargs

    def remove_dummy_from_output(self, scores, **kwargs):
        if self.dummy_added:
            for k in kwargs.keys():
                if k in self.molecule_columns:
                    smiles_list = kwargs[k]

                    if smiles_list[-1]=='c1ccccc1O':
                        smiles_list = smiles_list[:-1]
                    kwargs[k] = smiles_list
                else:
                    kwargs[k] = kwargs[k][:-1]
            scores = scores[:-1]
        return scores, kwargs

    def handle_positional_args(self, args, kwargs):
        if len(args)+len(kwargs) < len(self.molecule_columns) + len(self.numeric_input_columns):
            raise ValueError(f"Please provide the smiles for {self.molecule_columns} and numeric input for {self.numeric_input_columns}.")
        if len(args) > 0:
            print(f"Positional arguments are provided. Note that arguments should be in the order of {self.molecule_columns} and {self.numeric_input_columns}.")
            if len(args) == len(self.molecule_columns) + len(self.numeric_input_columns):
                kwargs = {self.molecule_columns[i]: args[i] for i in range(len(self.molecule_columns))}
                kwargs.update({self.numeric_input_columns[i]: args[i + len(self.molecule_columns)] for i in range(len(self.numeric_input_columns))})
            elif len(args) == len(self.molecule_columns):
                kwargs = {self.molecule_columns[i]: args[i] for i in range(len(self.molecule_columns))}
            elif len(args) == len(self.numeric_input_columns):
                kwargs = {self.numeric_input_columns[i]: args[i] for i in range(len(self.numeric_input_columns))}
            else:
                raise ValueError(f"Please provide the smiles for {self.molecule_columns} and numeric input for {self.numeric_input_columns}.")
        other_kwargs = {}
        if len(kwargs) >0:
            for k in kwargs.keys():
                if k not in self.molecule_columns and k not in self.numeric_input_columns:
                    other_kwargs[k] = kwargs.pop(k)
                
            for k in self.molecule_columns:
                if k not in kwargs:
                    raise ValueError(f"Please provide the smiles for {k}.")
            for k in self.numeric_input_columns:
                if k not in kwargs:
                    raise ValueError(f"Please provide the numeric input for {k}.")
        for k in kwargs.keys():
            if type(kwargs[k]) is not list :
                kwargs[k] = [kwargs[k]]
        return kwargs, other_kwargs

    def predict(self,*args, dropout=False, **kwargs):
        # TODO: load the data from the model_path
        kwargs,_ = self.handle_positional_args(args, kwargs)

        kwargs = self.add_dummy_into_input(**kwargs)
        test_loader,result = self.prepare_temp_data(**kwargs)

        score,_,_,_ = self.tm.predict(self.nm, test_loader, dropout=dropout)
        if type(score) is torch.Tensor:
            score = score.detach().cpu().numpy()
        score, kwargs = self.remove_dummy_from_output( score, **result)
        if len(score) > 0:
            score = self.scaler.inverse_transform(score)

        result = {}
        for i in range(len(score)):
            input_data = (kwargs[k][i] for k in self.molecule_columns + self.numeric_input_columns)
            result[tuple(input_data)] = score[i]
            # TODO: save the data

        # for i,smiles in enumerate(smiles_list):
        #     if solvent_list is not None:
        #         result[(smiles,solvent_list[i])] = score[i]
        #         self.save_data(smiles+"_"+solvent_list[i], {'prediction': score[i]})
        #     else:
        #         result[smiles] = score[i]
        #         self.save_data(smiles, {'prediction': score[i]})
        return result


def mol_with_atom_index( mol ):
    if type(mol) is str:
        mol = Chem.MolFromSmiles(mol)
    atoms = mol.GetNumAtoms()
    for idx in range( atoms ):
        mol.GetAtomWithIdx( idx ).SetProp( 'molAtomMapNumber', str( mol.GetAtomWithIdx( idx ).GetIdx() ) )
    return mol
