from rdkit import Chem
import re
import numpy as np
from rdkit.Chem import Draw
import io
import PIL
import matplotlib.pyplot as plt


def get_fragment_with_branch(smi,at_idx):
    if type(smi)==type(''):
        mol= Chem.MolFromSmiles(smi)
    else:
        mol= smi
    mol = remove_index_from_mol(mol)
    smi = Chem.MolToSmiles(mol, allHsExplicit=False, allBondsExplicit=False)
    mol = Chem.MolFromSmiles(smi)
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
    
def remove_index_from_mol(mol):
    for atom in mol.GetAtoms():
        atom.SetAtomMapNum(0)
    return mol



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
    

def showAtomHighlight(mol,atms_list,atom_with_index=True):
    """Draw the molecule with atom highlight
    Args:
        mol: str or rdkit.Chem.Mol
            the molecule to draw
        atms_list: list of list of int e.g [[0,1,2],[3,4,5]]
            the list of atoms to highlight. the list of atoms will be drawn with different colors.
        atom_with_index: bool
            if True, the atom index will be shown

    """
    if type(mol) is str:
        mol = Chem.MolFromSmiles(mol)
    atom_num = mol.GetNumAtoms()
    if atom_with_index:
        mol=mol_with_atom_index(mol)
    hit_ats=[]
    hit_bonds = []
    hit_ats_colormap={}
    hit_bonds_colormap={}
    
    colormap=[(1.0, 0.75, 0.79),
               (1.0, 1.0, 0.6),
               (0.74, 0.99, 0.79),
               (0.68, 0.85, 0.90),
               (0.87, 0.63, 0.87),
               (0.90, 0.90, 0.98),
               (0.82, 0.94, 0.75),
               (0.56, 0.93, 0.56),
               (0.50, 1.0, 0.83),
               (0.80, 0.60, 1.0),
               (1.0, 0.85, 0.73),
               (1.0, 1.0, 0.6),
               (0.53, 0.81, 0.92),
               (1.0, 0.75, 0.79),
               (1.0, 0.94, 0.84)
              ]
    for count,atms in enumerate(atms_list):
        atms = [int(x) for x in atms]
        hit_ats=hit_ats+atms
        for i in range(len(atms)):
            hit_ats_colormap[atms[i]]=colormap[count%len(colormap)]
            for j in range(i+1,len(atms)):
                bond=mol.GetBondBetweenAtoms(atms[i],atms[j])
                if bond:
                    bond_index=bond.GetIdx()
                    hit_bonds.append(bond_index)
                    hit_bonds_colormap[bond_index]=colormap[count%len(colormap)]
                    
                    
    d = Draw.MolDraw2DCairo(1000, 800)
    d.DrawMolecule(mol,highlightAtoms = hit_ats, highlightAtomColors=hit_ats_colormap,
                   highlightBonds=hit_bonds, highlightBondColors=hit_bonds_colormap)
    d.FinishDrawing()
    d = d.GetDrawingText()
    
    img_buf = io.BytesIO(d)
    plot(img_buf)

def plot(buf):
    image = PIL.Image.open(buf)

    plt.imshow(image)
    plt.axis('off')
    plt.show()

def mol_with_atom_index( mol ):
    "Return the mol object with atom index"
    if type(mol) is str:
        mol = Chem.MolFromSmiles(mol)
    atoms = mol.GetNumAtoms()
    for idx in range( atoms ):
        mol.GetAtomWithIdx( idx ).SetProp( 'molAtomMapNumber', str( mol.GetAtomWithIdx( idx ).GetIdx() ) )
    return mol
