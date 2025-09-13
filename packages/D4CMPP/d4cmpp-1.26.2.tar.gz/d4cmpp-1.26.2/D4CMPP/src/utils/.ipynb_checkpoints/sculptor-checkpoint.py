
import numpy as np
from rdkit import Chem
import sys
import os
import pandas as pd
import dgl
import torch

from D4CMPP.src.utils import tools

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

class Subgroup():
    def __init__(self, mol, atoms, name, priority):
        self.atoms=atoms
        self.name=name
        self.priority=priority
        self.mol = mol if type(mol)==Chem.rdchem.Mol else Chem.MolFromSmiles(mol)
        
    def __len__(self):
        return len(self.atoms)

    def add_smiles(self,thrsh=4):
        group_smiles = self.specify_group()
        if group_smiles is None: return
        if len(self.atoms)<=thrsh:
            self.smiles=group_smiles
        else:
            smi=Chem.MolFragmentToSmiles(self.mol,[int(j) for j in self.atoms])
            self.smiles=remove_index(smi)

    def specify_group(self):
        smiles=get_fragment_with_branch(self.mol,self.atoms)
        if smiles =="*c1ccccc1":
            self.name = "Phenyl"
            self.smiles = "*c1ccccc1"
            return None
        return smiles


class Subgroup_list():
    def __init__(self, mol, subgroups):
        self.subgroups = subgroups
        self.mol = mol if type(mol)==Chem.rdchem.Mol else Chem.MolFromSmiles(mol)
        
        adj_mat = np.eye(len(subgroups))
        for i in range(len(subgroups)):
            for j in range(i+1,len(subgroups)):
                sub1,sub2=subgroups[i],subgroups[j]
                if is_neighbor(self.mol,sub1.atoms,sub2.atoms):
                    adj_mat[i,j]=1
                    adj_mat[j,i]=1
        self.adj_mat=adj_mat
        
    def __len__(self):
        return len(self.subgroups)
    
    def __getitem__(self, key):
        return self.subgroups[key]
    
    def __iter__(self):
        return iter(self.subgroups)
    
    def is_neighbor(self,i,j):
        return self.adj_mat[i,j]==1
    
    def concat(self,idxs_list,order = '8'):
        if type(idxs_list)!=list: idxs_list=[idxs_list]

        delete_idx = []
        for idxs in idxs_list:
            if len(idxs)==1: continue
            i = idxs[0]
            for j in idxs[1:]:
                self.subgroups[i].atoms = list(np.concatenate([self.subgroups[i].atoms,self.subgroups[j].atoms]))
                self.subgroups[i].name = self.subgroups[i].name+'+'+self.subgroups[j].name
                self.subgroups[i].priority = order

                self.adj_mat[i,:]=((self.adj_mat[i,:]+self.adj_mat[j,:])>0)*1
                self.adj_mat[:,i]=((self.adj_mat[:,i]+self.adj_mat[:,j])>0)*1

                delete_idx.append(j)
        delete_idx = list(set(delete_idx))
        if len(delete_idx)==0: return
        self.adj_mat=np.delete(self.adj_mat,delete_idx,axis=0)
        self.adj_mat=np.delete(self.adj_mat,delete_idx,axis=1)
        for j in [self.subgroups[i] for i in delete_idx]:
            self.subgroups.remove(j)




class SubgroupSplitter(object):
    def __init__(self, refer_path,
                split_order=6, 
                 combine_rest_order=1,  
                 absorb_neighbor_order=-1,  
                                            
                 overlapped_ring_combine=True,  
                 log=False,
                 draw=False,
                get_index=False                
                ):
        path = os.path.join(refer_path)
        data_from = os.path.realpath(path)
        df = pd.read_csv(data_from, header=0)
        pattern = np.array([df['Name'], df['SMARTS'], df['Priority']])
        self.sorted_pattern = pattern[:, np.argsort(pattern[2, :])]
        self.frag_name_list = list(dict.fromkeys(self.sorted_pattern[0, :]))
        self.frag_dim=167
        
        self.split_order=split_order
        self.overlapped_ring_combine=overlapped_ring_combine
        self.combine_rest_order=combine_rest_order
        self.absorb_neighbor_order=absorb_neighbor_order
        self.log=log
        self.draw=draw
        self.get_index=get_index
        self.adj_mat = None

    def fragmentation_with_condition(self,mol,
                                     split_order=None,
                                     overlapped_ring_combine=None, 
                                     combine_rest_order=None, 
                                     absorb_neighbor_order=None,  
                                     log=None,
                                     draw=None,
                                    get_index=None,
                                    atom_with_index=False):
        if split_order is None: split_order=self.split_order
        if overlapped_ring_combine is None: 
            overlapped_ring_combine=self.overlapped_ring_combine
        if combine_rest_order is None: combine_rest_order=self.combine_rest_order
        if absorb_neighbor_order is None: 
            absorb_neighbor_order=self.absorb_neighbor_order
        if split_order>=8: overlapped_ring_combine=True
        if log is None: log=self.log
        if draw is None: draw=self.draw
        if get_index is None: get_index=self.get_index
        self.subgroup_list = None
       
    
        if type(mol)==str: mol = Chem.MolFromSmiles(mol)
        self.mol_size = mol.GetNumAtoms()
        self.mol=mol
        pat_list = self.get_pattern_list(mol)
        
        layer_pat_list,layer_sorted_pattern = self.get_masked_pattern_list(pat_list,order=split_order)
                
        self.init_subgroup_list(layer_pat_list,layer_sorted_pattern,
                                             log=log,ring_combine=overlapped_ring_combine,mol=mol)
        

        if combine_rest_order>0:
            self.combine_neighbor_subgroups(order=combine_rest_order,log=log)
                       
        if absorb_neighbor_order>0:
            self.absorb_neighbor_subgroups(order=absorb_neighbor_order,log=log)
        
        return self.return_result(log,draw,get_index,atom_with_index)
    
    def return_result(self,log=False,draw=False,get_index=False,atom_with_index=False):
        atoms = []
        for i in self.subgroup_list:
            for j in self.subgroup_list:
                if i==j: continue
                if set(i.atoms).intersection(set(j.atoms)):
                    raise Exception("Error: overlapped subgroup\n",i.atoms,j.atoms)
            atoms+=i.atoms
        if len(atoms)!=self.mol_size:
            raise Exception("Error: not matched subgroup\n",atoms)

        if draw:
            tools.showAtomHighlight(self.mol,[i.atoms for i in self.subgroup_list],atom_with_index=atom_with_index)

        if log:
            print("return_result")
            print([(i.name,i.atoms,) for i in self.subgroup_list])

        if get_index:
            return [i.atoms for i in self.subgroup_list]
        else:
            for l in self.subgroup_list:
                l.add_smiles()
            return self.subgroup_list

    
    def get_pattern_list(self, mol):
        pat_list = []
        for patt in self.sorted_pattern[1, :]:
            pat = Chem.MolFromSmarts(patt)

            pat_list.append(list(mol.GetSubstructMatches(pat)))
        return pat_list
    
    def get_masked_pattern_list(self, pat_list, order=4, min_order=-2):
        upper_layer_mask=np.where(self.sorted_pattern[2]<order+1)[0]
        lower_ayer_mask=np.where(self.sorted_pattern[2]>=min_order)[0]
        layer_mask=np.intersect1d(upper_layer_mask,lower_ayer_mask)
        layer_pat_list = [pat_list[i] for i in layer_mask]
        layer_sorted_pattern = np.flip(self.sorted_pattern[:,layer_mask],axis=1)
        return layer_pat_list, layer_sorted_pattern
    
    def init_subgroup_list(self, pat_list, sorted_pattern,log=False,ring_combine=False,mol=None,duplicate_allow=False):
        used_atom_list=[]  
        subgroup_list=[]   
        temporary_ring_list=[]
        temporary_ring_names=[]
        for pat_index, groups in enumerate(reversed(pat_list)):
            if len(groups) and log: print(pat_index,sorted_pattern[0][pat_index],
                                          sorted_pattern[1][pat_index],
                                          sorted_pattern[2][pat_index],groups)
            for group in groups:
                group=list(group)
                used=False
                if ring_combine:
                    is_temporary_ring=sorted_pattern[2][pat_index]>=5

                    if is_temporary_ring:
                        temporary_ring_list.append(group)
                        temporary_ring_names.append(sorted_pattern[0][pat_index])
                        used_atom_list=used_atom_list+group
                        if not duplicate_allow: continue
                        
                if not duplicate_allow:
                    for atom_index in group:
                        if atom_index in used_atom_list: used=True
                    if used: continue
                    
                used_atom_list=used_atom_list+group
                subgroup_list.append(Subgroup(self.mol,group,sorted_pattern[0][pat_index],sorted_pattern[2][pat_index]))
        if ring_combine:
            temporary_ring_list2=[]
            temporary_ring_list2_names=[]
            for i in range(len(temporary_ring_list)):
                if temporary_ring_list[i] not in temporary_ring_list2:
                    temporary_ring_list2.append(temporary_ring_list[i])
                    temporary_ring_list2_names.append(temporary_ring_names[i])
            
            if log: print(temporary_ring_list)
            concated_ring_list, ring_list, concated_names, ring_names =Concat_overlapped(mol,temporary_ring_list2,temporary_ring_list2_names) 
            for concated_ring, concated_name in zip(concated_ring_list,concated_names):
                    subgroup_list.append(Subgroup(self.mol,concated_ring,'poly rings','8'))
            for ring, ring_name in zip(ring_list,ring_names):
                    subgroup_list.append(Subgroup(self.mol,ring,ring_name,'6'))
            
        for atom_index in range(self.mol_size):
            if atom_index not in used_atom_list:
                subgroup_list.append(Subgroup(self.mol,[atom_index],'Undefined','-1'))
                

        self.subgroup_list = Subgroup_list(self.mol,subgroup_list)
    
    def combine_neighbor_subgroups(self,order=1,log=False):
        if log: 
            print("combine_neighbor_subgroups")
            print([(i.name,i.atoms,i.priority) for i in self.subgroup_list])
            print()
    
        concat_targets=[]

        for i,subgroup1 in enumerate(self.subgroup_list):  
            if float(subgroup1.priority) < order: 
                concat_targets.append(i)
        self.Concat_neighbor_asAll(concat_targets,order) 

    def absorb_neighbor_subgroups(self,order=5,log=False):
        if log: 
            print("absorb_neighbor_subgroups")
            print([(i.name,i.atoms,i.priority) for i in self.subgroup_list])
            print()
    
        concat_sbjs=[] 
        concat_objs=[] 
        
        for i,subgroup1 in enumerate(self.subgroup_list): 
            if float(subgroup1.priority) >= order: 
                concat_sbjs.append(i)
            else:
                concat_objs.append(i)
        self.Concat_neighbor_asSubject(concat_sbjs,concat_objs)
        
    

    def Concat_neighbor_asAll(self,frags,order = 1): 
        concat_targets= []
    
        for i in range(len(frags)):
            concat_target,concat_targets = self.get_concat_target(frags[i],concat_targets)
            for j in range(i+1,len(frags)):
                if self.subgroup_list.is_neighbor(frags[i],frags[j]):
                    concat_target.append(frags[j])
            concat_targets.append(list(set(concat_target)))
        self.subgroup_list.concat(concat_targets,order = str(order))

    def Concat_neighbor_asSubject(self,sbjs,objs): 
        concat_targets= [[sbj] for sbj in sbjs]
        used_obj = []
        for sbj in sbjs.copy():
            concat_target,concat_targets = self.get_concat_target(sbj,concat_targets)
            for obj in objs:
                if self.subgroup_list.is_neighbor(sbj,obj) and obj not in used_obj:
                    concat_target.append(obj)
                    used_obj.append(obj)
            concat_targets.append(list(set(concat_target)))
            
        self.subgroup_list.concat(concat_targets,order = '10')
        
    @staticmethod
    def get_concat_target(i,concat_targets):
        concat_target = None
        for _target in concat_targets.copy():
            if i in _target: 
                if concat_target is None:
                    concat_target = _target.copy()
                else:
                    concat_target = concat_target+_target
                concat_targets.remove(_target)
        if concat_target is None:
            concat_target = [i]
        return concat_target,concat_targets
        
class SubgroupSplitter_for_DA(SubgroupSplitter):
    def __init__(self, refer_path,
                split_order=6,
                 overlapped_ring_combine=False,  
                 combine_rest_order=1,  
                 absorb_neighbor_order=-1,  
                 log=False,
                 draw=True,
                get_index=False                
                ):
        super().__init__(refer_path,split_order,overlapped_ring_combine,combine_rest_order,absorb_neighbor_order,log,draw,get_index)
                         
    def fragmentation_with_condition(self,mol,get_index=None):
        if type(mol)==str: mol = Chem.MolFromSmiles(mol)
        if get_index is None: get_index=self.get_index
        self.mol_size = mol.GetNumAtoms()
        self.mol=mol
        pat_list = self.get_pattern_list(mol)
        
        layer_pat_list,layer_sorted_pattern = self.get_masked_pattern_list(pat_list,order=self.split_order)
                
        self.init_subgroup_list(layer_pat_list,layer_sorted_pattern,
                                             log=self.log,ring_combine=self.overlapped_ring_combine,mol=mol)
        
        if self.combine_rest_order>0:
            self.combine_neighbor_subgroups(order=self.combine_rest_order,log=self.log)
                       
        self.combine_notC()

        self.emphasize_bridge()

        self.emphasize_conjugated_terminal()

        self.neglect_simple_ring()


        if self.absorb_neighbor_order>0:
            self.absorb_neighbor_subgroups(order=self.absorb_neighbor_order,log=self.log)
        
        return self.return_result(self.log,self.draw,get_index)
        
    def combine_notC(self):        
        if self.log: 
            print("combine_notC")
            print([(i.name,i.atoms,i.priority) for i in self.subgroup_list])
            print()
        concat_targets = []
        adj = self.subgroup_list.adj_mat
        for i,subgroup1 in enumerate(self.subgroup_list):
            if len(subgroup1)!=1 or self.mol.GetAtomWithIdx(int(subgroup1.atoms[0])).GetSymbol()=='C' or adj[i,:].sum()==2: 
                continue
            concat_target,concat_targets = self.get_concat_target(i,concat_targets)
            for j in range(len(self.subgroup_list)):
                if i==j: continue
                if self.subgroup_list.is_neighbor(i,j):
                    concat_target.append(j)
            concat_targets.append(list(set(concat_target)))

        new_concat_targets = []
        for i in range(len(concat_targets)):
            if i>=len(concat_targets): break
            new_target = concat_targets[i].copy()
            concat_targets.remove(concat_targets[i])
            count = 0
            while count<len(concat_targets):
                c = concat_targets[count]
                if set.intersection(set(c),set(new_target)):
                    new_target+=c
                    concat_targets.remove(c)
                    count=0
                    continue
                count+=1
            new_concat_targets.append(list(set(new_target)))

        self.subgroup_list.concat(new_concat_targets,order = '8')
    
    def emphasize_bridge(self):        
        if self.log: 
            print("emphasize_bridge")
            print([(i.name,i.atoms,i.priority) for i in self.subgroup_list])
            print()
        adj = self.subgroup_list.adj_mat
        for i,subgroup1 in enumerate(self.subgroup_list):
            if len(subgroup1)==1: continue
            if adj[i,:].sum()>=3:
                subgroup1.priority='7'

    def emphasize_conjugated_terminal(self):
        if self.log: 
            print("emphasize_conjugated_terminal")
            print([(i.name,i.atoms,i.priority) for i in self.subgroup_list])
            print()
        adj = self.subgroup_list.adj_mat
        for i,subgroup1 in enumerate(self.subgroup_list):
            if len(subgroup1)<=2: continue
            if adj[i,:].sum()!=2: continue
            count=0
            for a in subgroup1.atoms:
                for b in subgroup1.atoms:
                    if a>=b: continue
                    bond = self.mol.GetBondBetweenAtoms(int(a),int(b))
                    if bond and bond.GetIsConjugated():
                        count+=1
                if count>=3: 
                    subgroup1.priority='6'
                    break

    def neglect_simple_ring(self):
        adj = self.subgroup_list.adj_mat
        target_idx=[]
        count = 0
        for i,subgroup1 in enumerate(self.subgroup_list):
            if int(subgroup1.priority)>=7:
                count+=1
                continue
            if len(subgroup1)>=7: continue
            if adj[i,:].sum()>2: continue
            is_simple_ring = True
            
            for a in subgroup1.atoms:
                if not self.mol.GetAtomWithIdx(int(a)).IsInRing(): 
                    is_simple_ring=False
                    break
            if is_simple_ring: 
                target_idx.append(i)
                
        if count<=2:
            return
        else:
            for i in target_idx:
                self.subgroup_list[i].priority='4'

def list2int(l):
    return [int(i) for i in l]
        
def is_overlapped(mol,frag1,frag2):
    for atom1 in frag1:
        if atom1 in frag2: return True
    return False
    
    
def is_neighbor(mol,frag1,frag2):
    for atom1 in frag1:
        for neighbor in mol.GetAtomWithIdx(int(atom1)).GetNeighbors():
            neighbor=neighbor.GetIdx()
            if neighbor in frag1: continue
            if neighbor in frag2: return True
    return False

def concat_frags(frags):
    return list(np.concatenate(frags))

def Concat_overlapped(mol, frags, names, _unoverlapped_result=None, _unoverlapped_result_names=None):
    result = []
    result_names = []
    if _unoverlapped_result is None:
        _unoverlapped_result = frags.copy()
        _unoverlapped_result_names = names.copy()
    unoverlapped_result = []
    unoverlapped_result_names = []

    unused_frags=frags.copy()
    have_concat=False
    for i, frag1 in enumerate(frags):
        if not frag1 in unused_frags: continue
        concat_list=[]
        name_list = []
        unused_frags.remove(frag1)
        used = False
        for frag2 in frags[i+1:]:
            if is_overlapped(mol,frag1,frag2) and frag2 in unused_frags:
                name_list.append(names[frags.index(frag2)])
                concat_list.append(frag2)
                unused_frags.remove(frag2)
                have_concat=True
                used=True
                continue
        if used:
            concat_list.append(frag1)
            name_list.append(names[frags.index(frag1)])
            result_names.append('+'.join(name_list))
            result.append(concat_frags(concat_list))
        else:
            unoverlapped_result.append(frag1)
            unoverlapped_result_names.append(names[frags.index(frag1)])

    new_unoverlapped_result = []
    new_unoverlapped_result_names = []
    for u,n in zip(unoverlapped_result,unoverlapped_result_names):
        if u in _unoverlapped_result: 
            new_unoverlapped_result.append(u)
            new_unoverlapped_result_names.append(n)
        else:
            result.append(u)
            result_names.append(n)
            
    result= [list(np.unique(i)) for i in result]
    if have_concat: result,new_unoverlapped_result,result_names,new_unoverlapped_result_names = Concat_overlapped(
                                                                        mol, result+new_unoverlapped_result, result_names+new_unoverlapped_result_names,
                                                                       new_unoverlapped_result, new_unoverlapped_result_names)
    return result,new_unoverlapped_result,result_names,new_unoverlapped_result_names

import re
def get_fragment_with_branch(smi,at_idx):
    if type(smi)==type(''):
        mol= Chem.MolFromSmiles(smi)
    else:
        mol= smi
    emol=Chem.EditableMol(mol)
    for i in mol.GetBonds():
        bond=[i.GetBeginAtomIdx(),i.GetEndAtomIdx()]
        if len(set.intersection(set(at_idx),set(bond)))==1:
            r=(bond[0] if bond[0] in at_idx else bond[1])
            n=emol.AddAtom(Chem.Atom('*'))
            emol.AddBond(r,n,order=i.GetBondType())
            emol.RemoveBond(bond[0],bond[1])
    rs=(Chem.MolToSmiles(emol.GetMol(),kekuleSmiles=False)).split('.')

    return remove_index(rs[0])

def remove_index(smi):
    return re.sub(r'\[(.)\1{0,1}H\d?\]',r'\1',smi)
    