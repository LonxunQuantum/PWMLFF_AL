import os
from active_learning.user_input.scf_param import DFTInput
from active_learning.user_input.iter_input import SCFParam
from utils.file_operation import str_list_format
from utils.json_operation import get_parameter, get_required_parameter
from utils.constant import DFT_STYLE

class InitBulkParam(object):
    def __init__(self, json_dict: dict) -> None:
        self.root_dir = get_parameter("work_dir", json_dict, "work_dir")
        if not os.path.isabs(self.root_dir):
            self.root_dir = os.path.realpath(self.root_dir)
        
        self.data_shuffle = get_parameter("data_shuffle", json_dict, True)
        self.train_valid_ratio = get_parameter("train_valid_ratio", json_dict, 0.8)

        # self.reserve_pwmat_files = get_parameter("reserve_pwmat_files", json_dict, False)
        self.reserve_work = get_parameter("reserve_work", json_dict, False)
        # read init configs
        sys_config_prefix = get_parameter("sys_config_prefix", json_dict, None)
        sys_configs = get_required_parameter("sys_configs", json_dict)
        if isinstance(sys_configs, str):
            sys_configs = [sys_configs]

        # set sys_config detail
        self.dft_style = get_required_parameter("dft_style", json_dict).lower()
        self.sys_config:list[Stage] = []
        is_relax = False
        is_aimd = False
        for index, config in enumerate(sys_configs):
            stage = Stage(config, index, sys_config_prefix, self.dft_style)
            self.sys_config.append(stage)
            if stage.relax and is_relax is False:
                is_relax = True
            if stage.aimd and is_aimd is False:
                is_aimd = True
                
        # for PWmat: set etot.input files and persudo files
        # for Vasp: set INCAR files and persudo files
        self.dft_input = SCFParam(json_dict=json_dict, is_relax=is_relax, is_aimd=is_aimd, root_dir=self.root_dir, dft_style=self.dft_style)
        # check and set relax etot.input file
        for config in self.sys_config:
            if config.relax_input_idx >= len(self.dft_input.relax_input_list):
                raise Exception("Error! for config '{}' 'relax_input_idx' {} not in 'relax_input'!".format(os.path.basename(config.config_file), config.relax_input_idx))
            if is_relax:
                config.set_relax_input_file(self.dft_input.relax_input_list[config.relax_input_idx])
        # check and set aimd etot.input file
        for config in self.sys_config:
            if config.aimd_input_idx >= len(self.dft_input.aimd_input_list):
                raise Exception("Error! for config '{}' 'aimd_input_idx' {} not in 'aimd_input'!".format(os.path.basename(config.config_file), config.aimd_input_idx))
            if is_aimd:
                config.set_aimd_input_file(self.dft_input.aimd_input_list[config.aimd_input_idx])

class Stage(object):
    def __init__(self, json_dict: dict, index:int, sys_config_prefix:str = None, dft_style:str=None) -> None:
        self.dft_style = dft_style
        self.config_index = index
        self.use_dftb = False
        self.use_skf = False
        
        config_file = get_required_parameter("config", json_dict)
        self.config_file = os.path.join(sys_config_prefix, config_file) if sys_config_prefix is not None else config_file
        if not os.path.exists:
            raise Exception("ERROR! The sys_config {} file does not exist!".format(self.config_file))
        self.format = get_parameter("format", json_dict, DFT_STYLE.pwmat).lower()
        self.pbc = get_parameter("pbc", json_dict, [1,1,1])
        # extract config file to Config object, then use it
        # self.config = extract_config(self.config_file, self.format)
        self.relax = get_parameter("relax", json_dict, True)
        self.relax_input_idx = get_parameter("relax_input_idx", json_dict, 0)
        self.relax_input_file = None
        
        self.aimd = get_parameter("aimd", json_dict, True)
        self.aimd_input_idx = get_parameter("aimd_input_idx", json_dict, 0)
        self.aimd_input_file = None
         
        super_cell = get_parameter("super_cell", json_dict, [])
        super_cell = str_list_format(super_cell)
        if len(super_cell) > 0:
            if len(super_cell) == 3 :#should c
                if isinstance(super_cell[0], int):
                    super_cell = [[super_cell[0], 0, 0], [0, super_cell[1], 0], [0, 0, super_cell[2]]]
            elif len(super_cell) == 9:
                super_cell = [super_cell[0:3], super_cell[3:6], super_cell[6:9]]
            else:
                raise Exception("Error! The input super_cell should be 3 or 9 values, for example:\
                    list format [1,2,1], [1,0,0,0,2,0,0,0,3]!")
            self.super_cell = super_cell
        else:
            self.super_cell = None
        
        scale = get_parameter("scale", json_dict, [])
        scale = str_list_format(scale)
        if len(scale) > 0:
            self.scale = scale
        else:
            self.scale = None
            
        self.perturb = get_parameter("perturb", json_dict, 3)
        if self.perturb == 0:
            self.perturb = None
        self.cell_pert_fraction = get_parameter("cell_pert_fraction", json_dict, 0.03)
        self.atom_pert_distance = get_parameter("atom_pert_distance", json_dict, 0.01)
    
    def set_relax_input_file(self, input_file:DFTInput):
        self.relax_input_file = input_file.input_file
        self.relax_kspacing = input_file.kspacing 
        self.relax_flag_symm = input_file.flag_symm

    def set_aimd_input_file(self, input_file:DFTInput):
        self.aimd_input_file = input_file.input_file
        self.aimd_kspacing = input_file.kspacing
        self.aimd_flag_symm = input_file.flag_symm
        self.use_dftb = input_file.use_dftb
        self.use_skf = input_file.use_skf