from rdkit import Chem
import numpy as np
from .utils import is_overlapped, get_fragment_with_branch, is_neighbor


class Subgroup():
    "the unit of the fragmentation"
    def __init__(self, mol, atoms, name, priority):
        self.atoms=atoms
        self.name=name
        self.priority=str(priority)
        self.mol = mol if type(mol)==Chem.rdchem.Mol else Chem.MolFromSmiles(mol)
        for atom in mol.GetAtoms():
            atom.SetAtomMapNum(atom.GetIdx()+1) 
        

    def __len__(self):
        return len(self.atoms)

    def add_smiles(self,thrsh=4):
        group_smiles = self.specify_group()
        if group_smiles is None: return
        if len(self.atoms)<=thrsh:
            self.smiles=group_smiles
        else:
            smi=Chem.MolFragmentToSmiles(self.mol,[int(j) for j in self.atoms])
            self.smiles=smi #remove_index(smi)
        # self.atoms = [int(i)-1 for i in re.findall(r'\:(\d+)\]',self.smiles)]

    def specify_group(self):
        # smiles=get_fragment_with_branch(self.mol,self.atoms)
        # if smiles =="*c1ccccc1":
        #     self.name = "Phenyl"
        #     self.smiles = "*c1ccccc1"
        #     return None
        return get_fragment_with_branch(self.mol,self.atoms)


class Subgroup_list():
    "the list of the subgroups for efficiently managing the subgroups"
    def __init__(self, mol, subgroups):
        self.subgroups = subgroups
        self.mol = mol if type(mol)==Chem.rdchem.Mol else Chem.MolFromSmiles(mol)
        
        # 그룹 인접행렬 생성
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
        if type(order) != list: order = [order]*len(idxs_list)
        elif len(order)!=len(idxs_list): 
            raise Exception("Error: order length must be equal to idxs_list length")
        
        delete_idx = []
        for idxs, _order in zip(idxs_list,order):
            if len(idxs)==1: continue
            i = idxs[0]
            for j in idxs[1:]:
                self.subgroups[i].atoms = list(np.concatenate([self.subgroups[i].atoms,self.subgroups[j].atoms]))
                self.subgroups[i].name = self.subgroups[i].name+'+'+self.subgroups[j].name
                self.subgroups[i].priority = _order

                self.adj_mat[i,:]=((self.adj_mat[i,:]+self.adj_mat[j,:])>0)*1
                self.adj_mat[:,i]=((self.adj_mat[:,i]+self.adj_mat[:,j])>0)*1

                delete_idx.append(j)
        delete_idx = list(set(delete_idx))
        if len(delete_idx)==0: return
        self.adj_mat=np.delete(self.adj_mat,delete_idx,axis=0)
        self.adj_mat=np.delete(self.adj_mat,delete_idx,axis=1)
        for j in [self.subgroups[i] for i in delete_idx]:
            self.subgroups.remove(j)

    def get_num_outter_bond(self, idx):
        # args| idx (int) : the index of the subgroup
        # return| list of int : the number of the outter bond of the atoms in the subgroup
        num_list = []
        for a in self.subgroups[idx].atoms:
            count=0
            atom = self.mol.GetAtomWithIdx(int(a))
            for n in atom.GetNeighbors():
                if n.GetIdx() not in self.subgroups[idx].atoms:
                    count+=1
            num_list.append(count)
        return num_list

    def get_atm_idx_of_outter_bond(self,idx):
        # args: idx (int) : the index of the subgroup
        # return: list of list of int: the index of destination atoms of the outter bond of the atoms in the subgroup
        dest_idx_list = []
        for a in self.subgroups[idx].atoms:
            atom = self.mol.GetAtomWithIdx(int(a))
            outter_atom = []
            for n in atom.GetNeighbors():
                if n.GetIdx() not in self.subgroups[idx].atoms:
                    outter_atom.append(n.GetIdx())
            dest_idx_list.append(outter_atom)
        return dest_idx_list

    def get_group_idx_of_outter_bond(self,idx):
        # args: idx (int) : the index of the subgroup
        # return: list of list of int: the index of destination atoms of the outter bond of the atoms in the subgroup
        dest_idx_list = []
        for a in self.subgroups[idx].atoms:
            atom = self.mol.GetAtomWithIdx(int(a))
            outter_atom = []
            for n in atom.GetNeighbors():
                if n.GetIdx() not in self.subgroups[idx].atoms:
                    outter_atom.append(self.get_parent_group_of_atom(n.GetIdx()))
            dest_idx_list.append(outter_atom)
        return dest_idx_list
    
    def get_parent_group_of_atom(self,atom_idx):
        # args: atom_idx (int) : the index of the atom
        # return: int : the index of the parent group of the atom
        for i,subgroup in enumerate(self.subgroups):
            if atom_idx in subgroup.atoms:
                return i
