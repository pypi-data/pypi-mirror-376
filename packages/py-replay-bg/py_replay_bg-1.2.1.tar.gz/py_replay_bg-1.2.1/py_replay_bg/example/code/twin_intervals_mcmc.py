import os
import numpy as np

from multiprocessing import freeze_support

from utils import load_test_data, load_patient_info

from py_replay_bg.py_replay_bg import ReplayBG
from py_replay_bg.visualizer import Visualizer
from py_replay_bg.analyzer import Analyzer


if __name__ == '__main__':
    freeze_support()

    # Set verbosity
    verbose = True
    plot_mode = False

    # Set the number of steps for MCMC
    n_steps = 5000  # 5k is for testing. In production, this should be >= 50k

    # Set other parameters for twinning
    blueprint = 'multi-meal'
    save_folder = os.path.join(os.path.abspath(''),'..','..','..')
    parallelize = True

    # load patient_info
    patient_info = load_patient_info()
    p = np.where(patient_info['patient'] == 1)[0][0]
    # Set bw and u2ss
    bw = float(patient_info.bw.values[p])
    u2ss = float(patient_info.u2ss.values[p])
    x0 = None
    previous_data_name = None

    # Initialize the list of results
    replay_results_interval = []
    data_interval = []

    # Instantiate ReplayBG
    rbg = ReplayBG(blueprint=blueprint, save_folder=save_folder,
                   yts=5, exercise=False,
                   seed=1,
                   verbose=verbose, plot_mode=plot_mode)

    # Set interval to twin
    start_day = 1
    end_day = 2

    # Twin the interval
    for day in range(start_day, end_day+1):

        # Step 1: Load data and set save_name
        data = load_test_data(day=day)
        save_name = 'data_day_' + str(day) + '_interval'

        print("Twinning " + save_name)

        # Run twinning procedure
        rbg.twin(data=data, bw=bw, save_name=save_name,
                 twinning_method='mcmc',
                 parallelize=parallelize,
                 n_steps=n_steps,
                 x0=x0, u2ss=u2ss, previous_data_name=previous_data_name)

        # Replay the twin with the same input data
        replay_results = rbg.replay(data=data, bw=bw, save_name=save_name,
                                    twinning_method='mcmc',
                                    save_workspace=True,
                                    x0=x0, previous_data_name=previous_data_name,
                                    save_suffix='_twin_mcmc')
        # Append results
        replay_results_interval.append(replay_results)
        data_interval.append(data)

        # Set initial conditions for next day equal to the "ending conditions" of the current day
        x0 = replay_results['x_end']['realizations'][0].tolist()

        # Set previous_data_name
        previous_data_name = save_name

    Visualizer.plot_replay_results_interval(replay_results_interval, data_interval=data_interval)
    analysis = Analyzer.analyze_replay_results_interval(replay_results_interval, data_interval=data_interval)
    print('Fit MARD: %.2f %%' % analysis['median']['twin']['mard'])
