import numpy as np
import os
import glob
from math import ceil
from collections import Counter
# import time
from data_format.image import Image
from data_format.movement import MOVEMENT
from data_format.outcar import OUTCAR
from data_format.poscar import POSCAR
from data_format.atomconfig import CONFIG
from data_format.movement_saver import save_to_movement
from data_format.extendedxyz import save_to_extxyz
from data_format.build.supercells import make_supercell
from data_format.pertub.perturbation import BatchPerturbStructure
from data_format.pertub.scale import BatchScaleCell
from data_format.const import elements

class Save_Data(object):
    def __init__(self, data_path, datasets_path = "./PWdata", train_data_path = "train", valid_data_path = "valid", 
                 train_ratio = None, random = True, seed = 2024, format = None, retain_raw = False) -> None:
        if format.lower() == "config":
            self.image_data = CONFIG(data_path)
        elif format.lower() == "poscar":
            self.image_data = POSCAR(data_path)
        elif format.lower() == "dump":
            pass
        else:
            assert train_ratio is not None, "train_ratio must be set when format is not config or poscar (inference)"
            self.data_name = os.path.basename(data_path)
            self.labels_path = os.path.join(datasets_path, self.data_name)
            if os.path.exists(datasets_path) is False:
                os.makedirs(datasets_path, exist_ok=True)
            if not os.path.exists(self.labels_path):
                os.makedirs(self.labels_path, exist_ok=True)
            if len(glob.glob(os.path.join(self.labels_path, train_data_path, "*.npy"))) > 0:
                print("Data %s has been processed!" % self.data_name)
                return
            if format.lower() == "movement":
                self.image_data = MOVEMENT(data_path)
            elif format.lower() == "outcar":
                self.image_data = OUTCAR(data_path)
            elif format.lower() == "xyz":
                pass
            elif format.lower() == "xml":
                pass
        self.lattice, self.position, self.energies, self.ei, self.forces, self.virials, self.atom_type, self.atom_types_image, self.image_nums = get_all(self.image_data.get())

        if train_ratio is not None:  # inference 时不存数据
            self.train_ratio = train_ratio        
            self.split_and_save_data(seed, random, self.labels_path, train_data_path, valid_data_path, retain_raw)
    
    def split_and_save_data(self, seed, random, labels_path, train_path, val_path, retain_raw):
        if seed:
            np.random.seed(seed)
        indices = np.arange(self.image_nums)    # 0, 1, 2, ..., image_nums-1
        if random:
            np.random.shuffle(indices)              # shuffle the indices
        train_size = ceil(self.image_nums * self.train_ratio)
        train_indices = indices[:train_size]
        val_indices = indices[train_size:]
        # image_nums = [self.image_nums]
        atom_types_image = self.atom_types_image.reshape(1, -1)

        train_data = [self.lattice[train_indices], self.position[train_indices], self.energies[train_indices], 
                      self.forces[train_indices], atom_types_image, self.atom_type,
                      self.ei[train_indices]]
        val_data = [self.lattice[val_indices], self.position[val_indices], self.energies[val_indices], 
                    self.forces[val_indices], atom_types_image, self.atom_type,
                    self.ei[val_indices]]

        if len(self.virials) != 0:
            train_data.append(self.virials[train_indices])
            val_data.append(self.virials[val_indices])
        else:
            train_data.append([])
            val_data.append([])

        if self.train_ratio == 1.0 or len(val_indices) == 0:
            labels_path = os.path.join(labels_path, train_path)
            if not os.path.exists(labels_path):
                os.makedirs(labels_path)
            if retain_raw:
                self.save_to_raw(train_data, train_path)
            self.save_to_npy(train_data, labels_path)
        else:
            train_path = os.path.join(labels_path, train_path) 
            val_path = os.path.join(labels_path, val_path)
            if not os.path.exists(train_path):
                os.makedirs(train_path)
            if not os.path.exists(val_path):
                os.makedirs(val_path)
            if retain_raw:
                self.save_to_raw(train_data, train_path)
                self.save_to_raw(val_data, val_path)
            self.save_to_npy(train_data, train_path)
            self.save_to_npy(val_data, val_path)
                
    def save_to_raw(self, data, directory):
        filenames = ["lattice.dat", "position.dat", "energies.dat", "forces.dat", "image_type.dat", "atom_type.dat", "ei.dat", "virials.dat"]
        formats = ["%.8f", "%.16f", "%.8f", "%.16f", "%d", "%d", "%.8f", "%.8f"]
        # for i in tqdm(range(len(data)), desc="Saving to raw files"):
        for i in range(len(data)):
            if i != 7 or (i == 7 and len(data[7]) != 0):
                np.savetxt(os.path.join(directory, filenames[i]), data[i], fmt=formats[i])

    def save_to_npy(self, data, directory):
        filenames = ["lattice.npy", "position.npy", "energies.npy", "forces.npy", "image_type.npy", "atom_type.npy", "ei.npy", "virials.npy"]
        # for i in tqdm(range(len(data)), desc="Saving to npy files"):
        for i in range(len(data)):
            if i != 7 or (i == 7 and len(data[7]) != 0):
                np.save(os.path.join(directory, filenames[i]), data[i])
                
class Configs(object):
    @staticmethod
    def read(format: str, data_path: str, pbc = None):
        """ Read the data from the input file. """
        if format.lower() == "config" or format.lower() == 'pwmat':
            image = CONFIG(data_path, pbc).image_list[0]
        elif format.lower() == "poscar" or format.lower() == 'vasp':
            image = POSCAR(data_path, pbc).image_list[0]
        elif format.lower() == "dump":
            image = None
        elif format.lower() == "movement":
            image = MOVEMENT(data_path).image_list
        elif format.lower() == "outcar":
            image = OUTCAR(data_path).image_list
        elif format.lower() == "xyz":
            image = None
        elif format.lower() == "xml":
            image = None
        elif format.lower() == 'cp2k':
            image = None
        else:
            raise Exception("Error! The format of the input file is not supported!")
        return image

    @staticmethod
    def get(image_data: list[Image]):
        """ Get and process the data from the input file. """
        lattice, position, energies, ei, forces, virials, atom_type, atom_types_image, image_nums = get_all(image_data)
        return {"lattice": lattice, "position": position, "energies": energies, "ei": ei, "forces": forces, "virials": virials, "atom_type": atom_type, "atom_types_image": atom_types_image, "image_nums": image_nums}

    @staticmethod
    def save(image_data_dict: dict, datasets_path = "./PWdata", train_data_path = "train", valid_data_path = "valid",
           train_ratio = None, random = True, seed = 2024, retain_raw = False, data_name=None):
        
        lattice = image_data_dict["lattice"]
        position = image_data_dict["position"]
        energies = image_data_dict["energies"]
        ei = image_data_dict["ei"]
        forces = image_data_dict["forces"]
        virials = image_data_dict["virials"]
        atom_type = image_data_dict["atom_type"]
        atom_types_image = image_data_dict["atom_types_image"]
        image_nums = image_data_dict["image_nums"]

        sc = Counter(atom_types_image)  # a list sc of (symbol, count) pairs
        temp_data_name = ''.join([elements[key] + str(count) for key, count in sc.items()])
        suffix = 0
        if data_name is None:
            data_name = temp_data_name
            while os.path.exists(os.path.join(datasets_path, data_name)):
                suffix += 1
                data_name = data_name + "_" + str(suffix)
        else:
            pass
        labels_path = os.path.join(datasets_path, data_name)
        if not os.path.exists(datasets_path):
            os.makedirs(datasets_path, exist_ok=True)
        if not os.path.exists(labels_path):
            os.makedirs(labels_path, exist_ok=True)
        
        if seed:
            np.random.seed(seed)
        indices = np.arange(image_nums)    # 0, 1, 2, ..., image_nums-1
        if random:
            np.random.shuffle(indices)              # shuffle the indices
        assert train_ratio is not None, "train_ratio must be set"
        train_size = ceil(image_nums * train_ratio)
        train_indices = indices[:train_size]
        val_indices = indices[train_size:]
        # image_nums = [image_nums]
        atom_types_image = atom_types_image.reshape(1, -1)

        train_data = [lattice[train_indices], position[train_indices], energies[train_indices],
                        forces[train_indices], atom_types_image, atom_type,
                        ei[train_indices]]
        val_data = [lattice[val_indices], position[val_indices], energies[val_indices],
                        forces[val_indices], atom_types_image, atom_type,
                        ei[val_indices]]
        
        if len(virials) != 0:
            train_data.append(virials[train_indices])
            val_data.append(virials[val_indices])
        else:
            train_data.append([])
            val_data.append([])

        if train_ratio == 1.0 or len(val_indices) == 0:
            labels_path = os.path.join(labels_path, train_data_path)
            if not os.path.exists(labels_path):
                os.makedirs(labels_path)
            if retain_raw:
                Configs.save_to_raw(train_data, train_data_path)
            Configs.save_to_npy(train_data, labels_path)
        else:
            train_path = os.path.join(labels_path, train_data_path) 
            val_path = os.path.join(labels_path, valid_data_path)
            if not os.path.exists(train_path):
                os.makedirs(train_path)
            if not os.path.exists(val_path):
                os.makedirs(val_path)
            if retain_raw:
                Configs.save_to_raw(train_data, train_path)
                Configs.save_to_raw(val_data, val_path)
            Configs.save_to_npy(train_data, train_path)
            Configs.save_to_npy(val_data, val_path)

    @staticmethod   
    def save_to_raw(data, directory):
        filenames = ["lattice.dat", "position.dat", "energies.dat", "forces.dat", "image_type.dat", "atom_type.dat", "ei.dat", "virials.dat"]
        formats = ["%.8f", "%.16f", "%.8f", "%.16f", "%d", "%d", "%.8f", "%.8f"]
        # for i in tqdm(range(len(data)), desc="Saving to raw files"):
        for i in range(len(data)):
            if i != 7 or (i == 7 and len(data[7]) != 0):
                np.savetxt(os.path.join(directory, filenames[i]), data[i], fmt=formats[i])
    @staticmethod
    def save_to_npy(data, directory):
        filenames = ["lattice.npy", "position.npy", "energies.npy", "forces.npy", "image_type.npy", "atom_type.npy", "ei.npy", "virials.npy"]
        # for i in tqdm(range(len(data)), desc="Saving to npy files"):
        for i in range(len(data)):
            if i != 7 or (i == 7 and len(data[7]) != 0):
                np.save(os.path.join(directory, filenames[i]), data[i])

class OUTCAR2MOVEMENT(object):
    def __init__(self, outcar_file, output_path, output_file) -> None:
        """
        Convert OUTCAR file to MOVEMENT file.

        Args:
            outcar_file (str): Path to the OUTCAR file.
            output_path (str): Path to the output directory.
            output_file (str): Name of the output file.

        Returns:
            None
        """
        self.image_data = OUTCAR(outcar_file)
        self.output_path = os.path.abspath(output_path)
        self.output_file = output_file
        self.is_cartesian = True    # data from cartesian coordinates
        save_to_movement(self.image_data.get(), self.output_path, self.output_file, self.is_cartesian)

class MOVEMENT2XYZ(object):
    def __init__(self, movement_file, output_path, output_file) -> None:
        """
        Convert MOVEMENT file to XYZ file.

        Args:
            movement_file (str): Path to the MOVEMENT file.
            output_path (str): Path to the output directory.
            output_file (str): Name of the output file.

        Returns:
            None
        """
        self.image_data = MOVEMENT(movement_file)
        self.output_path = os.path.abspath(output_path)
        self.output_file = output_file
        save_to_extxyz(self.image_data.get(), self.output_path, self.output_file)

class SUPERCELL(object):
    def __init__(self, config: Image, output_path = "./", output_file = "supercell", 
                 supercell_matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]], 
                 direct = True, sort = True, pbc = None, save_format: str = None) -> None:
        """
        Args:
            config (Image): Image object.
            output_path (str): Path to the output directory.
            output_file (str): Name of the output file.
            supercell_matrix (list): supercell matrix (3x3)
            direct (bool): Whether to write the positions in direct coordinates.
            sort (bool): Whether to sort the atoms by atomic number.
            pbc (list): three bool, Periodic boundary conditions flags.  Examples: [True, True, False] or [1, 1, 0]. True (1) means periodic, False (0) means non-periodic.
            save_format (str): Format of the output file.
        """

        self.output_path = os.path.abspath(output_path)
        self.output_file = output_file
        self.supercell_matrix = supercell_matrix   
        # Make a supercell     
        supercell = make_supercell(config, self.supercell_matrix, pbc)
        # Write out the structure
        supercell.to(file_path = self.output_path,
                     file_name = self.output_file,
                     file_format = save_format,
                     direct = direct,
                     sort = sort)
        # from build.write_struc import write_config, write_vasp
        # if format.lower() == "config":
        #     write_config(self.output_path, self.output_file, supercell, direct=direct, sort=sort)
        # elif format.lower() == "poscar":
        #     write_vasp(self.output_path, self.output_file, supercell, direct=direct, sort=sort)

class PerturbStructure(object):
    def __init__(self, perturbed_file: Image, pert_num = 50, cell_pert_fraction = 0.03, atom_pert_distance = 0.01,
                 output_path = "./", direct = True, sort = None, pbc = None, save_format: str = None) -> None:
        """
        Perturb the structure.

        Args:
            perturbed_file (Image): Image object.
            pert_num (int): Number of perturbed structures.
            cell_pert_fraction (float): Fraction of the cell perturbation.
            atom_pert_distance (float): Distance of the atom perturbation.
            output_path (str): Path to the output directory.
            direct (bool): Whether to write the positions in direct coordinates.
            sort (bool): Whether to sort the atoms by atomic number.
            pbc (list): three bool, Periodic boundary conditions flags.  Examples: [True, True, False] or [1, 1, 0]. True (1) means periodic, False (0) means non-periodic.
            save_format (str): Format of the output file.

        Returns:
            None
        """

        self.pert_num = pert_num
        self.cell_pert_fraction = cell_pert_fraction
        self.atom_pert_distance = atom_pert_distance
        self.output_path = os.path.abspath(output_path)
        self.perturbed_structs = BatchPerturbStructure.batch_perturb(perturbed_file, self.pert_num, self.cell_pert_fraction, self.atom_pert_distance)
        for tmp_perturbed_idx, tmp_pertubed_struct in enumerate(self.perturbed_structs):
            tmp_pertubed_struct.to(file_path = self.output_path,
                                   file_name = "{0}_pertubed.{1}".format(tmp_perturbed_idx, save_format.lower()),
                                   file_format = save_format,
                                   direct = direct,
                                   sort = sort) 
        
class ScaleCell(object):
    def __init__(self, scaled_file: Image, scale_factor = 1.0, output_path = "./", direct = True, sort = None, pbc = None, save_format: str = None) -> None:
        """
        Scale the lattice.

        Args:
            scaled_file (Image): Image object.
            scale_factor (float): Scale factor.
            output_path (str): Path to the output directory.
            direct (bool): Whether to write the positions in direct coordinates.
            sort (bool): Whether to sort the atoms by atomic number.
            pbc (list): three bool, Periodic boundary conditions flags.  Examples: [True, True, False] or [1, 1, 0]. True (1) means periodic, False (0) means non-periodic.
            save_format (str): Format of the output file.

        Returns:
            None
        """
        
        self.scale_factor = scale_factor
        self.output_path = os.path.abspath(output_path)
        self.scaled_struct = BatchScaleCell.batch_scale(scaled_file, self.scale_factor)
        self.scaled_struct.to(file_path = self.output_path,
                              file_name = "scaled.{0}".format(save_format.lower()),
                              file_format = save_format,
                              direct = direct,
                              sort = sort)

def get_all(image_data):
    # Initialize variables to store data
    all_lattices = []
    all_postions = []
    all_energies = []
    all_ei = []
    all_forces = []
    all_virials = []
    for image in image_data:
        all_lattices.append(image.lattice)
        all_postions.append(image.position)
        all_energies.append(image.Ep)
        all_forces.append(image.force)
        all_ei.append(image.atomic_energy)
        if len(image.stress) != 0:
            all_virials.append(image.stress)  
    image_nums = len(image_data)
    atom_type = np.array(image.atom_type).reshape(1, -1)
    atom_types_image = np.array(image.atom_types_image)
    all_lattices = np.array(all_lattices).reshape(image_nums, 9)
    all_postions = np.array(all_postions).reshape(image_nums, -1)
    all_energies = np.array(all_energies).reshape(image_nums, 1)
    all_forces = np.array(all_forces).reshape(image_nums, -1)
    all_ei = np.array(all_ei).reshape(image_nums, -1)
    if len(all_virials) != 0:
        all_virials = np.array(all_virials).reshape(image_nums, -1)
    return all_lattices, all_postions, all_energies, all_ei, all_forces, all_virials, atom_type, atom_types_image, image_nums

if __name__ == "__main__":
    import argparse
    SUPERCELL_MATRIX = [[2, 0, 0], [0, 2, 0], [0, 0, 2]]
    # data_file = "/data/home/hfhuang/2_MLFF/2-DP/19-json-version/4-CH4-dbg/atom.config"
    data_file = "/data/home/hfhuang/Si64/44_POSCAR"
    # data_file = "/data/home/hfhuang/software/mlff/Si/Si64-vasprun.xml"
    # data_file = "/data/home/hfhuang/2_MLFF/3-outcar2movement/0/OUTCARC3N4"
    output_path = "/data/home/hfhuang/Si64/"
    output_file = "supercell.pwmat"
    format = "poscar"
    pbc = [1, 1, 1]
    config = Configs.read(format, data_file)
    # SUPERCELL(config, output_path, output_file, SUPERCELL_MATRIX, pbc=pbc, save_format=format)
    # PerturbStructure(config, output_path = "/data/home/hfhuang/Si64", save_format=format)
    # ScaleCell(config, scale_factor = 1.1, output_path = "/data/home/hfhuang/Si64", save_format=format)
    config.to(file_path = output_path,
                     file_name = output_file,
                     file_format = 'lammps',
                     direct = False,
                     sort = False)
    # OUTCAR2MOVEMENT(data_path, output_path, output_file)
    parser = argparse.ArgumentParser(description='Convert and build structures.')
    parser.add_argument('--convert', type=int, required=False, help='Convert OUTCAR to MOVEMENT (1) or MOVEMENT to XYZ (2)')
    parser.add_argument('--format', type=str, required=False, help='Format of the input file', default="outcar")
    parser.add_argument('--outcar_file', type=str, required=False, help='Path to the OUTCAR file')
    parser.add_argument('--movement_file', type=str, required=False, help='Path to the MOVEMENT file')
    parser.add_argument('--output_path', type=str, required=False, help='Path to the output directory', default="./")
    parser.add_argument('--output_file', type=str, required=False, help='Name of the output file', default="MOVEMENT")
    parser.add_argument('--supercell_matrix', type=list, required=False, help='Supercell matrix', default=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    parser.add_argument('--pbc', type=list, required=False, help='Periodic boundary conditions flags', default=[1, 1, 1])
    parser.add_argument('--direct', type=bool, required=False, help='Whether to write the positions in direct (frac) coordinates', default=True)
    parser.add_argument('--sort', type=bool, required=False, help='Whether to sort the atoms by atomic number', default=True)
    parser.add_argument('--pert_num', type=int, required=False, help='Number of perturbed structures', default=50)
    parser.add_argument('--cell_pert_fraction', type=float, required=False, help='Fraction of the cell perturbation', default=0.03)
    parser.add_argument('--atom_pert_distance', type=float, required=False, help='Distance of the atom perturbation', default=0.01)
    parser.add_argument('--retain_raw', type=bool, required=False, help='Whether to retain raw data', default=False)
    parser.add_argument('--train_ratio', type=float, required=False, help='Ratio of training data', default=0.8)
    parser.add_argument('--random', type=bool, required=False, help='Whether to shuffle the data', default=True)
    parser.add_argument('--scale_factor', type=float, required=False, help='Scale factor of the lattice', default=1.0)

    
    args = parser.parse_args()
    
    if args.convert == 1:
        OUTCAR2MOVEMENT(args.outcar_file, args.output_path, args.output_file)
    elif args.convert == 2:
        MOVEMENT2XYZ(args.movement_file, args.output_path, args.output_file)
