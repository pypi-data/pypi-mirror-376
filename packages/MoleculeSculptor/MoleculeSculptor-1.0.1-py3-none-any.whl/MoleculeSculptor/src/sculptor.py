
import numpy as np
from rdkit import Chem
import os
import pandas as pd

from .utils import list2int, Concat_overlapped, showAtomHighlight
from .subgroup import Subgroup,Subgroup_list
BASE_DIR = os.path.dirname(os.path.abspath(__file__))




class Segmentator():
    "the class for the Segmentation"
    def __init__(self, s, c, a, combine_overlapped_ring=True):
        """
        Args:
            s   : int
                  the order of the split
            c   : int
                  the order of the combine
            a   : int
                  the order of the assimilation
            combine_overlapped_ring: bool. Default is True
                  if True, the overlapped rings will be combined
        """
        self.ss = SubgroupSplitter(refer_path="./functional_group.csv",
                                   split_order=s,
                                   combine_rest_order=c,
                                   absorb_neighbor_order=a, 
                                   overlapped_ring_combine=combine_overlapped_ring)

    def segment(self, mol, get_only_index=False, draw=False, star_threshold = 4, concat_double_bond_with_ring=False):
        """
        Args:
            mol: str or Chem.rdchem.Mol
                 the molecule to segment
            get_only_index: bool. Default is False
                 if True, the index of the atoms will be returned
                 if False, the Subgroup objects will be returned
            draw: bool. Default is False
                 if True, the molecule with the highlighted atoms will be drawn
        ----------------------------------------------
        Returns:
            list of list of int or Subgroup_list  
        """
        return self.ss.fragmentation_with_condition(mol,get_index=get_only_index,draw=draw,star_threshold = star_threshold, concat_double_bond_with_ring=concat_double_bond_with_ring)


class SubgroupSplitter(object):
    def __init__(self, refer_path=None,
                split_order=6, 
                 combine_rest_order=2,  
                 absorb_neighbor_order=0,  
                                            
                 overlapped_ring_combine=True,  
                 log=False,
                 draw=False,
                get_index=False                
                ):
        
        #self.smiles_list = smiles_list
        refer_path = os.path.join(BASE_DIR, "functional_group.csv")
        data_from = os.path.realpath(refer_path)
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
                                    atom_with_index=False,
                                    star_threshold=4,
                                    concat_double_bond_with_ring=False):
        if split_order is None: split_order=self.split_order
        if overlapped_ring_combine is None: overlapped_ring_combine=self.overlapped_ring_combine
        if combine_rest_order is None: combine_rest_order=self.combine_rest_order
        if absorb_neighbor_order is None: absorb_neighbor_order=self.absorb_neighbor_order
        if log is None: log=self.log
        if draw is None: draw=self.draw
        if get_index is None: get_index=self.get_index
        self.subgroup_list = None
       
    
        if type(mol)==str: mol = Chem.MolFromSmiles(mol)

        #Canonicalize the molecule
        mol = Chem.MolFromSmiles(Chem.MolToSmiles(mol))

        self.mol_size = mol.GetNumAtoms()
        self.mol=mol
        pat_list = self.get_pattern_list(mol)
        
        # 분자내의 모든 패턴을 찾음
        layer_pat_list,layer_sorted_pattern = self.get_masked_pattern_list(pat_list,order=split_order)
                
        # 찾은 패턴 중 유효한 패턴을 찾음
        self.init_subgroup_list(layer_pat_list,layer_sorted_pattern,
                                             log=log,ring_combine=overlapped_ring_combine,mol=mol)
        
        # 이중결합이 있는 그룹이 고리와 이웃한 경우 합침
        if concat_double_bond_with_ring:
            self.combine_double_bond_with_ring()

        # 이웃하는 패턴끼리 합침 
        if combine_rest_order>0:
            self.combine_neighbor_subgroups(order=combine_rest_order,log=log)
                       
        # 주변 고리패턴에 흡수됨
        if absorb_neighbor_order>0:
            self.absorb_neighbor_subgroups(order=absorb_neighbor_order,log=log)
        
        return self.return_result(log,draw,get_index,atom_with_index,star_threshold)
    
    def return_result(self,log=False,draw=False,get_index=False,atom_with_index=True,star_threshold=4):
        atoms = []
        for i in self.subgroup_list:
            for j in self.subgroup_list:
                if i==j: continue
                if set(i.atoms).intersection(set(j.atoms)):
                    raise Exception("Error: overlapped subgroup\n",i.atoms,j.atoms)
            atoms+=i.atoms
        if len(atoms)!=self.mol_size:
            raise Exception("Error: not matched subgroup\n",atoms)

        if log:
            print("return_result")
            print([(i.name,i.atoms,) for i in self.subgroup_list])
        if draw:
            hit_atom_list = [list2int(i.atoms) for i in self.subgroup_list]
            showAtomHighlight(self.mol,hit_atom_list,atom_with_index=atom_with_index)
        
        if get_index:
            return [i.atoms for i in self.subgroup_list]
        else:
            for l in self.subgroup_list:
                l.add_smiles(thrsh = star_threshold)
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
        used_atom_list=[]  # 이미 할당된 원자를 기록
        subgroup_list=[]   # subgroup 객체를 저장할 리스트
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
                                    # subgroup( atoms list, pattern name, priority)
        if ring_combine:
            temporary_ring_list2=[]
            temporary_ring_list2_names=[]
            for i in range(len(temporary_ring_list)):
                if temporary_ring_list[i] not in temporary_ring_list2:
                    temporary_ring_list2.append(temporary_ring_list[i])
                    temporary_ring_list2_names.append(temporary_ring_names[i])
            
            if log: print(temporary_ring_list)
            concated_ring_list, ring_list, concated_names, ring_names =Concat_overlapped(mol,temporary_ring_list2,temporary_ring_list2_names) # 겹치는 고리끼리 합침
            for concated_ring, concated_name in zip(concated_ring_list,concated_names):
                    subgroup_list.append(Subgroup(self.mol,concated_ring,'poly rings','8'))
            for ring, ring_name in zip(ring_list,ring_names):
                    subgroup_list.append(Subgroup(self.mol,ring,ring_name,'6'))
            
        for atom_index in range(self.mol_size): # 할당되지 않은 원자에 우선순위 -1 부여
            if atom_index not in used_atom_list:
                subgroup_list.append(Subgroup(self.mol,[atom_index],'Undefined','-1'))
                

        self.subgroup_list = Subgroup_list(self.mol,subgroup_list)
    
    def combine_double_bond_with_ring(self):
        # 2. 이중결합이 있는 그룹이 고리와 이웃한 경우 합침
        concat_targets = []
        for i,subgroup1 in enumerate(self.subgroup_list):
            if int(subgroup1.priority)>=5:
                for a in subgroup1.atoms:
                    atom = self.mol.GetAtomWithIdx(int(a))
                    # if not atom.GetIsAromatic(): continue
                    for neighbor in atom.GetNeighbors():
                        neighbor=neighbor.GetIdx()
                        if neighbor in subgroup1.atoms: 
                            continue
                        for j,subgroup2 in enumerate(self.subgroup_list):
                            if neighbor in subgroup2.atoms:
                                if len(subgroup2.atoms)!=1: break
                                if self.mol.GetBondBetweenAtoms(int(a),neighbor).GetBondType()==Chem.rdchem.BondType.DOUBLE:
                                    concat_targets.append([i,j])
                                    break
        self.subgroup_list.concat(concat_targets,order = '7')

    def combine_neighbor_subgroups(self,order=1,log=False):
        if log: 
            print("combine_neighbor_subgroups")
            print([(i.name,i.atoms,i.priority) for i in self.subgroup_list])
            print()
    
        concat_targets=[] # 합칠 대상 검색

        for i,subgroup1 in enumerate(self.subgroup_list):  
            if float(subgroup1.priority) < order: # 우선순위가 1보다 작은 그룹을 검색
                concat_targets.append(i)
        self.Concat_neighbor_asAll(concat_targets,order) # 검색된 그룹들끼리 이웃하면 합침

    def absorb_neighbor_subgroups(self,order=5,log=False):
        if log: 
            print("absorb_neighbor_subgroups")
            print([(i.name,i.atoms,i.priority) for i in self.subgroup_list])
            print()
    
        concat_sbjs=[] # 합칠 주체 검색        
        concat_objs=[] # 합칠 대상 검색
        
        for i,subgroup1 in enumerate(self.subgroup_list): 
            if float(subgroup1.priority) >= order: # 우선순위가 5이상인 큰 그룹을 검색
                concat_sbjs.append(i)
            else: # 우선순위가 5보다 작은 그룹을 검색
                concat_objs.append(i)
        self.Concat_neighbor_asSubject(concat_sbjs,concat_objs) # 대상이 주체와 이웃하면 합침
        
    

    def Concat_neighbor_asAll(self,frags,order = 1): # frags내의 인접한 frag를 합쳐서 출력
        concat_targets= []
    
        for i in range(len(frags)):
            concat_target,concat_targets = self.get_concat_target(frags[i],concat_targets)
            for j in range(i+1,len(frags)):
                if self.subgroup_list.is_neighbor(frags[i],frags[j]):
                    concat_target.append(frags[j])
            concat_targets.append(list(set(concat_target)))
        self.subgroup_list.concat(concat_targets,order = str(order))

    def Concat_neighbor_asSubject(self,sbjs,objs): # sbjs 중심으로 주변의 objs를 합쳐서 출력
        concat_targets= [[sbj] for sbj in sbjs]
        used_obj = []
        for sbj in sbjs.copy():
            concat_target,concat_targets = self.get_concat_target(sbj,concat_targets)
            for obj in objs:
                if self.subgroup_list.is_neighbor(sbj,obj) and obj not in used_obj:
                    concat_target.append(obj)
                    used_obj.append(obj)
            concat_targets.append(list(set(concat_target)))
        orders = []
        for group in concat_targets:
            max_order = max([int(self.subgroup_list[i].priority) for i in group])
            orders.append(max_order)
        self.subgroup_list.concat(concat_targets,order = orders)
        
    @staticmethod
    def get_concat_target(i,concat_targets):
        # concat_targets에서 i가 포함된 concat_target을 찾고 concat_targets에서 제거
        # concat_target이 없으면 i를 포함하는 concat_target을 생성
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
                split_order=6, # 나누기 위한 최대 단위 - 클 수록 더 큰 단위가 우선적으로 고려됨
                 overlapped_ring_combine=False,  # 겹치는 고리를 합칠 것인지 여부
                 combine_rest_order=1,  # <order> 이하의 그룹은 하나로 묶음, -1이면 묶지 않음
                 absorb_neighbor_order=-1,  # <order> 이하의 그룹은 <order> 이상의 그룹에 묶임, 
                                            # -1이면 묶지 않음
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
        
        # 분자내의 모든 패턴을 찾음
        layer_pat_list,layer_sorted_pattern = self.get_masked_pattern_list(pat_list,order=self.split_order)
                
        # 찾은 패턴 중 유효한 패턴을 찾음
        self.init_subgroup_list(layer_pat_list,layer_sorted_pattern,
                                             log=self.log,ring_combine=self.overlapped_ring_combine,mol=mol)
        
        # 이웃하는 패턴끼리 합침 
        if self.combine_rest_order>0:
            self.combine_neighbor_subgroups(order=self.combine_rest_order,log=self.log)
                       
        # 1. 카본이 아닌 원자가 두개이상의 그룹과 이웃한 경우 모두 하나로 합침
        self.combine_notC()

        # 3. 두개 이상의 원자로 이루어진 체인이 두개 이상의 그룹과 이웃한 경우 우선순위를 높여서 합쳐지지 않도록 함
        self.emphasize_bridge()

        # 4. 세개 이상의 원자로 이루어진 체인 중 하나의 그룹과 이웃한 경우 aromacity가 있으면 우선순위를 높여서 합쳐지지 않도록 함
        self.emphasize_conjugated_terminal()

        # 5. 링이 한개의 그룹과 이웃한 경우 현재 우선순위가 낮으면 합쳐지도록 함
        #     - 이를 위해 기본 링/가지가 있는 링/폴리사이클링 에 따라 우선순위를 부여함
        self.neglect_simple_ring()


        # 주변 고리패턴에 흡수됨
        if self.absorb_neighbor_order>0:
            self.absorb_neighbor_subgroups(order=self.absorb_neighbor_order,log=self.log)
        
        return self.return_result(self.log,self.draw,get_index)
        
    def combine_notC(self):        
        if self.log: 
            print("combine_notC")
            print([(i.name,i.atoms,i.priority) for i in self.subgroup_list])
            print()
        # 1. 카본이 아닌 원자가 두개이상의 그룹과 이웃한 경우 모두 하나로 합침
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
        # 3. 두개 이상의 원자로 이루어진 체인이 두개 이상의 그룹과 이웃한 경우 우선순위를 높여서 합쳐지지 않도록 함
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
        # 4. 세개 이상의 원자로 이루어진 체인 중 하나의 그룹과 이웃한 경우 conjugated되어 있으면 우선순위를 높여서 합쳐지지 않도록 함        
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
        # 5. 링이 한개의 그룹과 이웃한 경우 현재 우선순위가 낮으면 합쳐지도록 함
        #     - 이를 위해 기본 링/가지가 있는 링/폴리사이클링 에 따라 우선순위를 부여함
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
        


    
    

