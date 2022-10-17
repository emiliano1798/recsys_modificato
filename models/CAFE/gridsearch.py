import argparse
import json
from models.CAFE.cafe_utils import *
import wandb
import sys
import numpy as np
import shutil
import os
from sklearn.model_selection import ParameterGrid
import subprocess
from tqdm import tqdm

TRAIN_FILE_NAME = 'train_neural_symbol.py'
TEST_FILE_NAME = 'execute_neural_symbol.py'

def load_metrics(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        metrics = json.load(f)
    return metrics
def save_metrics(metrics, filepath):
    with open(filepath, 'w') as f:
        json.dump(metrics, f)
def save_cfg(configuration, filepath):
    with open(filepath, 'w') as f:
        json.dump(configuration, f)     
def metrics_average(metrics):
    avg_metrics = dict()
    for k, v in metrics.items():
        avg_metrics[k] = sum(v)/max(len(v),1)
    return avg_metrics

def save_best(best_metrics, test_metrics, grid):
    dataset_name = grid["dataset"]
    if best_metrics is None:
        save_metrics(test_metrics, f'{BEST_TEST_METRICS_FILE_PATH[dataset_name]}')
        save_cfg(grid, f'{BEST_CFG_FILE_PATH[dataset_name] }')
        shutil.rmtree(BEST_CFG_DIR[dataset_name])
        shutil.copytree(TMP_DIR[dataset_name], BEST_CFG_DIR[dataset_name] )
        return 
    x = test_metrics[OPTIM_HPARAMS_METRIC][-1]
    best_x = best_metrics[OPTIM_HPARAMS_METRIC][-1]
    # if avg total reward is higher than current best
    if best_x > x :
        save_metrics(test_metrics, f'{BEST_TEST_METRICS_FILE_PATH[dataset_name]}')
        save_cfg(grid, f'{BEST_CFG_FILE_PATH[dataset_name] }')
        shutil.rmtree(BEST_CFG_DIR[dataset_name])
        shutil.copytree(TMP_DIR[dataset_name], BEST_CFG_DIR[dataset_name] )





def main(args):


    chosen_hyperparam_grid = {"batch_size": [64],#128], 
           "dataset": ["lfm1m", "ml1m"], 
            "deep_module": [True], 
            "do_execute": [False], 
            "do_infer": [False], 
            "embed_size": [100], 
            "epochs": [40], 
            "gpu": [0], 
            "lr": [0.1], 
            "name": ["neural_symbolic_model"],
             "rank_weight": [10.0],
              "sample_size": [15], 
              "seed": [123], 
              "steps_per_checkpoint": [100], 
              "topk_candidates": [10], 
              "use_dropout": [True],
                "wandb": [True if args.wandb else False], 
     "wandb_entity": [args.wandb_entity]}





    hparam_grids = ParameterGrid(chosen_hyperparam_grid)
    print('num_experiments: ', len(hparam_grids))

    for i, configuration in enumerate(tqdm(hparam_grids)):
        dataset_name = configuration["dataset"]
        makedirs(dataset_name)
        if args.wandb:
            wandb.init(project=f'grid_cafe_{dataset_name}',
                           entity=args.wandb_entity, config=configuration)    
            
         

        CMD = ["python3", TRAIN_FILE_NAME]

        for k,v in configuration.items():
                if k == 'wandb':
                    CMD.extend([f'--{k}'])
                elif isinstance(v,list):
                    cmd_args = [f'--{k}'] + [f" {val} " for val in v]
                    CMD.extend( cmd_args )
                else:
                    CMD.extend( [f'--{k}', f'{v}'] )     
        print(f'Executing job {i+1}/{len(hparam_grids)}: ',configuration)
        subprocess.call(CMD)#,
        #        stdout=subprocess.DEVNULL,
        #        stderr=subprocess.STDOUT)
        
        '''        
        # cafe and ucpr have the same command line args, pgpr does not, so the call below will have to be 
        # modified accordingly
        print('Done training, testing phase')
        CMD = ["python3", TEST_FILE_NAME]
        for k,v in configuration.items():
                if k == 'wandb':
                    CMD.extend([f'--{k}'])
                elif isinstance(v,list):
                    cmd_args = [f'--{k}'] + [f" {val} " for val in v]
                    CMD.extend( cmd_args )
                else:
                    CMD.extend( [f'--{k}', f'{v}'] )     
        subprocess.call(CMD)
        '''

        save_cfg(configuration, CFG_FILE_PATH[dataset_name])        
        test_metrics = load_metrics(TEST_METRICS_FILE_PATH[dataset_name])
        best_metrics = load_metrics(BEST_TEST_METRICS_FILE_PATH[dataset_name])
        save_best(best_metrics, test_metrics, configuration)
    
        if args.wandb:
            wandb.log(test_metrics)





if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--wandb", action="store_true", help="If passed, will log to Weights and Biases.")
    parser.add_argument(
        "--wandb_entity",
        required="--wandb" in sys.argv,
        type=str,
        help="Entity name to push to the wandb logged data, in case args.wandb is specified.",
    )    
    args = parser.parse_args()
    main(args)
                 
    