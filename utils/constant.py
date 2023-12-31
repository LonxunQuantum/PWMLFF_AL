from enum import Enum

class AL_STRUCTURE:
    train = "train"
    explore = "explore"
    labeling = "label"

class TRAIN_FILE_STRUCTUR:
    work_dir = "work_dir"
    feature_dir = "feature"
    feature_json = "feature.json"
    feature_job = "feature.job"
    feature_tag = "tag.feature.success"
    train_json = "train.json"
    train_job = "train.job"
    train_tag = "tag.train.success"
    
    kpu_json = "kpu.json"
    kpu_tag = "tag.kpu.success"
    kpu_tag_failed = "tag.kpu.failed"
    kpu_job = "kpu.job"
    kpu = "kpu"
    kpu_file = "kpu_info.csv"
    base_kpu = "base_kpu"
    
    movement = "MOVEMENT"
    model_record = "model_record"
    dp_model_name ="dp_model.ckpt"
    compree_dp_name = "cmp_cp_model.ckpt"
    # cmp_tracing_dp_name = "torch_script_module.pt"
    script_dp_name = "torch_script_module.pt"
    fortran_dp = "forcefield"
    fortran_dp_name = "forcefield.ff"

class EXPLORE_FILE_STRUCTURE:
    md = "md"
    select = "select"
    md_tag = "tag.md.success"
    md_tag_faild = "tag.md.error"
    md_job = "md.job"
    # selected image info file names
    candidate = "candidate.csv"
    # candidate_random = "candidate_random.csv"
    candidate_delete = "candidate_delete.csv"
    failed = "fail.csv"
    accurate = "accurate.csv"
    select_summary = "select_summary.txt"

    tarj ="traj"
    
    # for committee method 
    model_devi = "model_deviation.out"
    model_devi_force = 2 # the model deviation foce data row in model_deviation.out file
    model_devi_energy = 1
    model_devi_step = 0
    
    
class LABEL_FILE_STRUCTURE:
    scf = "scf"
    result = "result"
    scf_tag = "tag.scf.success"
    fail_scf_tag = "tag.scf.failed"
    scf_job = "scf.job"
    
    
class MODEL_CMD:
    train = "train"
    gen_feat = "gen_feat"
    test = "test"
    script = "script"
    compress = "compress"
    kpu = "kpu"
    
class SCF_FILE_STRUCTUR:
    NCPP = "NCPP-SG15-PBE"

class TRAIN_INPUT_PARAM:
    train_mvm_files = "train_movement_file"
    train_feature_path = "train_feature_path"
    test_mvm_files = "test_movement_file"
    reserve_feature = "reserve_feature" #False
    reserve_work_dir = "reserve_work_dir" #False
    valid_shuffle = "valid_shuffle" #True
    train_valid_ratio = "train_valid_ratio" #0.8
    sample_nums ="sample_nums" # for kpu or test nums
    seed = "seed" #2023
    recover_train = "recover_train" #true
    type_embedding = "type_embedding"
    model_type = "model_type"
    atom_type = "atom_type"
    model_load_file = "model_load_file"
    test_dir_name = "test_dir_name"

class LAMMPSFILE:
    input_lammps="in.lammps"
    vasp_sys_config = "POSCAR"
    lammps_sys_config = "lmp.config"

class PWMAT:
    config_postfix = ".config"
    atom_config = "atom.config"
    etot_input = "etot.input"
    out_mlmd = "OUT.MLMD"
    mvm = "mvm"
    
class FORCEFILED:
    fortran_lmps = 1 #
    libtorch_lmps = 2 # default
    main_md = 3 #

class ENSEMBLE:
    npt_tri = "npt_tri",
    nvt = "nvt"
    npt = "npt"
    nve = "nve"
    
class UNCERTAINTY:
    kpu = "KPU"
    committee="COMMITTEE"

ELEMENTTABLE={'H': 1,
    'He': 2,  'Li': 3,  'Be': 4,  'B': 5,   'C': 6,   'N': 7,   'O': 8,   'F': 9,   'Ne': 10,  'Na': 11,
    'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15,  'S': 16,  'Cl': 17, 'Ar': 18, 'K': 19,  'Ca': 20,  'Sc': 21,
    'Ti': 22, 'V': 23,  'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30,  'Ga': 31,
    'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39,  'Zr': 40,  'Nb': 41, 
    'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50,  'Sb': 51, 
    'Te': 52, 'I': 53,  'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60,  'Pm': 61,
    'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70,  'Lu': 71, 
    'Hf': 72, 'Ta': 73, 'W': 74,  'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80,  'Tl': 81, 
    'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90,  'Pa': 91, 
    'U': 92,  'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100, 'Md': 101,
    'No': 102,'Lr': 103,'Rf': 104,'Db': 105,'Sg': 106,'Bh': 107,'Hs': 108,'Mt': 109,'Ds': 110,'Rg': 111,
    'Uub': 112
    }

ELEMENTTABLE_2 = {1: 'H', 
    2: 'He',     3: 'Li',   4: 'Be',   5: 'B',    6: 'C',    7: 'N',   8: 'O',     9: 'F',   10: 'Ne',  11: 'Na', 
    12: 'Mg',   13: 'Al',  14: 'Si',  15: 'P',   16: 'S',   17: 'Cl',  18: 'Ar',  19: 'K',   20: 'Ca',  21: 'Sc', 
    22: 'Ti',   23: 'V',   24: 'Cr',  25: 'Mn',  26: 'Fe',  27: 'Co',  28: 'Ni',  29: 'Cu',  30: 'Zn',  31: 'Ga', 
    32: 'Ge',   33: 'As',  34: 'Se',  35: 'Br',  36: 'Kr',  37: 'Rb',  38: 'Sr',  39: 'Y',   40: 'Zr',  41: 'Nb', 
    42: 'Mo',   43: 'Tc',  44: 'Ru',  45: 'Rh',  46: 'Pd',  47: 'Ag',  48: 'Cd',  49: 'In',  50: 'Sn',  51: 'Sb', 
    52: 'Te',   53: 'I',   54: 'Xe',  55: 'Cs',  56: 'Ba',  57: 'La',  58: 'Ce',  59: 'Pr',  60: 'Nd',  61: 'Pm', 
    62: 'Sm',   63: 'Eu',  64: 'Gd',  65: 'Tb',  66: 'Dy',  67: 'Ho',  68: 'Er',  69: 'Tm',  70: 'Yb',  71: 'Lu', 
    72: 'Hf',   73: 'Ta',  74:  'W',  75: 'Re',  76: 'Os',  77: 'Ir',  78: 'Pt',  79: 'Au',  80: 'Hg',  81: 'Tl', 
    82: 'Pb',   83: 'Bi',  84: 'Po',  85: 'At',  86: 'Rn',  87: 'Fr',  88: 'Ra',  89: 'Ac',  90: 'Th',  91: 'Pa', 
    92: 'U',    93: 'Np',  94: 'Pu',  95: 'Am',  96: 'Cm',  97: 'Bk',  98: 'Cf',  99: 'Es', 100: 'Fm', 101: 'Md', 
    102: 'No', 103: 'Lr', 104: 'Rf', 105: 'Db', 106: 'Sg', 107: 'Bh', 108: 'Hs', 109: 'Mt', 110: 'Ds', 111: 'Rg', 
    112: 'Uub'
    }
ELEMENTMASSTABLE={  1:1.007,2:4.002,3:6.941,4:9.012,5:10.811,6:12.011,
                            7:14.007,8:15.999,9:18.998,10:20.18,11:22.99,12:24.305,
                            13:26.982,14:28.086,15:30.974,16:32.065,17:35.453,
                            18:39.948,19:39.098,20:40.078,21:44.956,22:47.867,
                            23:50.942,24:51.996,25:54.938,26:55.845,27:58.933,
                            28:58.693,29:63.546,30:65.38,31:69.723,32:72.64,33:74.922,
                            34:78.96,35:79.904,36:83.798,37:85.468,38:87.62,39:88.906,
                            40:91.224,41:92.906,42:95.96,43:98,44:101.07,45:102.906,46:106.42,
                            47:107.868,48:112.411,49:114.818,50:118.71,51:121.76,52:127.6,
                            53:126.904,54:131.293,55:132.905,56:137.327,57:138.905,58:140.116,
                            59:140.908,60:144.242,61:145,62:150.36,63:151.964,64:157.25,65:158.925,
                            66:162.5,67:164.93,68:167.259,69:168.934,70:173.054,71:174.967,72:178.49,
                            73:180.948,74:183.84,75:186.207,76:190.23,77:192.217,78:195.084,
                            79:196.967,80:200.59,81:204.383,82:207.2,83:208.98,84:210,85:210,86:222,
                            87:223,88:226,89:227,90:232.038,91:231.036,92:238.029,93:237,94:244,
                            95:243,96:247,97:247,98:251,99:252,100:257,101:258,102:259,103:262,104:261,105:262,106:266}