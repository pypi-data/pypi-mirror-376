import numpy as np
import os
import time
import subprocess
from ase.io import read, write
import argparse, textwrap
import sys

import readline  # For command line input with tab completion
import glob # For file name tab completion


def print_logo():
    """
    Print aMACEing_toolkit logo
    """
    print(
    r"""
    ┌──────────────────────────────────────────────────────────────────────────────────────────┐
    │              __  ______   _____________                 __              ____   _ __      │
    │       ____ _/  |/  /   | / ____/ ____(_)___  ____ _    / /_____  ____  / / /__(_) /_     │
    │      / __ `/ /|_/ / /| |/ /   / __/ / / __ \/ __ `/   / __/ __ \/ __ \/ / //_/ / __/     │
    │     / /_/ / /  / / ___ / /___/ /___/ / / / / /_/ /   / /_/ /_/ / /_/ / / ,< / / /_       │
    │     \__,_/_/  /_/_/  |_\____/_____/_/_/ /_/\__, /____\__/\____/\____/_/_/|_/_/\__/       │
    │                                           /____/_____/                                   │
    │     by Jonas Hänseroth, Theoretical Solid-State Physics, Ilmenau University of Technology│
    └──────────────────────────────────────────────────────────────────────────────────────────┘ 
    """
    )
    # created with https://www.asciiart.eu/text-to-ascii-art (Slant Font)

def cite_amaceing_toolkit():
    """
    Print the citation for aMACEing_toolkit
    """
    print(
    r"""
    ┌
    │ If you use aMACEing_toolkit in your research, please cite the following publication:
    │
    │ PREPRINT AVAILABLE SOON!
    └
    """
    # print(
    # r"""
    # ┌
    # │ If you use aMACEing_toolkit in your research, please cite the following publication:
    # │
    # │ Jonas Hänseroth, Christian Dreßler.  A Python package for a fast and easy workflow of molecular dynamics simulations with MACE and CP2K,
    # │ Journal, 111 (111), 1111, https://google.com, 2025. 
    # │
    # │ BibTeX:
    # │ @article{haenseroth2025_amaceing_toolkit,
    # │   doi = {111/1111},
    # │   url = {https://google.com},
    # │   year = {2025},
    # │   publisher = {Publisher},
    # │   volume = {111},
    # │   number = {111},
    # │   pages = {111},
    # │   author = {Hänseroth, Jonas and Dreßler, Christian},
    # │   title = {aMACEing_toolkit: A Python package for a fast and easy workflow of molecular dynamics simulations with MACE and CP2K},
    # │   journal = {Journal}
    # │ }
    # └
    # """
    )

try:
    # Enable tab completion for file names, append '/' for directories
    def complete(text, state):
        matches = glob.glob(text + '*')
        # Append '/' if match is a directory
        matches = [
            m + '/' if os.path.isdir(m) else m
            for m in matches
        ]
        matches.append(None)
        return matches[state]

    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete)
except ImportError:
    # If readline is not available, fallback to simple input
    pass

def atk_utils():
    """
    Main function for the aMACEing_toolkit utilities
    """
    print_logo()

    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description='Build CP2K input files: (1) Via a short Q&A: NO arguments needed! (2) Directly from the command line with a dictionary: TWO arguments needed!', formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('-rt', '--run_type', type=str, help="[OPTIONAL] Which type of function do you want to run? ('EVAL_ERROR', 'PREPARE_EVAL_ERROR', 'EXTRACT_XYZ', 'CITATIONS')")
        parser.add_argument('-c', '--config', type=str, help=textwrap.dedent("""[OPTIONAL] Dictionary with the configuration:\n 
        \033[1m EVAL_ERROR \033[0m: "{'ener_filename_ground_truth': 'PATH', 'force_filename_ground_truth': 'PATH', 'ener_filename_compare': 'PATH', 'force_filename_compare': 'PATH'}"\n
        \033[1m PREPARE_EVAL_ERROR \033[0m: "{'traj_file': 'traj.traj', 'each_nth_frame': 200, 'start_cp2k': 'y/n', 'log_file': 'mace_input.log/None', 'xc_funtional': 'BLYP(_SR)/PBE(_SR)'}"\n
        \033[1m EXTRACT_XYZ \033[0m: "{'coord_file': 'traj.xyz', 'each_nth_frame': 10}"\n
        \033[1m CITATIONS \033[0m: "{'log_file': 'xxx_input.log'}" 
        \033[1m BENCHMARK \033[0m: "{'mode': 'MD/RECALC', 'coord_file': 'PATH', 'pbc_list': '[FLOAT FLOAT FLOAT FLOAT FLOAT FLOAT FLOAT FLOAT]', 'force_nsteps': 'INT/PATH', 'mace_model': '['mace_mp/...' 'small/...']', 'mattersim_model': 'small/large', 'sevennet_model': '['7net-mf-ompa/...' 'mpa/oma24/None']', 'orb_model': '['orb_v2/orb_v3_conservative_inf', 'mpa/omat/None']', 'grace_model': 'GRACE-1L-OMAT/GRACE-1L-OAM'}" """))
        parser.add_argument('-l','--logger', type=str, help='[OPTIONAL] Shows the logger output of the model_logger or the run_logger: "model" or "run"/"runexport".')
        args = parser.parse_args()
        if args.logger in ['model', 'run', 'runexport']:
            if args.logger == 'model':
                from amaceing_toolkit.runs.model_logger import show_models
                show_models(all_model=True)
                exit()
            elif args.logger == 'run':
                from amaceing_toolkit.runs.run_logger import show_runs
                show_runs()
                exit()
            elif args.logger == 'runexport':
                from amaceing_toolkit.runs.run_logger import export_run_logs
                export_run_logs()
                exit()
        if args.config != ' ':
            try:
                if args.run_type == 'BENCHMARK':
                    input_config = string_to_dict_multi(args.config)
                    print(input_config)
                else:
                    input_config = string_to_dict(args.config)
            except:
                print("The dictionary is not in the right format. Please check the help page.")

        
        with open('utils.log', 'w') as logfile:
            logfile.write("Function run with the following configuration:\n")
            logfile.write(f"{args.config}")

        if args.run_type == 'EVAL_ERROR':
            run_eval_error([input_config['ener_filename_ground_truth'], input_config['force_filename_ground_truth'], input_config['ener_filename_compare'], input_config['force_filename_compare']])

        elif args.run_type == 'PREPARE_EVAL_ERROR':
            if 'log_file' in input_config:
                run_prepare_eval_error(input_config['traj_file'], input_config['each_nth_frame'], input_config['start_cp2k'], input_config['log_file'], input_config['xc_functional'])
            else:
                run_prepare_eval_error(input_config['traj_file'], input_config['each_nth_frame'], input_config['start_cp2k'])
        
        elif args.run_type == 'EXTRACT_XYZ':
            extracted_filename = extract_frames(input_config['coord_file'], input_config['each_nth_frame'])

            print(f"Extracted every {input_config['each_nth_frame']} frame from the file {input_config['coord_file']}.")
            print(f"Extracted frames are saved in the file {extracted_filename}.")

        elif args.run_type == 'CITATIONS':
            print(input_config['log_file'])
            citation_grabber(input_config['log_file'])

        elif args.run_type == 'BENCHMARK':
            print(input_config["pbc_list"])
            try:
                pbc_list = f'[{input_config["pbc_list"][0,0]} {input_config["pbc_list"][0,1]} {input_config["pbc_list"][0,1]} {input_config["pbc_list"][1,0]} {input_config["pbc_list"][1,1]} {input_config["pbc_list"][1,2]} {input_config["pbc_list"][2,0]} {input_config["pbc_list"][2,1]} {input_config["pbc_list"][2,2]}]'
            except TypeError:
                pbc_list = f'[{input_config["pbc_list"][0]} 0.0 0.0 0.0 {input_config["pbc_list"][1]} 0.0 0.0 0.0 {input_config["pbc_list"][2]}]'
            if input_config['mode'] == 'MD':
                setup_bechmark_dir(input_config['coord_file'], pbc_list, input_config['force_nsteps'], input_config['mace_model'], input_config['mattersim_model'], input_config['sevennet_model'])
            elif input_config['mode'] == 'RECALC':
                recalc_bechmark_dir(input_config['coord_file'], pbc_list, input_config['force_nsteps'], input_config['mace_model'], input_config['mattersim_model'], input_config['sevennet_model'])
            print("Benchmark directories created.")

    else:
        util_type_dict = {'1': 'EVAL_ERROR', '2': 'PREPARE_EVAL_ERROR', '3': 'EXTRACT_XYZ', '4': 'CITATIONS', '5': 'BENCHMARK'}
        util_type = ' '
        while util_type not in ['1', '2', '3', '4', '5']:
            util_type = input("Which type of calculation do you want to run? (1=EVAL_ERROR, 2=PREPARE_EVAL_ERROR, 3=EXTRACT_XYZ, 4=CITATIONS, 5=BENCHMARK): ")
            if util_type not in ['1', '2', '3', '4', '5']:
                print("Invalid input! Please enter '1', '2', '3', '4' or '5'.")
        util_type = util_type_dict[util_type]

        if util_type == 'EVAL_ERROR':
            # Check if the eval_dft_data/force.xyz and eval_dft_data/eval_run-pos-1.xyz files exist
            if os.path.isfile('eval_dft_data/force.xyz') and os.path.isfile('eval_dft_data/eval_run-pos-1.xyz') and os.path.isfile('mace_coord.xyz') and os.path.isfile('mace_force.xyz'):
                ener_filename_ground_truth = 'eval_dft_data/eval_run-pos-1.xyz'
                force_filename_ground_truth = 'eval_dft_data/force.xyz'
                ener_filename_compare = 'mace_coord.xyz'
                force_filename_compare = 'mace_force.xyz'
            else:
                print("You have chosen to evaluate the error of a dataset.")
                print("Please provide the following information:")

                # Read the ground thruth and comparison files
                ener_filename_ground_truth = input("What is the name of the ground truth energy file? ")
                assert os.path.isfile(ener_filename_ground_truth), "Ground truth energy file does not exist!"

                force_filename_ground_truth = input("What is the name of the ground truth force file? ")
                assert os.path.isfile(force_filename_ground_truth), "Ground truth force file does not exist!"

                ener_filename_compare = input("What is the name of the comparison energy file (energy file or trajectory)? ")
                assert os.path.isfile(ener_filename_compare), "Comparison energy file does not exist!"
                
                force_filename_compare = input("What is the name of the comparison force file? ")
                assert os.path.isfile(force_filename_compare), "Comparison force file does not exist!"

            filenames = [ener_filename_ground_truth, force_filename_ground_truth, ener_filename_compare, force_filename_compare]

            # Run the error evaluation
            run_eval_error(filenames)
            input_config = {'ener_filename_ground_truth': ener_filename_ground_truth, 'force_filename_ground_truth': force_filename_ground_truth, 'ener_filename_compare': ener_filename_compare, 'force_filename_compare': force_filename_compare}

        elif util_type == 'PREPARE_EVAL_ERROR':
            print("You have chosen to prepare the error evaluation of a MLMD-Run.")

            # Read the ASE trajectory file
            traj_file = input("What is the name of the ASE trajectory (.traj) or xyz file? ")
            assert os.path.isfile(traj_file), "Trajectory file does not exist!"

            # Which frames to extract
            each_nth_frame = ask_for_int("Which n-th frame do you want to extract from the file?", 1000)

            # Ask for the CP2K input file
            start_cp2k = ask_for_yes_no("Do you want to run the CP2K calculation for the error evaluation now?", 'y')
            if start_cp2k == 'y':
                from amaceing_toolkit.default_configs import available_functionals
                #log_file = input("What is the name of the log file of the ASE calculation? ['mace_input.log'] ")
                #if log_file == '':
                #    log_file = 'mace_input.log'
                #assert os.path.isfile(log_file), "Log file of the ASE calculation does not exist!"
                log_file = ''
                xc_functional = input(f"Which XC functional do you want to use for the CP2K calculation? {available_functionals()}: ")

                # Run the preparation
                run_prepare_eval_error(traj_file, each_nth_frame, start_cp2k, log_file, xc_functional)
                input_config = {'traj_file': traj_file, 'each_nth_frame': each_nth_frame, 'start_cp2k': start_cp2k, 'log_file': log_file, 'xc_functional': xc_functional}

            else:
                # Run the preparation
                run_prepare_eval_error(traj_file, each_nth_frame, start_cp2k)
                input_config = {'traj_file': traj_file, 'each_nth_frame': each_nth_frame, 'start_cp2k': start_cp2k}


        elif util_type == 'EXTRACT_XYZ':
            print("You have chosen to extract a fraction of the frames from an xyz file.")
            print("Please provide the following information:")
            
            coord_file = input("What is the name of the coordinate file? ")
            assert os.path.isfile(coord_file), "Coordinate file does not exist!"

            each_nth_frame = ask_for_int("Which n-th frame do you want to extract from the file?", 10)

            extracted_filename = extract_frames(coord_file, each_nth_frame)

            print(f"Extracted every {each_nth_frame} frame from the file {coord_file}.")
            print(f"Extracted frames are saved in the file {extracted_filename}.")
            input_config = {'coord_file': coord_file, 'each_nth_frame': each_nth_frame}


        # ADD CITATIONS for all frameworks
        elif util_type == 'CITATIONS':
            print("You have chosen to print the citations for the production run.")

            log_file = input("What is the name of the log file of the production run configured with the aMACEing_toolkit? ['mace_input.log'] ")
            if log_file == '':
                log_file = 'mace_input.log'     

            frameworks = ['MACE', 'MatterSim', 'SevenNet', 'Orb', 'CP2K', 'Grace']

            for framework in frameworks:
                if framework.lower() in log_file.split('/')[-1].split('.')[0].lower():
                    print(f"Found {framework} in the log file name. Printing citations for {framework}.")
                    break
                else:
                    continue
            
            citation_grabber(log_file, framework)
            
            input_config = {'log_file': log_file}

        elif util_type == 'BENCHMARK':
            print("You have chosen to create benchmark directories for MACE, MatterSim and SevenNet.")

            coord_file = input("What is the name of the coordinate file (or reference trajecory/training file)? [coord.xyz]: ")
            if coord_file == '':
                coord_file = 'coord.xyz'
            assert os.path.isfile(coord_file), "Coordinate file does not exist!"

            box_cubic = ask_for_yes_no_pbc("Is the box cubic? (y/n/pbc)", 'pbc')

            if box_cubic == 'y':
                box_xyz = ask_for_float_int("What is the length of the box in Å?", str(10.0))
                pbc_list = [box_xyz, box_xyz, box_xyz]
            elif box_cubic == 'n':
                box_x = ask_for_float_int("What is the length of the box in the x-direction in Å?", str(10.0))
                box_y = ask_for_float_int("What is the length of the box in the y-direction in Å?", str(10.0))
                box_z = ask_for_float_int("What is the length of the box in the z-direction in Å?", str(10.0))
                pbc_list = [box_x, box_y, box_z]
            else:
                pbc_mat = np.loadtxt(box_cubic)
                assert os.path.isfile(pbc_mat), "PBC file does not exist!"
                pbc_list = [pbc_mat[0,0], pbc_mat[1,1], pbc_mat[2,2]]
            pbc_list = f'[{pbc_list[0]} {pbc_list[1]} {pbc_list[2]}]'

            mode = ask_for_yes_no("Do you want to run a MD simulation (y) or a recalculation of the AIMD trajectory (n)?", 'y')
            if mode == 'y':
                mode = 'MD'
                nsteps = ask_for_int("How many steps do you want to run?", 200000)
            else:
                mode = 'RECALC'
                force_file = input("What is the name of the corresponding force file ? [force.xyz]: ")
                if force_file == '':
                    force_file = 'force.xyz'
                assert os.path.isfile(force_file), "Force file does not exist!"


            # MACE model
            mace_model = ['mace_mp', 'small']
            foundation_model = ' '
            while foundation_model not in ['mace_off', 'mace_anicc', 'mace_mp', '']:
                foundation_model = input(f"Which MACE foundational model do you want to use? ('mace_off', 'mace_anicc', 'mace_mp') [{mace_model[0]}]: ")
                if foundation_model not in ['mace_off', 'mace_anicc', 'mace_mp', '']:
                    print("Invalid input! Please enter 'mace_off', 'mace_anicc' or 'mace_mp'.")
            if foundation_model == '':
                foundation_model = mace_model[0]
            if foundation_model in ['mace_off', 'mace_mp']:
                model_size = ' '
                while model_size not in ['small', 'medium', 'large', '']:
                    model_size = input(f"Choose the model size: ('small', 'medium', 'large') [{mace_model[1]}]: ")
                    if model_size not in ['small', 'medium', 'large', '']:
                        print("Invalid input! Please enter 'small', 'medium', or 'large'.")
                if model_size == '':
                    model_size = mace_model[1]
            mace_model[0] = foundation_model
            mace_model[1] = model_size

            # MatterSim model
            mattersim_model = 'large'
            foundation_model = ' '
            while foundation_model not in ['small', 'large', 'custom', '']:
                foundation_model = input(f"Which MatterSim foundational model do you want to use? ('small', 'large') [{mattersim_model}]: ")
                if foundation_model not in ['small', 'large', '']:
                    print("Invalid input! Please enter 'small' or 'large'.")
            if foundation_model == '':
                foundation_model = mattersim_model
            mattersim_model = foundation_model

            # SevenNet model
            sevennet_model = ['7net-mf-ompa', 'mpa']
            foundation_model_dict = {1: '7net-mf-ompa', 2: '7net-omat', 3: '7net-l3i5', 4: '7net-0'}
            foundation_model = ' '
            while foundation_model not in ['1', '2', '3', '4', '']:
                foundation_model = input(f"Which SevenNet foundational model do you want to use? (1=7net-mf-ompa, 2=7net-omat, 3=7net-l3i5, 4=7net-0): [{sevennet_model[0]}]: ")
                if foundation_model not in ['1', '2', '3', '4', '']:
                    print("Invalid input! Please enter '1', '2', '3', or '4'.")
            if foundation_model == '':
                foundation_model = sevennet_model[0]
            else:
                foundation_model = foundation_model_dict[int(foundation_model)]
            if foundation_model == '7net-mf-ompa':
                print("You chose the 7net-mf-ompa model. This model supports multi-fidelity learning to train simultaneously on the MPtrj, Alex, and OMat24 datasets.")
                modal = ask_for_yes_no("Do you want to produce PBE52 (MP) results (y) or PBE54 (OMAT24) results (n)?" , 'y')
                if modal == 'y':
                    modal = 'mpa'
                else:
                    modal = 'oma24'
            else: 
                modal = ''
            sevennet_model[0] = foundation_model
            sevennet_model[1] = modal

            # Orb model
            orb_model = ['orb_v3_conservative_inf', 'omat']
            foundation_model_dict = {1: 'orb_v3_conservative_inf', 2: 'orb_v2'}
            foundation_model = ' '
            while foundation_model not in ['1', '2', '']:
                foundation_model = input(f"Which Orb foundational model do you want to use? (1=orb_v3_conservative_inf, 2=orb_v2): [{orb_model[0]}]: ")
                if foundation_model not in ['1', '2', '']:
                    print("Invalid input! Please enter '1' or '2'.")
            if foundation_model == '':
                foundation_model = orb_model[0]
            else:
                foundation_model = foundation_model_dict[int(foundation_model)]
            if foundation_model == 'orb_v3_conservative_inf':
                print("You chose the orb_v3_conservative_inf model. This model was trained on the MPtrj, Alex, and OMat24 datasets.")
                modal = ask_for_yes_no("Do you want to produce MPA results (y) or OMAT24 results (n)?" , 'y')
                if modal == 'y':
                    modal = 'mpa'
                else:
                    modal = 'omat'
            else:
                modal = ''
            orb_model[0] = foundation_model
            orb_model[1] = modal

            # Grace model
            grace_model = 'GRACE-1L-OMAT'
            foundation_model_dict = {1: 'GRACE-1L-OMAT', 2: 'GRACE-2L-OMAT', 3: 'GRACE-1L-OAM', 4: 'GRACE-2L-OAM'}
            foundation_model = ' '
            while foundation_model not in ['1', '2', '3', '4', '']:
                foundation_model = input(f"Which Grace foundational model do you want to use? (1=GRACE-1L-OMAT, 2=GRACE-2L-OMAT, 3=GRACE-1L-OAM, 4=GRACE-2L-OAM): [{grace_model}]: ")
                if foundation_model not in ['1', '2', '3', '4', '']:
                    print("Invalid input! Please enter '1', '2', '3', or '4'.")
            if foundation_model == '':
                foundation_model = grace_model
            else:
                foundation_model = foundation_model_dict[int(foundation_model)]


            # Create the directories
            if mode == 'MD':
                setup_bechmark_dir(coord_file, pbc_list, nsteps, mace_model, mattersim_model, sevennet_model, orb_model, grace_model)
                input_config = {'mode': mode, 'coord_file': coord_file, 'pbc_list': pbc_list, 'force_nsteps': nsteps, 'mace_model': f"""'['{mace_model[0]}' '{mace_model[1]}']'""", 'mattersim_model': mattersim_model, 'sevennet_model': f"""'['{sevennet_model[0]}' '{sevennet_model[1]}']'""", 'orb_model': f"""'['{orb_model[0]}' '{orb_model[1]}']'""", 'grace_model': grace_model}
            else:
                recalc_bechmark_dir(coord_file, pbc_list, force_file, mace_model, mattersim_model, sevennet_model, orb_model, grace_model)
                input_config = {'mode': mode, 'coord_file': coord_file, 'pbc_list': pbc_list, 'force_nsteps': force_file, 'mace_model': f"""'['{mace_model[0]}' '{mace_model[1]}']'""", 'mattersim_model': mattersim_model, 'sevennet_model': f"""'['{sevennet_model[0]}' '{sevennet_model[1]}']'""", 'orb_model': f"""'['{orb_model[0]}' '{orb_model[1]}']'""", 'grace_model': grace_model}

            input_config = str(input_config).replace('"', '')



    # Write the configuration to a log file
    write_log(input_config)

    cite_amaceing_toolkit()
    return 0


def run_eval_error(filenames):
    """
    Function to evaluate the error of a dataset
    """
    # IMPORTS
    if filenames[0].split('.')[-1] == 'xyz':
        ener_ground_truth = xyz_reader(filenames[0])[2]
    else:
        ener_ground_truth = np.loadtxt(filenames[0])
    force_ground_truth = xyz_reader(filenames[1])[1]
    if filenames[2].split('.')[-1] == 'xyz':
        ener_compare = xyz_reader(filenames[2])[2]
    else:
        ener_compare = np.loadtxt(filenames[2])
    if filenames[3].split('.')[-1] == 'xyz':
        force_compare = xyz_reader(filenames[3])[1]
    elif filenames[3].split('.')[-1] == 'lammpstrj':
        force_compare = lmp_reader(filenames[3])[1]

    # Rescale the ground truth (AIMD) forces and energies
    force_ground_truth *= 51.4221
    ener_ground_truth *= 27.2114

    # Compare them
    diff_force = force_compare - force_ground_truth
    diff_ener = ener_compare - ener_ground_truth

    diff_force = np.linalg.norm(diff_force, axis=2)
    ref_force = np.linalg.norm(force_ground_truth, axis=2)
    rel_diff_force = diff_force / ref_force
    diff_force = np.mean(diff_force, axis=1)
    rel_diff_force = np.mean(rel_diff_force, axis=1)
    print(f"The mean absolute force error is {np.mean(diff_force):.8f} eV/Angstrom.")
    print(f"The mean relative force error is {np.mean(rel_diff_force):.8f}.")

    diff_energy = np.abs(ener_compare - ener_ground_truth)/force_compare.shape[1]
    print(f"The mean absolute energy error per atom is {np.mean(diff_energy):.8f} eV/atom.")

    # Write the error files
    with open('errors.txt', 'w') as f:
        f.write("Mean absolute force error: " + str(np.mean(diff_force)) + " eV/Angstrom\n")
        f.write("Mean relative force error: " + str(np.mean(rel_diff_force)) + "\n")
        f.write("Mean absolute energy error per atom: " + str(np.mean(diff_energy)) + " eV/atom\n")


def run_prepare_eval_error(traj_file, each_nth_frame, start_cp2k, log_file="", xc_functional=""):
    # Read the frames

    if traj_file.split('.')[-1] == 'xyz':
        atom, coord = xyz_reader(traj_file)[:2]
        force_file = input("What is the name of the force LAMMPS (.lammpstrj) or xyz file? ")
        assert os.path.isfile(force_file), "Trajectory file does not exist!"
        if force_file.split('.')[-1] == 'xyz':
            force = xyz_reader(force_file)[1]
        elif force_file.split('.')[-1] == 'lammpstrj':
            force = lmp_reader(force_file)
        if "E" in traj_file:
            ener = xyz_reader(traj_file)[2]
        else:
            ener_file = input("What is the name of the energy file? ")
            assert os.path.isfile(ener_file), "Energy file does not exist!"
            ener = np.loadtxt(ener_file)

        # Extract the nth frames and save them
        coord = coord[::each_nth_frame]
        force = force[::each_nth_frame]
        ener = ener[::each_nth_frame]
        xyz_writer("mace_coord.xyz", atom, coord, ener)
        xyz_writer("mace_force.xyz", atom, force)
    else:
        atoms = read(traj_file, index = f":: {each_nth_frame}")

        coord = []
        force = []
        ener = []

        for i in range(len(atoms)):
            coord.append(atoms[i].get_positions())
            force.append(atoms[i].get_forces())
            ener.append(atoms[i].get_potential_energy())
        
        atom = np.array(atoms[0].get_chemical_symbols())
        coord = np.array(coord)
        force = np.array(force)
        ener = np.array(ener)

        # Extract the pbc from the first frame
        pbc= atoms[0].get_cell()
        pbc_list = [pbc[0,0], pbc[1,1], pbc[2,2]]

        # Write the files
        xyz_writer("mace_coord.xyz", atom, coord, ener)
        xyz_writer("mace_force.xyz", atom, force)
        np.savetxt("pbc", pbc)

    # Print the information
    print(f"Extracted every {each_nth_frame} frame from the file {traj_file}.")
    print(f"Extracted frames are saved in the files mace_coord.xyz and mace_force.xyz.")

    # Initialize the CP2K run
    if start_cp2k == 'y':
        # Read the log file
        #with open(log_file) as f:
        #    lines = f.readlines()
        #input_mace = string_to_dict(lines[-1])

        run_type = "REFTRAJ"
        config_dict = {'project_name': 'eval_run', 'ref_traj': '../mace_coord.xyz', 'pbc_list': f'[{pbc_list[0]} {pbc_list[1]} {pbc_list[2]}]', 'nsteps': f'{coord.shape[0]}', 'stride': '1', 'print_velocities': 'OFF', 'print_forces': 'ON', 'xc_functional': xc_functional, 'cp2k_newer_than_2023x': 'y'}

       # Call amaceing_cp2k 
        command = f"""amaceing_cp2k --run_type="{run_type}" --config="{config_dict}" """ 

        if not os.path.exists('eval_data'):
            os.mkdir('eval_data')
        os.chdir('eval_data')
        print("Running the following command: ", command, " in folder ", os.getcwd())

        # Run the command for input file generation
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        process.wait()

        # Starting CP2K on the HPC
        from amaceing_toolkit.default_configs import cp2k_runscript

        start_command = cp2k_runscript('.', 'reftraj_cp2k.inp')[1]
        print(start_command)

        print("Please run the following command after the CP2K calculation finished:")
        print("amaceing_utils and choose EVAL_ERROR")

        os.chdir('..')
    
    else:
        # Print the relevant commands
        print("Please run the following commands to evaluate the error:")
        print("1. Create the CP2K input file to obtain the ground truth energy and forces:")
        print("""amaceing_cp2k --run_type="REFTRAJ" --config="{'project_name' : 'NAME', 'ref_traj' : 'FILE', 'pbc_list' = '[FLOAT FLOAT FLOAT]', 'nsteps': 'INT', 'stride': '1', 'print_velocities': 'OFF', 'print_forces': 'ON', 'xc_functional': PBE(_SR)/BLYP(_SR), 'cp2k_newer_than_2023x': 'y'}" """)
        print("2. Run the CP2K calculation on your HPC.")
        print("3. Run the following command to evaluate the error:")
        print("amaceing_utils and choose EVAL_ERROR")

def string_to_dict(string):
    """
    Convert a string which looks like a python dictionary to an actual python dictionary for the aMACEing_toolkit direct input.
    All keys and values are expected to be strings. Floats and integers etc. have to be inserted as strings.
    """

    string = string[1:-2]
    dict_export = {}
    for pair in string.split(','):
        pair_key = pair.split(':')[0]
        pair_key = pair_key.strip()
        pair_key = pair_key.strip("'")
        pair_value = pair.split(':')[1]
        if pair_key == 'pbc_list':
            pair_value = pair_value.strip(" ")
            pair_value = pair_value.strip("'")
            list = pair_value.strip('[ ]')
            list = list.split(' ')
            list = [float(i) for i in list]
            pair_value = list
        else:
            pair_value = pair_value.strip()
            pair_value = pair_value.strip("'")
        dict_export[pair_key] = pair_value
    return dict_export

def string_to_dict_multi(string):
    """
    Convert a string which looks like a python dictionary to an actual python dictionary for the aMACEing_toolkit direct input.
    All keys and values are expected to be strings. Floats and integers etc. have to be inserted as strings.
    Special case for multi_md, because "lists" are in the dictionary.
    """

    string = string[1:-2]
    dict_export = {}
    for pair in string.split(','):
        pair_key = pair.split(':')[0]
        pair_key = pair_key.strip()
        pair_key = pair_key.strip("'")
        pair_value = pair.split(':')[1]
        if pair_key == 'pbc_list':
            pair_value = pair_value.strip(" ")
            pair_value = pair_value.strip("'")
            list = pair_value.strip('[ ]')
            list = list.split(' ')
            list = [float(i) for i in list]
            pair_value = list
        elif pair_key in ['foundation_model', 'model_size', 'modal', 'dispersion_via_simenv', 'mace_model',  'sevennet_model']:
            pair_value = pair_value.strip(" ")
            pair_value = pair_value.strip("'")
            list = pair_value.strip('[ ]')
            list = list.split(' ')
            list = [str(i) for i in list]
            # Strip the entries in the list from the "'"
            list = [i.strip("'") for i in list]
            pair_value = list
        else:
            pair_value = pair_value.strip()
            pair_value = pair_value.strip("'")
        dict_export[pair_key] = pair_value
    return dict_export


def string_to_dict_multi2(string):
    """
    Convert a string which looks like a python dictionary to an actual python dictionary for the aMACEing_toolkit direct input.
    All keys and values are expected to be strings. Floats and integers etc. have to be inserted as strings.
    Special case for finetune_multihead, because a "list" is in the dictionary.
    """

    string = string[1:-2]
    dict_export = {}
    for pair in string.split(','):
        pair_key = pair.split(':')[0]
        pair_key = pair_key.strip()
        pair_key = pair_key.strip("'")
        pair_value = pair.split(':')[1]
        if pair_key == 'train_file' or pair_key == 'xc_functional_of_dataset':
            pair_value = pair_value.strip(" ")
            pair_value = pair_value.strip("'")
            list = pair_value.strip('[ ]')
            list = list.split(' ')
            list = [str(i) for i in list]
            # Strip the entries in the list from the "'"
            list = [i.strip("'") for i in list]
            pair_value = list
        else:
            pair_value = pair_value.strip()
            pair_value = pair_value.strip("'")
        dict_export[pair_key] = pair_value
    return dict_export

def atom_symbol_to_atomic_number(atom_symbol):
    atom_to_atomic_number = {'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82}
    return atom_to_atomic_number[atom_symbol]


def create_dataset(coord_file, force_file, pbc_list):
    """
    Function to create the training dataset out of the force and position files
    """
   
    # Read the coordinate file
    atoms = xyz_reader(coord_file)[0]
    positions  = xyz_reader(coord_file)[1]
    energies = xyz_reader(coord_file)[2]
    forces = xyz_reader(force_file)[1]

    # Set the pbc string
    lattice = f"{pbc_list[0,0]} {pbc_list[0,1]} {pbc_list[0,2]} {pbc_list[1,0]} {pbc_list[1,1]} {pbc_list[1,2]} {pbc_list[2,0]} {pbc_list[2,1]} {pbc_list[2,2]}"

    # Rescale the forces (ASE uses eV/Angstrom)
    forces *= 51.4221

    # Rescale the energies (ASE uses eV)
    energies *= 27.2114

    # Write the dataset file
    filename = 'dataset.xyz'
    with open(filename, 'w') as f:
        for i in range(0, positions.shape[0]):
            f.write(f"{len(atoms)}\n")
            f.write(f"REF_TotEnergy={energies[i]:.8f} cutoff=-1.00000000 nneightol=1.20000000 pbc=\"T T T\" Lattice=\"{lattice}\" Properties=species:S:1:pos:R:3:REF_Force:R:3:Z:I:1\n")
            for j in range(0, positions.shape[1]):
                atomic_number = atom_symbol_to_atomic_number(atoms[j])
                f.write('%s %f %f %f %f %f %f %d \n' % (atoms[j], positions[i,j,0], positions[i,j,1], positions[i,j,2], forces[i,j,0], forces[i,j,1], forces[i,j,2], atomic_number))
    return filename        

def e0_wrapper(e0s_precalc, coord_file, xc_functional):
    """
    Function to create the e0 dict
    """

    # Read the first frame of the coordinate file and get only the atoms
    atoms = xyz_reader(coord_file, only_atoms=True)[0]

    # Search for individual atoms in the atom array
    atom_list = []
    for atom in atoms:
        if atom not in atom_list:
            atom_list.append(atom)

    # Search which atoms are missing in the precalculated e0s dictionary
    missing_atoms = []
    for atom in atom_list:
        if atom_symbol_to_atomic_number(atom) not in e0s_precalc:
            missing_atoms.append(atom)
    
    print(f"{len(missing_atoms)}/{len(atom_list)} are missing in the precalculated E0 dictionary...")
    
    # Create the E0_dict including all individual atoms
    e0_dict = {}
    for atom in atom_list:
        if atom_symbol_to_atomic_number(atom) in e0s_precalc:
            e0_dict[atom_symbol_to_atomic_number(atom)] = e0s_precalc[atom_symbol_to_atomic_number(atom)]
        else:
            print(f"Calculating E0 for {atom}...")
            e0_dict[atom_symbol_to_atomic_number(atom)] = e0_on_the_fly(atom, xc_functional)
            print(f"Calculated E0 for {atom}: {e0_dict[atom_symbol_to_atomic_number(atom)]}")

    print("E0 dictionary created using the precalculated data: ", e0_dict)

    return e0_dict

def e0_on_the_fly(atom, xc_functional):
    """
    Function to calculate the E0 on the fly with aMACEing_toolkit itself
    """
    # Call the CP2K function to calculate the E0

    run_type = 'ENERGY'
    config_dict = {'project_name': f'atomic_energy_{atom}', 'coord_file': 'coord.xyz', 'pbc_list': '[20.0 20.0 20.0]', 'xc_functional': xc_functional, 'cp2k_newer_than_2023x': 'y'}

    # Create a temporary directory for the calculation of the atomic energy of this atom type
    temp_dir = f"calc_atomic_ener_{atom}"
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    os.chdir(temp_dir)

    # Write the coord file
    with open('coord.xyz', 'w') as f:
        f.write(f"1\n")
        f.write(f"Atomic energy calculation for {atom}\n")
        f.write(f"{atom} 10.0 10.0 10.0\n")

    # Call amaceing_cp2k 
    command = f"""amaceing_cp2k --run_type="{run_type}" --config="{config_dict}" """ 
    print("Running the following command:", command)

    # Run the command for input file generation
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    process.wait()

    # Run CP2K locally
    from amaceing_toolkit.default_configs.runscript_loader import RunscriptLoader
    runscript_content = RunscriptLoader('cp2k_local', '_no_project_name', 'energy_cp2k.inp').load_runscript()

    # runscript_content is a string with two lines: the first is the source command, the second is the cp2k command
    lines = runscript_content.strip().splitlines()
    source_command = lines[0]
    cp2k_command = lines[1]

    print("Running the following command:", source_command)
    print("Running the following commands:", f"""{cp2k_command}""")

    # Run the CP2K calculation on the local machine within one process
    process = subprocess.Popen(f"""{source_command} && {cp2k_command}""", shell=True, stdout=subprocess.PIPE)
    process.wait()


    # Read the energy from the output file
    import re
    while not os.path.exists('energy_cp2k.out'):
        time.sleep(1)
    with open('energy_cp2k.out') as f:
        lines = f.readlines()

        # Search for the energy 
        energy = 0

        for line in lines:
            if 'ENERGY|' in line:
                energy = float(re.findall(r"[-+]?\d*\.\d+|\d+", line)[0])
                break
        if energy == 0:
            print("Error: Energy not found in the output file. Please check the output file.")
            exit()

    os.chdir('..')
    return energy * 27.2114 # Convert from Hartree to eV

def equi_to_md(project_name, coord_file):
    """
    Function writes a python file which reads the equilibration trajectory and writes its last step for the MD run
    """
    file_content = f"""
from amaceing_toolkit.workflow.utils import xyz_reader, xyz_writer
import os

# Rename the coord file
if os.path.isfile('{coord_file}') and not os.path.isfile('{coord_file.split(".")[0]}_before_equi.xyz'):
    os.rename('{coord_file}', '{coord_file.split(".")[0]}_before_equi.xyz')

# Read the equilibration trajectory
atoms, coords, energies, forces, meta_data = xyz_reader('{project_name}_equi-pos-1.xyz')

# Write the last frame of the equilibration trajectory to the MD trajectory
xyz_writer('{coord_file}', atoms, coords[-1].reshape(1, coords.shape[1], coords.shape[2]))
"""

    with open('equi_to_md.py', 'w') as f:
        f.write(file_content)
    
    print("""Before starting the MD run you have to extract the last frame of the Equilibration by using "python equi_to_md.py" has been written.""")


def xyz_reader(file, only_atoms=False):
    """
    Read an xyz file and return the number of atoms and the positions or forces
    """
    with open(file) as f:
        lines = f.readlines()
        n_atoms = int(lines[0])
        n_frames = int(len(lines)/(n_atoms+2))
        atoms = np.zeros((n_atoms),dtype='<U2')
        energies = np.zeros((n_frames))
        xyz_data = np.zeros((n_frames, n_atoms, 3))
        meta_data = np.zeros((n_frames))
        meta_data = np.array(meta_data, dtype='object')

        # Check if the file contains forces
        force_check = lines[2].split(' ')
        force_check = list(filter(None, force_check))
        if len(force_check) > 5:
            forcesX = np.zeros((n_frames, n_atoms, 4))
        else:
            forcesX = np.zeros((1,1,1))

        energy_check = False
        if 'E = ' in lines[1] or 'TotEnergy=' in lines[1]:
            energy_check = True

        for i in range(0,n_frames):
            if i == 0:
                if energy_check:
                    try:
                        energies[i] = float(lines[i*(n_atoms+2)+1].split('E = ')[1])
                    except:
                        energies[i] = float(lines[i*(n_atoms+2)+1].split('TotEnergy=')[1].split(' ')[0])
                meta_data[i] = lines[i*(n_atoms+2)+1]
                for j in range(0,n_atoms):
                    line_splitted = lines[j+2].strip().split(' ')
                    line_splitted = np.array(line_splitted)
                    mask = line_splitted != ''
                    line_splitted = line_splitted[mask]

                    atoms[j] = line_splitted[0]

                    xyz_data[i, j, 0] = float(line_splitted[1])
                    xyz_data[i, j, 1] = float(line_splitted[2])
                    xyz_data[i, j, 2] = float(line_splitted[3])
                    if len(force_check) > 5:
                        forcesX[i, j, 0] = float(line_splitted[4])
                        forcesX[i, j, 1] = float(line_splitted[5])
                        forcesX[i, j, 2] = float(line_splitted[6])
                        forcesX[i, j, 3] = float(line_splitted[7])
            else:
                if only_atoms == False:
                    if energy_check:
                        try:
                            energies[i] = float(lines[i*(n_atoms+2)+1].split('E = ')[1])
                        except:
                            energies[i] = float(lines[i*(n_atoms+2)+1].split('TotEnergy=')[1].split(' ')[0])
                    meta_data[i] = str(lines[i*(n_atoms+2)+1])
                    for j in range(0,n_atoms):
                        line_splitted = lines[i*(n_atoms+2)+j+2].strip().split(' ')
                        line_splitted = np.array(line_splitted)
                        mask = line_splitted != ''
                        line_splitted = line_splitted[mask]

                        xyz_data[i, j, 0] = float(line_splitted[1])
                        xyz_data[i, j, 1] = float(line_splitted[2])
                        xyz_data[i, j, 2] = float(line_splitted[3])
                        if len(force_check) > 5:
                            forcesX[i, j, 0] = float(line_splitted[4])
                            forcesX[i, j, 1] = float(line_splitted[5])
                            forcesX[i, j, 2] = float(line_splitted[6])
                            forcesX[i, j, 3] = float(line_splitted[7])

    return atoms, xyz_data, energies, forcesX, meta_data

def xyz_writer(filename, atoms, coords, energies = "", forces = "", meta_data = ""):
    """
    Write an xyz file with atoms, coordinates and energies
    """
    print_ener = True
    print_meta = True
    print_force = True

    if np.all(meta_data == ""):
        print_meta = False

    if np.all(energies == ""):
        print_ener = False

    if np.all(forces == ""):
        print_force = False


    with open(filename, 'w') as f:
        for i in range(0, coords.shape[0]):
            f.write(f"{len(atoms)}\n")
            if print_meta:
                f.write(f"{meta_data[i]}")
            elif print_ener:
                f.write(f"E = {energies[i]:.8f}\n")
            else:
                f.write(f"\n")
            if print_force:
                for j in range(0, coords.shape[1]):
                    f.write('%s %f %f %f %f %f %f %d\n' % (atoms[j], coords[i,j,0], coords[i,j,1], coords[i,j,2], forces[i,j,0], forces[i,j,1], forces[i,j,2], forces[i,j,3]))
            else:
                for j in range(0, coords.shape[1]):
                    f.write('%s %f %f %f\n' % (atoms[j], coords[i,j,0], coords[i,j,1], coords[i,j,2]))
    
    print("Wrote the file ", filename)

def mace_citations(foundation_model = ""):
    """
    Function to print the citations for MACE
    """
    print("")
    print(r""" 1. Ilyes Batatia, David Peter Kovacs, Gregor N. C. Simm, Christoph Ortner, Gábor Csányi, MACE: Higher Order Equivariant Message Passing Neural Networks for Fast and Accurate Force Fields, Advances in Neural Information Processing Systems, 2022, https://openreview.net/forum?id=YPpSngE-ZU
@inproceedings{Batatia2022mace,
  title={{MACE}: Higher Order Equivariant Message Passing Neural Networks for Fast and Accurate Force Fields},
  author={Ilyes Batatia and David Peter Kovacs and Gregor N. C. Simm and Christoph Ortner and Gábor Csányi},
  booktitle={Advances in Neural Information Processing Systems},
  editor={Alice H. Oh and Alekh Agarwal and Danielle Belgrave and Kyunghyun Cho},
  year={2022},
  url={https://openreview.net/forum?id=YPpSngE-ZU}
}""")
    print("")
    print(r""" 2. Ilyes Batatia, Simon Batzner, David Peter Kovacs, Albert Musaelian, Gregor N. C. Simm, Ralf Drautz, Christoph Ortner, Boris Kozinsky, Gábor Csányi, The Design Space of E(3)-Equivariant Atom-Centered Interatomic Potentials, arXiv:2205.06643, 2022, https://arxiv.org/abs/2205.06643
@misc{Batatia2022Design,
  title = {The Design Space of E(3)-Equivariant Atom-Centered Interatomic Potentials},
  author = {Batatia, Ilyes and Batzner, Simon and Kov{\'a}cs, D{\'a}vid P{\'e}ter and Musaelian, Albert and Simm, Gregor N. C. and Drautz, Ralf and Ortner, Christoph and Kozinsky, Boris and Cs{\'a}nyi, G{\'a}bor},
  year = {2022},
  number = {arXiv:2205.06643},
  eprint = {2205.06643},
  eprinttype = {arxiv},
  doi = {10.48550/arXiv.2205.06643},
  archiveprefix = {arXiv}
 }""")
    if foundation_model == 'mace_mp':
        print("")
        print(r""" 3. Ilyes Batatia, Philipp Benner, Yuan Chiang, Alin M. Elena, Dávid P. Kovács, Janosh Riebesell, Xavier R. Advincula, Mark Asta, William J. Baldwin, Noam Bernstein, Arghya Bhowmik, Samuel M. Blau, Vlad Cărare, James P. Darby, Sandip De, Flaviano Della Pia, Volker L. Deringer, Rokas Elijošius, Zakariya El-Machachi, Edvin Fako, Andrea C. Ferrari, Annalena Genreith-Schriever, Janine George, Rhys E. A. Goodall, Clare P. Grey, Shuang Han, Will Handley, Hendrik H. Heenen, Kersti Hermansson, Christian Holm, Jad Jaafar, Stephan Hofmann, Konstantin S. Jakob, Hyunwook Jung, Venkat Kapil, Aaron D. Kaplan, Nima Karimitari, Namu Kroupa, Jolla Kullgren, Matthew C. Kuner, Domantas Kuryla, Guoda Liepuoniute, Johannes T. Margraf, Ioan-Bogdan Magdău, Angelos Michaelides, J. Harry Moore, Aakash A. Naik, Samuel P. Niblett, Sam Walton Norwood, Niamh O'Neill, Christoph Ortner, Kristin A. Persson, Karsten Reuter, Andrew S. Rosen, Lars L. Schaaf, Christoph Schran, Eric Sivonxay, Tamás K. Stenczel, Viktor Svahn, Christopher Sutton, Cas van der Oord, Eszter Varga-Umbrich, Tejs Vegge, Martin Vondrák, Yangshuai Wang, William C. Witt, Fabian Zills, Gábor Csányi, A foundation model for atomistic materials chemistry, arXiv:2401.00096, 2023, https://arxiv.org/abs/2401.00096
@article{batatia2023foundation,
  title={A foundation model for atomistic materials chemistry},
  author={Ilyes Batatia and Philipp Benner and Yuan Chiang and Alin M. Elena and Dávid P. Kovács and Janosh Riebesell and Xavier R. Advincula and Mark Asta and William J. Baldwin and Noam Bernstein and Arghya Bhowmik and Samuel M. Blau and Vlad Cărare and James P. Darby and Sandip De and Flaviano Della Pia and Volker L. Deringer and Rokas Elijošius and Zakariya El-Machachi and Edvin Fako and Andrea C. Ferrari and Annalena Genreith-Schriever and Janine George and Rhys E. A. Goodall and Clare P. Grey and Shuang Han and Will Handley and Hendrik H. Heenen and Kersti Hermansson and Christian Holm and Jad Jaafar and Stephan Hofmann and Konstantin S. Jakob and Hyunwook Jung and Venkat Kapil and Aaron D. Kaplan and Nima Karimitari and Namu Kroupa and Jolla Kullgren and Matthew C. Kuner and Domantas Kuryla and Guoda Liepuoniute and Johannes T. Margraf and Ioan-Bogdan Magdău and Angelos Michaelides and J. Harry Moore and Aakash A. Naik and Samuel P. Niblett and Sam Walton Norwood and Niamh O'Neill and Christoph Ortner and Kristin A. Persson and Karsten Reuter and Andrew S. Rosen and Lars L. Schaaf and Christoph Schran and Eric Sivonxay and Tamás K. Stenczel and Viktor Svahn and Christopher Sutton and Cas van der Oord and Eszter Varga-Umbrich and Tejs Vegge and Martin Vondrák and Yangshuai Wang and William C. Witt and Fabian Zills and Gábor Csányi},
  year={2023},
  eprint={2401.00096},
  archivePrefix={arXiv},
  primaryClass={physics.chem-ph}
}""")
        print("")
        print(r""" 4. Bowen Deng, Peichen Zhong, KyuJung Jun, Janosh Riebesell, Kevin Han, Christopher J. Bartel, Gerbrand Ceder, CHGNet: Pretrained universal neural network potential for charge-informed atomistic modeling, arXiv:2302.14231, 2023, https://arxiv.org/abs/2302.14231
@article{deng2023chgnet,
  title={CHGNet: Pretrained universal neural network potential for charge-informed atomistic modeling},
  author={Bowen Deng and Peichen Zhong and KyuJung Jun and Janosh Riebesell and Kevin Han and Christopher J. Bartel and Gerbrand Ceder},
  year={2023},
  eprint={2302.14231},
  archivePrefix={arXiv},
  primaryClass={cond-mat.mtrl-sci}
}
""")
        print("")
    elif foundation_model == 'mace_off':
        print("")
        print(r""" 3. Dávid Péter Kovács, J. Harry Moore, Nicholas J. Browning, Ilyes Batatia, Joshua T. Horton, Venkat Kapil, William C. Witt, Ioan-Bogdan Magdău, Daniel J. Cole, Gábor Csányi, MACE-OFF23: Transferable Machine Learning Force Fields for Organic Molecules, arXiv:2312.15211, 2023, https://arxiv.org/abs/2312.15211
@misc{kovacs2023maceoff23,
  title={MACE-OFF23: Transferable Machine Learning Force Fields for Organic Molecules}, 
  author={Dávid Péter Kovács and J. Harry Moore and Nicholas J. Browning and Ilyes Batatia and Joshua T. Horton and Venkat Kapil and William C. Witt and Ioan-Bogdan Magdău and Daniel J. Cole and Gábor Csányi},
  year={2023},
  eprint={2312.15211},
  archivePrefix={arXiv},
}        
""")
        print("")
        
def mattersim_citations():
    """
    Function to print the citations for Mattersim
    """
    print("")
    print(r""" Han Yang, Chenxi Hu, Yichi Zhou, Xixian Liu, Yu Shi, Jielan Li, Guanzhi Li, Zekun Chen, Shuizhou Chen, Claudio Zeni, Matthew Horton, Robert Pinsler, Andrew Fowler, Daniel Zügner, Tian Xie, Jake Smith, Lixin Sun, Qian Wang, Lingyu Kong, Chang Liu, Hongxia Hao, Ziheng Lu, MatterSim: A Deep Learning Atomistic Model Across Elements, Temperatures and Pressures, arXiv:2405.04967, 2024, https://arxiv.org/abs/2405.04967
@article{yang2024mattersim,
title={MatterSim: A Deep Learning Atomistic Model Across Elements, Temperatures and Pressures},
author={Han Yang and Chenxi Hu and Yichi Zhou and Xixian Liu and Yu Shi and Jielan Li and Guanzhi Li and Zekun Chen and Shuizhou Chen and Claudio Zeni and Matthew Horton and Robert Pinsler and Andrew Fowler and Daniel Zügner and Tian Xie and Jake Smith and Lixin Sun and Qian Wang and Lingyu Kong and Chang Liu and Hongxia Hao and Ziheng Lu},
year={2024},
eprint={2405.04967},
archivePrefix={arXiv},
primaryClass={cond-mat.mtrl-sci},
url={https://arxiv.org/abs/2405.04967},
journal={arXiv preprint arXiv:2405.04967}
}
""")
    print("")
    
def sevennet_citations(foundation_model = ""):
    """
    Function to print the citations for SevenNet
    """
    print("")
    print(r""" 1. Yutack Park, Jaesun Kim, Seungwoo Hwang, Seungwu Han, Scalable Parallel Algorithm for Graph Neural Network Interatomic Potentials in Molecular Dynamics Simulations, J. Chem. Theory Comput., 2024, 20 (11), pp 4857–4868, https://doi.org/10.1021/acs.jctc.4c00190
@article{park_scalable_2024,
	title = {Scalable Parallel Algorithm for Graph Neural Network Interatomic Potentials in Molecular Dynamics Simulations},
	volume = {20},
	doi = {10.1021/acs.jctc.4c00190},
	number = {11},
	journal = {J. Chem. Theory Comput.},
	author = {Park, Yutack and Kim, Jaesun and Hwang, Seungwoo and Han, Seungwu},
	year = {2024},
	pages = {4857--4868},
}
""")
    print("")
    if foundation_model == '7net-mf-ompa':
        print(r""" 2. Jaesun Kim, Jisu Kim, Jaehoon Kim, Jiho Lee, Yutack Park, Youngho Kang, Seungwu Han, Data-Efficient Multifidelity Training for High-Fidelity Machine Learning Interatomic Potentials, J. Am. Chem. Soc., 2024, 147 (1), pp 1042–1054, https://doi.org/10.1021/jacs.4c14455
@article{kim_sevennet_mf_2024,
	title = {Data-Efficient Multifidelity Training for High-Fidelity Machine Learning Interatomic Potentials},
	volume = {147},
	doi = {10.1021/jacs.4c14455},
	number = {1},
	journal = {J. Am. Chem. Soc.},
	author = {Kim, Jaesun and Kim, Jisu and Kim, Jaehoon and Lee, Jiho and Park, Yutack and Kang, Youngho and Han, Seungwu},
	year = {2024},
	pages = {1042--1054},
}
""")
        print("")

def orb_citations(foundation_model = ""):
    """
    Function to print the citations for Orb
    """
    print("")
    print(r""" 1. Mark Neumann, James Gin, Benjamin Rhodes, Steven Bennett, Zhiyi Li, Hitarth Choubisa, Arthur Hussey, Jonathan Godwin, Orb: A Fast, Scalable Neural Network Potential, arXiv:2410.22570, 2024, https://arxiv.org/abs/2410.22570
@misc{neumann2024orbfastscalableneural,
      title={Orb: A Fast, Scalable Neural Network Potential}, 
      author={Mark Neumann and James Gin and Benjamin Rhodes and Steven Bennett and Zhiyi Li and Hitarth Choubisa and Arthur Hussey and Jonathan Godwin},
      year={2024},
      eprint={2410.22570},
      archivePrefix={arXiv},
      primaryClass={cond-mat.mtrl-sci},
      url={https://arxiv.org/abs/2410.22570}, 
}
""")
    print("")
    if 'v3' in foundation_model:
        print(r""" 2. Benjamin Rhodes, Sander Vandenhaute, Vaidotas Šimkus, James Gin, Jonathan Godwin, Tim Duignan, Mark Neumann, Orb-v3: atomistic simulation at scale, arXiv:2504.06231, 2025, https://arxiv.org/abs/2504.06231
@misc{rhodes2025orbv3atomisticsimulationscale,
      title={Orb-v3: atomistic simulation at scale}, 
      author={Benjamin Rhodes and Sander Vandenhaute and Vaidotas Šimkus and James Gin and Jonathan Godwin and Tim Duignan and Mark Neumann},
      year={2025},
      eprint={2504.06231},
      archivePrefix={arXiv},
      primaryClass={cond-mat.mtrl-sci},
      url={https://arxiv.org/abs/2504.06231}, 
}
""")
        print("")

def grace_citations(foundation_model = ""):
    """
    Function to print the citations for Grace
    """
    print("")
    print(r""" Anton Bochkarev, Yury Lysogorskiy, Ralf Drautz, Graph Atomic Cluster Expansion for Semilocal Interactions beyond Equivariant Message Passing, Phys. Rev. X 14, 021036 (2024), https://doi.org/10.1103/PhysRevX.14.021036
@article{PhysRevX.14.021036,
  title = {Graph Atomic Cluster Expansion for Semilocal Interactions beyond Equivariant Message Passing},
  author = {Bochkarev, Anton and Lysogorskiy, Yury and Drautz, Ralf},
  journal = {Phys. Rev. X},
  volume = {14},
  issue = {2},
  pages = {021036},
  numpages = {28},
  year = {2024},
  month = {Jun},
  publisher = {American Physical Society},
  doi = {10.1103/PhysRevX.14.021036},
  url = {https://link.aps.org/doi/10.1103/PhysRevX.14.021036}
}
          """)
    print("")
    

def citation_grabber(log_file, framework):
    """
    Function to grab the citations from the log file
    """

    with open(log_file) as f:
        lines = f.readlines()
    
    config_line = lines[1]

    config_line = config_line.split(',')
    for config in config_line:
        config = config.strip()
        if 'foundation_model' in config:
            foundation_model = config.split(':')[1].strip()
            foundation_model = foundation_model.strip("'")
            break

    print(f"Found foundation model: {foundation_model}")

    if framework == 'MACE':
        mace_citations(foundation_model)
    elif framework == 'Mattersim':
        mattersim_citations()
    elif framework == 'SevenNet':
        sevennet_citations(foundation_model)
    elif framework == 'CP2K':
        print("Please refer to the CP2K log file for the citations.")
    elif framework == 'Orb':
        orb_citations(foundation_model)
    elif framework == 'Grace':
       grace_citations()


def frame_counter(file):
    """
    Count the number of frames in an xyz file
    """
    with open(file) as f:
        lines = f.readlines()
        n_atoms = int(lines[0])
        n_frames = int(len(lines)/(n_atoms+2))
    return n_frames


def extract_frames(file, each_nth_frame):
    """
    Extract a fraction of the frames from an xyz file without any questions (EXTRACT_XYZ workflow)
    """
    filename = file.split('/')[-1]
    filename = filename.split('.')[0]
    filename = f"extracted_each_{each_nth_frame}_frame_{filename}.xyz"

    each_nth_frame = int(each_nth_frame)

    atoms, coords, ener, forcesX, meta_data = xyz_reader(file)
    extracted_coords = coords[::each_nth_frame,:,:]
    if forcesX.shape[0] > 1:
        extracted_forces = forcesX[::each_nth_frame,:,:]
    else:
        extracted_forces = ""
    extracted_meta_data = meta_data[::each_nth_frame]
    xyz_writer(filename, atoms, extracted_coords, meta_data=extracted_meta_data ,forces=extracted_forces)

    return filename

def setup_bechmark_dir(coord_data, pbc_data, nsteps, mace_model, mattersim_model, sevennet_model, orb_model, grace_model):
    """
    Function to setup the benchmark directory
    """
    for nn in ['mace', 'mattersim', 'sevennet', 'orb', 'grace']:
        if os.path.isdir(nn):
            os.rmdir(nn)
        os.mkdir(nn)
        os.chdir(nn)

        if nn == 'mace':
            
            command = r"""amaceing_mace --run_type="MD" --config="{ """+f"""'project_name': 'mace_benchmark', 'coord_file': '../{coord_data}', 'pbc_list': '{pbc_data}', 'foundation_model': '{mace_model[0]}', 'model_size': '{mace_model[1]}', 'dispersion_via_simenv': 'n', 'temperature': '300', 'pressure': '1.0', 'thermostat': 'Langevin', 'nsteps': '{nsteps}', 'write_interval': 10, 'timestep': 0.5, 'log_interval': 10, 'print_ext_traj': 'y', 'simulation_environment': 'ase'"""+r"""}" """

            print("Creating directory for MACE benchmark: including the MACE input file and runscript.")
        
        elif nn == 'mattersim':

            command = r"""amaceing_mattersim --run_type="MD" --config="{"""+f"""'project_name': 'mattersim_benchmark', '../coord_file': '{coord_data}', 'pbc_list': '{pbc_data}', 'foundation_model': '{mattersim_model}', 'dispersion_via_simenv': 'n', 'temperature': '300', 'pressure': '1.0', 'thermostat': 'Langevin', 'nsteps': '{nsteps}', 'write_interval': 10, 'timestep': 0.5, 'log_interval': 100, 'print_ase_traj': 'y'"""+r"""}" """

            print("Creating directory for Mattersim benchmark: including the Mattersim input file and runscript.")

        elif nn == 'sevennet':

            command = r"""amaceing_sevennet --run_type="MD" --config="{"""+f"""'project_name': 'sevennet_benchmark', 'coord_file': '../{coord_data}', 'pbc_list': '{pbc_data}', 'foundation_model': '{sevennet_model[0]}', 'modal': '{sevennet_model[1]}', 'dispersion_via_simenv': 'n', 'temperature': '300', 'pressure': '1.0', 'thermostat': 'Langevin', 'nsteps': '{nsteps}', 'write_interval': 10, 'timestep': 0.5, 'log_interval': 100, 'print_ext_traj': 'y', 'simulation_environment': 'ase'"""+r"""}" """

            print("Creating directory for SevenNet benchmark: including the SevenNet input file and runscript.")

        elif nn == 'orb':
            
            command = r"""amaceing_orb --run_type="MD" --config="{"""+f"""'project_name': 'orb_benchmark', 'coord_file': '../{coord_data}', 'pbc_list': '{pbc_data}', 'foundation_model': '{orb_model[0]}', 'modal': '{orb_model[1]}', 'dispersion_via_simenv': 'n', 'temperature': '300', 'pressure': '1.0', 'thermostat': 'Langevin', 'nsteps': '{nsteps}', 'write_interval': 10, 'timestep': 0.5, 'log_interval': 100, 'print_ext_traj': 'y'"""+r"""}" """

            print("Creating directory for Orb benchmark: including the Orb input file and runscript.")

        elif nn == 'grace':

            command = r"""amaceing_grace --run_type="MD" --config="{"""+f"""'project_name': 'grace_benchmark', 'coord_file': '../{coord_data}', 'pbc_list': '{pbc_data}', 'foundation_model': '{grace_model}', 'temperature': '300', 'pressure': '1.0', 'thermostat': 'Langevin', 'nsteps': '{nsteps}', 'write_interval': 10, 'timestep': 0.5, 'log_interval': 100, 'print_ext_traj': 'y'"""+r"""}" """

            print("Creating directory for Grace benchmark: including the Grace input file and runscript.")

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        process.wait()
        os.chdir('..')

def recalc_bechmark_dir(ref_traj, pbc_data, force_file, mace_model, mattersim_model, sevennet_model, orb_model, grace_model):
    """
    Function to recalc an AIMD trajectory with different ML packages
    """
    nn_dict ={'mace': 0, 'mattersim': 0, 'sevennet': 0, 'orb': 0, 'grace': 0}

    # Check if the reference trajectory is a relative path (add ../)
    if ref_traj[0] == '.':
        ref_traj = f'../{ref_traj}'
    

    for nn in ['mace', 'mattersim', 'sevennet', 'orb', 'grace']:
        if os.path.isdir(nn):
            os.rmdir(nn)
        os.mkdir(nn)
        os.chdir(nn)

        print("""\n\n\n STARTING THE RECALCULATION OF THE REFERENCE TRAJECTORY WITH """+ f"{nn}"+"""\n\n\n""")

        if nn == 'mace':

            command = r"""amaceing_mace --run_type="RECALC" --config="{ """+f"""'project_name': 'benchmark', 'coord_file': '{ref_traj}', 'pbc_list': '{pbc_data}', 'foundation_model': '{mace_model[0]}', 'model_size': '{mace_model[1]}', 'dispersion_via_simenv': 'n', 'simulation_environment': 'ase'"""+r"""}" """
            
            print("Creating directory for MACE benchmark and recalcing the reference trajectory...")
        
        elif nn == 'mattersim':
            
            try: 
                import mattersim
                command = r"""amaceing_mattersim --run_type="RECALC" --config="{"""+f"""'project_name': 'benchmark', 'coord_file': '{ref_traj}', 'pbc_list': '{pbc_data}', 'foundation_model': '{mattersim_model}'"""+r"""}" """
                print("Creating directory for Mattersim benchmark and recalcing the reference trajectory...")
            except ModuleNotFoundError:
                print("Mattersim is currently not installed (in this environment). Please install it first or change to the respective environment.")
                print("The MatterSim Run can be run via: ")
                print("""amaceing_mattersim --run_type="RECALC" --config="{"""+f"project_name: benchmark, coord_file: {ref_traj}, pbc_list: {pbc_data}, foundation_model: {mattersim_model}"+"""}" """)
                command = "FAIL"
        
        elif nn == 'sevennet':
            
            try:
                import sevenn
                command = """amaceing_sevennet --run_type="RECALC" --config="{"""+f"""'project_name': 'benchmark', 'coord_file': '{ref_traj}', 'pbc_list': '{pbc_data}', 'foundation_model': '{sevennet_model[0]}', 'modal': '{sevennet_model[1]}', 'dispersion_via_ase': 'n'"""+r"""}" """
                print("Creating directory for SevenNet benchmark and recalcing the reference trajectory...")
            except ModuleNotFoundError:
                print("SevenNet is currently not installed (in this environment). Please install it first or change to the respective environment.")
                print("The SevenNet Run can be run via: ")
                print("""amaceing_sevennet --run_type="RECALC" --config="{"""+f"'project_name': benchmark, 'coord_file': {ref_traj}, 'pbc_list': {pbc_data}, 'foundation_model': {sevennet_model[0]}, 'modal': {sevennet_model[1]}, 'dispersion_via_simenv': 'n', 'simulation_environment': 'ase'"+"""}" """)
                command = "FAIL"

        elif nn == 'orb':
            
            try:
                import orb_models
                command = """amaceing_orb --run_type="RECALC" --config="{"""+f"""'project_name': 'benchmark', 'coord_file': '{ref_traj}', 'pbc_list': '{pbc_data}', 'foundation_model': '{orb_model[0]}', 'modal': '{orb_model[1]}', 'dispersion_via_simenv': 'n', 'simulation_environment': 'ase'"""+r"""}" """
                print("Creating directory for Orb benchmark and recalcing the reference trajectory...")
            except ModuleNotFoundError:
                print("Orb is currently not installed (in this environment). Please install it first or change to the respective environment.")
                print("The Orb Run can be run via: ")
                print("""amaceing_orb --run_type="RECALC" --config="{"""+f"'project_name': benchmark, 'coord_file': {ref_traj}, 'pbc_list': {pbc_data}, 'foundation_model': {orb_model[0]}, 'modal': {orb_model[1]}, 'dispersion_via_simenv': 'n'"+"""}" """)
                command = "FAIL"

        elif nn == 'grace':
            
            try:
                import tensorpotential
                command = """amaceing_grace --run_type="RECALC" --config="{"""+f"""'project_name': 'benchmark', 'coord_file': '{ref_traj}', 'pbc_list': '{pbc_data}', 'foundation_model': '{grace_model}', 'simulation_environment': 'ase'"""+r"""}" """
                print("Creating directory for Grace benchmark and recalcing the reference trajectory...")
            except ModuleNotFoundError:
                print("Grace is currently not installed (in this environment). Please install it first or change to the respective environment.")
                print("The Grace Run can be run via: ")
                print("""amaceing_grace --run_type="RECALC" --config="{"""+f"'project_name': benchmark, 'coord_file': {ref_traj}, 'pbc_list': {pbc_data}, 'foundation_model': {grace_model}, 'simulation_environment': ase'"+"""}" """)
                command = "FAIL"

        if command != "FAIL":
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            process.wait()
        
        os.chdir('..')


    # Run directly the EVAL_ERROR workflow
    # Check if the reference force file is a relative path (add ../)
    if force_file[0] == '.':
        force_file = f'../{force_file}'
        try:
            os.path.isfile(force_file)
        except:
            print("Force file does not exist!")


    for nn in ['mace', 'mattersim', 'sevennet', 'orb', 'grace']:
        os.chdir(nn)
        print("""\n"""+f"Running the EVAL_ERROR workflow for {nn}..." + """\n""")

        # Run the EVAL_ERROR workflow
        try: 
            # Check if energy file exists
            os.path.isfile(f'energies_recalc_with_{nn}_model_benchmark.xyz')
            run_eval_error([ref_traj, force_file, f'energies_recalc_with_{nn}_model_benchmark', f'forces_recalc_with_{nn}_model_benchmark.xyz'])
        except:
            print(f"The automatic evaluation of the {nn} run could not done, because the recalcuation did not start. Please run the recalculation first.")
            print("The EVAL_ERROR Run can be run via: ")
            print("""amaceing_utils --run_type="EVAL_ERROR" --config="{"""+f"""'ener_filename_ground_truth': '{ref_traj}', 'force_filename_ground_truth': '{force_file}', 'ener_filename_compare': 'energies_recalc_with_{nn}_model_benchmark', 'force_filename_compare': 'forces_recalc_with_{nn}_model_benchmark.xyz'"""+r"""}" """)

        os.chdir('..')


def lmp_reader(file):
    """
    Read an LAMMPS dump file and return positions or forces
    """
    if "fx" in file:
        # Replace the fx, fy, fz with x, y, z in the file
        with open(file, 'r') as f:
            content = f.read()
        content = content.replace('fx', 'x')
        content = content.replace('fy', 'y')
        content = content.replace('fz', 'z')
        with open("tmp.lammpstrj", 'w') as f:
            f.write(content)
        frames = read("tmp.lammpstrj", index=":")
        os.remove("tmp.lammpstrj")
    else:
        frames = read("10steps.lammpstrj", index=":") 
    positions = []
    for frame in frames:
        positions.append(frame.get_positions())
    positions = np.array(positions)

    return positions

# Question functions
def ask_for_float_int(question, default):
    """
    Ask user for a float or integer value
    """
    value = ' '
    value = input(question + " [" + str(default) + "]: ")
    if value == '':
        value = str(default)
    if "." in value:
        while np.logical_and(not value.split('.')[0].isnumeric(), not value.split('.')[1].isnumeric()):
            value = input(question + " [" + str(default) + "]: ")
            if value == '':
                value = str(default)
            elif value.isnumeric() == False:
                if value.split('.')[0].isnumeric() == False and value.split('.')[1].isnumeric() == False:
                    print("Invalid input. Please enter a float or integer.")
    else:
        while not value.isnumeric():
            value = input(question + " [" + str(default) + "]: ")
            if value == '':
                value = str(default)
            elif value.isnumeric() == False:
                print("Invalid input. Please enter a float or integer.")
    return value

def ask_for_non_cubic_pbc():
    """
    Ask user for box length (orthogonal) or pbc vector (non-orthogonal) 
    """
    default = 10.0
    dim_row_dict = {'x': 'first', 'y': 'second', 'z': 'third'}
    # Build the box matrix
    box_mat = np.zeros((3, 3))

    for dim in ['x', 'y', 'z']:
        question = f'What is the box length/vector in the {dim}-direction/{dim_row_dict[dim]} row in Å? ("20.0" or "20.0, 1.0, 0.7")'
        value = ' '
        value = input(question + " [" + str(default) + "]: ")
        if value == '':
            value = str(default)

        # Check if the input is a float/int or a vector
        if "," in value:
            value = value.split(',')
            value = [float(i) for i in value]
            value = np.array(value)
            if len(value) != 3:
                print("Invalid input. Please enter a vector with 3 elements.")
                value = ' '
                while len(value) != 3:
                    value_tmp = input(question + " [" + str(default) + "]: ")
                    if value_tmp == '':
                        value_tmp = str(default)
                    if "," in value_tmp:
                        value_tmp = value_tmp.split(',')
                        value_tmp = [float(i) for i in value_tmp]
                        value = np.array(value_tmp)
                        if len(value) != 3:
                            print("Invalid input. Please enter a vector with 3 elements.")
            # Convert the orthogonal box length to a vector
            if dim == 'x':
                box_mat[0, :] = value
            elif dim == 'y':
                box_mat[1, :] = value
            elif dim == 'z':
                box_mat[2, :] = value

        else:
            if "." in value:
                while np.logical_and(not value.split('.')[0].isnumeric(), not value.split('.')[1].isnumeric()):
                    value = input(question + " [" + str(default) + "]: ")
                    if value == '':
                        value = str(default)
                    elif value.isnumeric() == False:
                        if value.split('.')[0].isnumeric() == False and value.split('.')[1].isnumeric() == False:
                            print("Invalid input. Please enter a float or integer.")
            else:
                while not value.isnumeric():
                    value = input(question + " [" + str(default) + "]: ")
                    if value == '':
                        value = str(default)
                    elif value.isnumeric() == False:
                        print("Invalid input. Please enter a float or integer.")
                
            # Convert the orthogonal box length to a vector
            value= float(value)
            if dim == 'x':
                box_mat[0, :] = np.array([value, 0.0, 0.0])
            elif dim == 'y':
                box_mat[1, :] = np.array([0.0, value, 0.0])
            elif dim == 'z':
                box_mat[2, :] = np.array([0.0, 0.0, value])
    return box_mat

def ask_for_int(question, default):
    """
    Ask user for an integer value
    """
    value = ' '
    value = input(question + " [" + str(default) + "]: ")
    if value == '':
        value = str(default)
    while not value.isnumeric():
        value = input(question + " [" + str(default) + "]: ")
        if value == '':
            value = str(default)
        elif value.isnumeric() == False:
            print("Invalid input. Please enter an integer.")
    return value

def ask_for_yes_no(question, default):
    """
    Ask user for a yes or no answer
    """
    value = ' '
    while value != 'y' and value != 'n':
        value = input(question + " [" + default + "]: ")
        if value == '':
            value = default
        elif value != 'y' and value != 'n':
            print("Invalid input. Please enter 'y' or 'n'.")
    return value

def ask_for_yes_no_pbc(question, default):
    """
    Ask user for a yes or no answer or directly read pbc file
    """
    value = ' '
    while value != 'y' and value != 'n' and value != 'pbc':
        value = input(question + " [" + default + "]: ")
        if value == '':
            value = default
        elif value != 'y' and value != 'n':
            # pbc file import: check if the file exists and if its a 3x3 matrix
            if os.path.isfile(value):
                if len(np.loadtxt(value).shape) == 2 and np.loadtxt(value).shape[0] == 3 and np.loadtxt(value).shape[1] == 3:
                    break
            else:
                print("Invalid input. Please enter 'y' or 'n' or 'pbc'-path.")
    return value

# Write the configuation file
def write_log(input_config):
    """
    Write configuration to log file with the right format to be read by direct input
    """
    with open('utils.log', 'w') as output:
        output.write("Utils function run with the following configuration:\n") 
        output.write(f'"{input_config}"')