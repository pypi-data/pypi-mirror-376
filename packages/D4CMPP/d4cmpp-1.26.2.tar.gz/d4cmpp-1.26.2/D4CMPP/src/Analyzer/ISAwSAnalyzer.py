
import numpy as np
import torch
import io
import rdkit.Chem as Chem


from .ISAAnalyzer import ISAAnalyzer

class ISAwSAnalyzer(ISAAnalyzer):
    def check_score_by_group(self):
        if getattr(self.dm.gg,'sculptor',None) is None:
            self.is_score_by_group = True
        else:
            temp_smiles='CC(C)(C)OC(=O)C1=CC=CC=C1C(=O)O'
            temp_solvent = "CS(=O)C"
            
            test_loader,_ = self.prepare_temp_data([temp_smiles],solvents=[temp_solvent])
            temp_score = self.tm.get_score(self.nm, test_loader)

            if 'positive' in temp_score:
                temp_score['positive'] = temp_score['positive'].detach().cpu().numpy()
                if temp_score['positive'].shape[0] == len(self.get_fragment(temp_smiles)):
                    self.is_score_by_group = True
                elif temp_score['positive'].shape[0] == Chem.MolFromSmiles(temp_smiles).GetNumAtoms():
                    self.is_score_by_group = False
                else:
                    raise ValueError('The length of the score and the number of fragments do not match.')
            else:
                raise ValueError('The score is not calculated properly.')


    # get the attention score of the given smiles
    def get_score(self, smiles, solvent):
        "get the attention score of the given smiles by its subgroups"
        # pos_score = self.load_data(smiles, 'positive')
        # if pos_score is not None:
        #     neg_score = self.load_data(smiles, 'negative')
        #     if neg_score is not None:
        #         return {'positive': pos_score, 'negative': neg_score}
        #     else:
        #         return {'positive': pos_score}
        if False:
            pass
        else:            
            test_loader,_ = self.prepare_temp_data([smiles],[solvent])
            result = self.tm.get_score(self.nm, test_loader)
            for k in result.keys():
                if type(result[k]) is torch.Tensor:
                    result[k] = result[k].detach().cpu().numpy()

            result['positive'] = self.get_group_score(smiles, result['positive'])
            if 'negative' in result:
                result['negative'] = self.get_group_score(smiles, result['negative'])
            self.save_data(smiles, result)
            return result

    def get_feature(self, smoles, solvent):
        """
        This function gets the feature of the given smiles and solvent.

        Args:
            smiles (str): The smiles of the molecule.
            solvent (str): The solvent of the molecule.

        Returns:
            dict: The feature of the given smiles and solvent.
        """
        test_loader, _ = self.prepare_temp_data([smoles], [solvent])
        return self.tm.get_feature(self.nm, test_loader)
    
    def get_feature(self, smiles_list, solvent_list, feature=None):
        results = {}

        if len(smiles_list) > 0:
            valid_smiles, new_results = self._get_all_features(smiles_list, solvent_list, feature=feature)
            for smiles, result in zip(valid_smiles, new_results):
                results[smiles] = result
        return results
    
    
    def _get_all_features(self, smiles_list, solvent_list, feature=None):
        temp_loader,valid_smiles = self.prepare_temp_data(smiles_list, solvent_list)
        features = self.tm.get_feature(self.nm, temp_loader)
        features = {k:features[k].detach().cpu().numpy() for k in features.keys()}
        results = []
        count=0
        for i, smiles in enumerate(valid_smiles['compound']):
            result = {}
            if feature is not None:
                result[feature] = features[feature][i]
            else:
                frag = self.get_fragment(smiles)
                result['feature_P'] = features['feature_P'][count:count+len(frag)]
                if 'feature_N' in features:
                    result['feature_N'] =  features['feature_N'][count:count+len(frag)]
                count+=len(frag)
            results.append(result)
            self.save_data(smiles, result)
        return valid_smiles['compound'], results



    def plot_score(self, smiles, solvent ,**kwargs):
        """
        This function plots the attention score of the given smiles by its subgroups.

        Args:
            smiles (str): The smiles of the molecule.
            atom_with_index (bool): Whether to show the atom index or not.
            score_scaler (function): The function to scale the score. Default is lambda x:x.
            ticks (list): The ticks of the colorbar. Default is [0,0.25,0.5,0.75,1].
            rot (int): The rotation of the molecule. Default is 0.
            locate (str): The location of the subplots. Default is 'right'. It can be 'right' or 'bottom'.
            figsize (float): The size of the figure. Default is 1.
            only_total (bool): Whether to plot only the total score or plot PAS and NAS as well. Default is False.
            with_colorbar (bool): Whether to show the colorbar or not. Default is True.

        Returns:
            dict: The attention score of the given smiles.
                  Each value in the dictionary is the attention score of corresponding atom with the same index.
        
        """
        score = self.get_score(smiles, solvent)
        return self._plot_score(smiles, score, **kwargs)
        
