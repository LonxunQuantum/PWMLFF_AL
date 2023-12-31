"""
    dir of explore:
    iter.0000/explore/md:
    --------------------/*-md.job file
    --------------------/*-md.tag.success file
    --------------------/md.000.sys.000/ dir
    -----------------------------------/md.000.sys.000.t.000.p.000 or md.000.sys.000.t.000 dir
    -------------------------------------------------------------/md files: lmp.config, in.lammps, forcefile files, model_devi file
    -------------------------------------------------------------/trajs
    iter.0000/explore/select:
    -------------------/summary.txt
    -------------------/accurate.txt candidate.txt failed.txt candidate_del.txt
    the content of candidate.txt is:
            traj_file_path1 index1
            traj_file_path2 index2
            ...
"""
from active_learning.slurm import Mission, SlurmJob, get_slurm_sbatch_cmd
from active_learning.user_input.resource import Resource
from active_learning.user_input.param_input import InputParam, MdDetail
from utils.constant import AL_STRUCTURE, EXPLORE_FILE_STRUCTURE,FORCEFILED, ENSEMBLE, LAMMPSFILE, PWMAT, TRAIN_FILE_STRUCTUR, EXPLORE_FILE_STRUCTURE
from utils.format_input_output import get_iter_from_iter_name, get_sub_md_sys_template_name,\
    make_md_sys_name, make_temp_press_name, make_temp_name, make_train_name
from utils.file_operation import save_json_file, write_to_file, copy_file, get_file_extension, link_file, read_data
from utils.slurm_script import CONDA_ENV, CPU_SCRIPT_HEAD, GPU_SCRIPT_HEAD, get_slurm_job_run_info, set_slurm_comm_basis, split_job_for_group
from utils.app_lib.lammps import make_lammps_input
from utils.app_lib.pwmat import atom_config_to_lammps_in, poscar_to_lammps_in

import os
import json
import sys
import time
import pandas as pd
"""
md_dir:
  a. pwmat+dpkf run md ->MOVEMENT
md_dpkf_dir:
  b. step a.MOVEMENT add Atomic-Energy block ->MOVEMENT
md_traj_dir:
  c. step a.MOVEMENT add Atomic-Energy block ->seperate MOVEMENT to atom.configs
kpu_dir:
  d. step b. calculate KPU of each image(MD)
  f. step d. select cadidate set by limited Delta0 and Delta1
"""
class Explore(object):
    def __init__(self, itername:str, resource: Resource, input_param:InputParam):
        self.itername = itername
        self.iter = get_iter_from_iter_name(self.itername)
        self.resouce = resource
        self.input_param = input_param
        self.sys_paths = self.input_param.explore.sys_configs
        self.md_job = self.input_param.explore.md_job_list[self.iter]
        # md work dir
        self.explore_dir = os.path.join(self.input_param.root_dir, itername, AL_STRUCTURE.explore)
        self.md_dir = os.path.join(self.explore_dir, EXPLORE_FILE_STRUCTURE.md)
        self.select_dir = os.path.join(self.explore_dir, EXPLORE_FILE_STRUCTURE.select)
        
    def make_md_work(self):
        md_work_list = []
        for md_index, md in enumerate(self.md_job):
            for sys_index in md.sys_idx:
                char_len = 3 if len(md.sys_idx) < 1000 else len(str(len(md.sys_idx)))
                md_sys_name = make_md_sys_name(md_index, sys_index, char_len)
                md_sys_dir = os.path.join(self.md_dir, md_sys_name)
                if not os.path.exists(md_sys_dir):
                    os.makedirs(md_sys_dir)
                for temp_index, temp in enumerate(md.temp_list):
                    if ENSEMBLE.nvt in md.ensemble:#for nvt ensemble
                        temp_name = make_temp_name(md_index, sys_index, temp_index, char_len)
                        temp_dir = os.path.join(md_sys_dir, temp_name)
                        # mkdir: md.000.sys.000/md.000.sys.000.t.000
                        if not os.path.exists(temp_dir):
                            os.makedirs(temp_dir)
                        self.set_md_files(temp_dir, sys_index, temp_index, None, md)
                        md_work_list.append(temp_dir)
                    elif ENSEMBLE.npt in md.ensemble: # for npt ensemble
                        for press_index, press in enumerate(md.press_list):
                            temp_press_name = make_temp_press_name(md_index, sys_index, temp_index, press_index, char_len)
                            temp_press_dir = os.path.join(md_sys_dir, temp_press_name)
                            # mkdir: md.000.sys.000/md.000.sys.000.p.000.t.000
                            if not os.path.exists(temp_press_dir):
                                os.makedirs(temp_press_dir)
                            self.set_md_files(len(md_work_list), temp_press_dir, sys_index, temp_index, press_index, md)
                            md_work_list.append(temp_press_dir)
                            
        self.make_md_slurm_jobs(md_work_list)
             
    def make_md_slurm_jobs(self, md_work_list:list[str]):
        #4. set slurm job file
        group_list = split_job_for_group(self.resouce.explore_resource.group_size, md_work_list)
        for g_index, group in enumerate(group_list):
            if group[0] == "NONE":
                continue
            jobname = "md{}".format(g_index)
            tag_name = "{}-{}".format(g_index, EXPLORE_FILE_STRUCTURE.md_tag)
            tag = os.path.join(self.md_dir, tag_name)
            slurm_job_script = self.set_md_slurm_job_script(group, jobname, tag)
            slurm_script_name = "{}-{}".format(g_index, EXPLORE_FILE_STRUCTURE.md_job)
            slurm_job_file = os.path.join(self.md_dir, slurm_script_name)
            write_to_file(slurm_job_file, slurm_job_script, "w")
        
        
    def set_md_files(self, md_index:int, md_dir:str, sys_index:int, temp_index:int, press_index:int, md_detail:MdDetail):
        #1. set sys.config file
        config_path = self.set_lammps_in_file(md_dir, self.sys_paths[sys_index])
        
        #2. set forcefiled file
        md_model_paths = self.set_forcefiled_file(md_dir)
        
        #3. set lammps input file
        input_lammps_file = os.path.join(md_dir, LAMMPSFILE.input_lammps)
        press=md_detail.press_list[press_index] if press_index is not None else None
        lmp_input_content = make_lammps_input(
                        md_file=LAMMPSFILE.input_lammps, #save_file
                        md_type = self.input_param.strategy.md_type,
                        forcefiled = md_model_paths,
                        ensemble = md_detail.ensemble,
                        nsteps = md_detail.nsteps,
                        dt = md_detail.md_dt,
                        neigh_modify = md_detail.neigh_modify,
                        trj_freq = md_detail.trj_freq,
                        mass = md_detail.mass,
                        temp = md_detail.temp_list[temp_index],
                        tau_t=md_detail.taut, # for fix
                        press=press,
                        tau_p=md_detail.taup if press is not None else None, # for fix    
                        boundary=True, #true is 'p p p', false is 'f f f'
                        merge_traj=md_detail.merge_traj
        )
        write_to_file(input_lammps_file, lmp_input_content, "w")
        
    '''
    description: 
        copy sys.config to md dir, then,
        if the sys.config is atom.config or poscar format, convert to lammps.in format
    param {*} self
    param {str} md_dir
    param {str} sys_file
    return {*}
    author: wuxingxing
    '''
    def set_lammps_in_file(self, md_dir:str, sys_file:str):
        # copy sys.config to md_dir
        sys_config_name = os.path.basename(sys_file)
        # convert atom.config to lammps.init file
        if get_file_extension(sys_config_name).upper() in PWMAT.atom_config.upper():
            target_sys_config = os.path.join(md_dir, PWMAT.atom_config)
            link_file(sys_file, target_sys_config)
            atom_config_to_lammps_in(md_dir)
        # convert poscar to lammps.init file
        elif get_file_extension(sys_config_name).upper() in LAMMPSFILE.vasp_sys_config.upper():
            target_sys_config = os.path.join(md_dir, LAMMPSFILE.vasp_sys_config)
            link_file(sys_file, target_sys_config)
            poscar_to_lammps_in(md_dir)
        else:
            print("The lammps input file type {} is lammps format.".format(sys_config_name))
        return target_sys_config
    
    '''
    description: 

    param {*} self
    param {str} md_dir
    param {list} forcefile
    return {*}
    author: wuxingxing
    '''    
    def set_forcefiled_file(self, md_dir:str):
        model_name = ""
        md_model_paths = []
        if self.input_param.strategy.md_type == FORCEFILED.libtorch_lmps:
            model_name += TRAIN_FILE_STRUCTUR.script_dp_name
        elif self.input_param.strategy.md_type == FORCEFILED.fortran_lmps:
            if self.input_param.strategy.compress:
                raise Exception("ERROR! The compress model does not support fortran lammps md! Please change the 'md_type' to 2!")
            else:
                model_name += "{}/{}".format(TRAIN_FILE_STRUCTUR.fortran_dp, TRAIN_FILE_STRUCTUR.fortran_dp_name)

        for model_index in range(self.input_param.strategy.model_num):
            model_name_i = "{}/{}".format(make_train_name(model_index), model_name)
            source_model_path = os.path.join(self.input_param.root_dir, self.itername, AL_STRUCTURE.train, model_name_i)
            target_model_path = os.path.join(md_dir, "{}_{}".format(model_index, os.path.basename(source_model_path)))
            link_file(source_model_path, target_model_path)
            md_model_paths.append(target_model_path)
        return md_model_paths
    
    def set_md_slurm_job_script(self, group:list[str], job_name:str, tag:str):
        # set head
        script = ""
        if self.resouce.explore_resource.gpu_per_node is None or\
            self.resouce.explore_resource.gpu_per_node == 0:
            script += CPU_SCRIPT_HEAD.format(job_name, \
                self.resouce.explore_resource.number_node,\
                self.resouce.explore_resource.cpu_per_node,\
                    self.resouce.explore_resource.queue_name)
            mpirun_cmd_template = "mpirun -np {} lmp_mpi -in {}\n"\
                .format(self.resouce.explore_resource.cpu_per_node, \
                        LAMMPSFILE.input_lammps)
            
        else:
            script += GPU_SCRIPT_HEAD.format(job_name, \
                self.resouce.explore_resource.number_node,\
                self.resouce.explore_resource.gpu_per_node,\
                    self.resouce.explore_resource.gpu_per_node,\
                    1,\
                    self.resouce.explore_resource.queue_name)
            mpirun_cmd_template = "mpirun -np {} lmp_mpi -in {}\n"\
                .format(self.resouce.explore_resource.gpu_per_node,\
                        self.resouce.explore_resource.gpu_per_node,\
                        LAMMPSFILE.input_lammps)
                            
        script += set_slurm_comm_basis(self.resouce.explore_resource.custom_flags, \
            self.resouce.explore_resource.source_list, \
                self.resouce.explore_resource.module_list)
        
        # set conda env
        script += "\n"
        script += CONDA_ENV
        
        script += "\n"
        
        
        script += "start=$(date +%s)\n"
        
        md_cmd = ""
        for md_dir in group:
            if md_dir == "NONE":
                continue
            md_cmd += "cd {}\n".format(md_dir)
            md_cmd += "if [ ! -f {} ] ; then\n".format(EXPLORE_FILE_STRUCTURE.md_tag)
            md_cmd += mpirun_cmd_template
            md_cmd += "    if test $? -eq 0; then touch {}; else echo 1 >> {}; fi\n".format(EXPLORE_FILE_STRUCTURE.md_tag, EXPLORE_FILE_STRUCTURE.md_tag_faild)
            md_cmd += "fi &\n"
            md_cmd += "wait\n\n"
            
        script += md_cmd
        script += "end=$(date +%s)\n"
        script += "take=$(( end - start ))\n"
        script += "echo Time taken to execute commands is ${{take}} seconds > {}\n".format(tag)
        script += "\n"
        return script
    
    '''
    description: 
        waiting: if need set group size, make new script: work1 wait; work2 wait; ...
    param {*} self
    param {list} md_work_list
    return {*}
    author: wuxingxing
    '''    
    def do_md_jobs(self):
        mission = Mission()
        slurm_remain, slurm_done = get_slurm_job_run_info(self.md_dir, \
            job_patten="*-{}".format(EXPLORE_FILE_STRUCTURE.md_job), \
            tag_patten="*-{}".format(EXPLORE_FILE_STRUCTURE.md_tag))
        slurm_done = True if len(slurm_remain) == 0 and len(slurm_done) > 0 else False
        if slurm_done == False:
            #recover slurm jobs
            if len(slurm_remain) > 0:
                print("Doing these MD Jobs:\n")
                print(slurm_remain)
                for i, script_path in enumerate(slurm_remain):
                    slurm_cmd = get_slurm_sbatch_cmd(os.path.dirname(script_path), os.path.basename(script_path))
                    slurm_job = SlurmJob()
                    tag_name = "{}-{}".format(os.path.basename(script_path).split('-')[0].strip(), EXPLORE_FILE_STRUCTURE.md_tag)
                    tag = os.path.join(os.path.dirname(script_path),tag_name)
                    slurm_job.set_tag(tag)
                    slurm_job.set_cmd(slurm_cmd, os.path.dirname(script_path))
                    mission.add_job(slurm_job)

            if len(mission.job_list) > 0:
                mission.commit_jobs()
                mission.check_running_job()
                mission.all_job_finished()
                mission.move_slurm_log_to_slurm_work_dir()
        
    def post_process_md(self):
        pass
    
    '''
    description: 
    select structure of system by model deviation (committee method)
    the candidate.csv columns is ["devi_force", "file_path", "config_index"]
    param {*} self
    return {*}
    author: wuxingxing
    '''    
    def select_image_by_committee(self):
        #1. get model_deviation file
        model_deviation_patten = "{}/{}".format(get_sub_md_sys_template_name(), EXPLORE_FILE_STRUCTURE.model_devi)
        model_devi_files = glob.glob(os.path.join(self.md_dir, model_deviation_patten))
        model_devi_files = sorted(model_devi_files)
        
        #2. for each file, read the model_deviation
        devi_pd = pd.DataFrame(columns=["devi_force", "file_path", "config_index"])
        for devi_file in model_devi_files:
            devi_force = read_data(devi_file)
            tmp_pd = pd.DataFrame()
            tmp_pd["devi_force"] = devi_force[EXPLORE_FILE_STRUCTURE.model_devi_force]
            tmp_pd["config_index"] = devi_force[EXPLORE_FILE_STRUCTURE.model_devi_step]
            tmp_pd["file_path"] = os.path.dirname(devi_file)
            devi_pd = pd.concat([devi_pd, tmp_pd])
        
        #3. select images with lower and upper limitation
        lower = self.input_param.strategy.lower_model_deiv_f
        higer = self.input_param.strategy.upper_model_deiv_f
        max_select = self.input_param.strategy.max_select
        accurate_pd  = devi_pd[devi_pd['devi_force'] < lower]
        candidate_pd = devi_pd[devi_pd['devi_force'] >= lower and devi_pd['devi_force'] < higer]
        error_pd     = devi_pd[devi_pd['devi_force'] > higer]
        #4. if selected images more than number limitaions, randomly select
        remove_candi = None
        rand_candi = None
        if candidate_pd.shape[0] > max_select:
            rand_candi = candidate_pd.sample(max_select)
            remove_candi = candidate_pd.drop(rand_candi.index)
        
        #5. save select info
        accurate_pd.to_csv(os.path.join(self.select_dir, EXPLORE_FILE_STRUCTURE.accurate))
        candi_info = ""
        if rand_candi is not None:
            rand_candi.to_csv(os.path.join(self.select_dir, EXPLORE_FILE_STRUCTURE.candidate))
            remove_candi.to_csv(os.path.join(self.select_dir, EXPLORE_FILE_STRUCTURE.candidate_delete))
            candi_info += "candidate configurations: {}, randomly select {}, delete {}\n\
                \t select details in file {}\n\t delete details in file {}.".format(
                    candidate_pd.shape[0], rand_candi.shape[0], remove_candi.shape[0],\
                    os.path.join(self.select_dir, EXPLORE_FILE_STRUCTURE.candidate),\
                    os.path.join(self.select_dir, EXPLORE_FILE_STRUCTURE.candidate_delete)  
                )
        else:
            candidate_pd.to_csv(os.path.join(self.select_dir, EXPLORE_FILE_STRUCTURE.candidate))
            candi_info += "candidate configurations: {}\n\t select details in file {}\n".format(
                    candidate_pd.shape[0],
                    os.path.join(self.select_dir, EXPLORE_FILE_STRUCTURE.candidate))
                
        error_pd.to_csv(os.path.join(self.select_dir, EXPLORE_FILE_STRUCTURE.failed))
        
        summary_info = ""
        summary_info += "total configurations: {}\n".format(devi_pd.shape[0])
        summary_info += "select by model deviation force:\n"
        summary_info += "accurate configurations: {}, details in file {}\n".\
            foramt(accurate_pd.shape[0], os.path.join(self.select_dir, EXPLORE_FILE_STRUCTURE.accurate))
            
        summary_info += candi_info
            
        summary_info += "error configurations: {}, details in file {}\n".\
            foramt(error_pd.shape[0], os.path.join(self.select_dir, EXPLORE_FILE_STRUCTURE.failed))
        
        write_to_file(os.path.join(self.select_dir, EXPLORE_FILE_STRUCTURE.select_summary), summary_info)
        print("committee method result:\n {}".format(summary_info))
    