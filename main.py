import sys, os, json
import torch
import numpy as np
import argparse
from datetime import datetime

sys.path.append('src') 
from load_data import dataPrep
from cnn_net import CNNNet
from fc_net import FCNet
from linear_net import LinNet
from helper import compare_thresholds, performance, createDirs
from heatmap import *
from plotbestworst import *

from torch.utils.tensorboard import SummaryWriter

pwd = os.getcwd()
        
if __name__ == '__main__':

    # Print start time
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Start Time =", current_time)
    print()
    
    # Command line arguments
    parser = argparse.ArgumentParser(description='Main file combining all three networks')
    parser.add_argument('--input', default=os.path.join('data', 'torch_data_ID'), type=str, help="location for input data files")
    parser.add_argument('--network', default='cnn', type=str, help="Neural network to be used. Default: cnn. Options: [ cnn | fc | linear ]")
    parser.add_argument('--view', default='local', type=str, help="view of data (as described in paper): can be local, global or both; default: local")
    parser.add_argument('--user', default='s', type=str, help="User currently running the data: should be changed everytime repo is pulled")
    parser.add_argument('--param', type=str, help="location of parameter file. Default will use <network>_<view>.json")
    parser.add_argument('--result', default='results', type=str, help="location of results")
    parser.add_argument('-v', default=1 , help="Verbosity (0 = no command line output, 1 = print training loss); default: 1")
    args = parser.parse_args()

    # Check if view is valid
    if (args.view != 'local' and args.view != 'global' and args.view != 'both'):
        print("Error: view needs to be local, global or both")
        sys.exit(1)
    else:
        view = args.view
    
    # Get the hyper-parameter file
    if args.param is None:
        param_file = args.network + "_" + args.view + ".json"
    else:
        param_file = args.param

    network = args.network
    user = args.user
    input_folder = args.input
    res_path = args.result
    verbosity = args.v

    # Create the output directories
    createDirs(res_path)
    
    if args.param is None:
        param_file = args.network + "_" + args.view + ".json"
    else:
        param_file = args.param
    print("Using json parameter file: {}".format(param_file))

    # Get parameters from json parameter file    
    with open(os.path.join('param', param_file)) as paramfile:
        params = json.load(paramfile)

    lr = params['optim']['learning rate']
    beta_l = params['optim']['beta 1']
    beta_h = params['optim']['beta 2']
    epsilon = params['optim']['epsilon']
    amsgrad = params['optim']['amsgrad']
    wd = params['optim']['weight decay']

    num_epochs = params['training']['num epochs']
    trainbs = params['training']['batch size']
    testbs = params['testing']['batch size']

    tuned_param = params['output']['tuned params']

    # Generic name for output files
    res_file = '{}_{}_{}_{}'.format(network, view, user, tuned_param)

    # Create directory and files for TensorBoard
    for i in range(1, 5000):
        cur_name = os.path.join(res_path, 'TensorBoard', network, view, '{}_{}'.format(res_file, str(i)))
        if not os.path.isdir(cur_name):
            tb_ID = cur_name
            res_file = '{}_{}'.format(res_file, str(i))
            break


    # Directory for TensorBoard
    tb_ID = os.path.join(res_path, 'TensorBoard', network, view, res_file)
    writer = SummaryWriter(tb_ID)
    print("Using TensorBoard ID: {}".format(tb_ID))
    print()

    # Training and Testing data
    train_loader, test_loader = dataPrep(input_folder, trainbs, testbs)
    train_set = list(train_loader)
    test_set = list(test_loader)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Get the proper network
    if network == "cnn":
        model = CNNNet(view, device).to(device)
    elif network == "fc":
        model = FCNet(view, device).to(device)
    elif network == "linear":
        model = LinNet(view, device).to(device)
    else:
        print("Wrong Network Name. Only options are [ cnn | fc | lin ]")
        sys.exit(1)

    # Optimizer and loss function
    optim = torch.optim.Adam(model.parameters(), lr=lr, betas=(beta_l, beta_h), eps=epsilon, weight_decay=wd, amsgrad=amsgrad)
    loss_fn = torch.nn.BCELoss()

    # Training and testing loop
    print("Training...")
    for e in range(num_epochs):
        
        # Train the model
        model.train()
        train_loss_val = 0
        for batch_idx_train, (data_train, labels_train) in enumerate(train_loader):

            # Get outputs and labels
            outputs_train = model(data_train)
            label_train = labels_train[0]
            kepid = labels_train[1]
            tce_plnt_num = labels_train[2]
            
            label_train = label_train.to(device)
            label_train = label_train.view(-1, 1)

            # Backpropogate and get training loss
            loss_train = loss_fn(outputs_train, label_train)
            optim.zero_grad()
            loss_train.backward()
            optim.step()
            train_loss_val += float(loss_train.item())

        # Validate the model with test dataset
        model.eval()
        test_loss_val = 0

        # Initialize ID lists
        listof_kepids = []
        listof_tce_plnt_num = []
        listof_labels = []
        listof_preds = []

        with torch.no_grad():
            for batch_idx_test, (data_test, labels_test) in enumerate(test_loader):
                # Get outputs and labels
                outputs_test = model(data_test)
                label_test = labels_test[0]

                # Store ID'd data
                label = labels_test[0].tolist()
                kepid = labels_test[1].tolist()
                tce_plnt_num = labels_test[2].tolist()
                output_test = outputs_test.tolist()

                listof_kepids += kepid
                listof_tce_plnt_num += tce_plnt_num
                listof_labels += label

                for pred in output_test:
                    listof_preds += pred

                label_test = label_test.to(device)
                label_test = label_test.view(-1, 1)
                loss_test = loss_fn(outputs_test, label_test)
                test_loss_val += float(loss_test.item())

        # Obtain average loss per "data point"
        train_loss_avg = train_loss_val / len(train_set)
        test_loss_avg = test_loss_val / len(test_set)
        
        # Obtain performance metrics for testing
        perf_list_train = performance(model, train_set)
        perf_list_test = performance(model, test_set)

        # Print training and test loss 
        if verbosity and e % 1 == 0:
            print("Epoch [{}/{}] \t Train Loss: {} \t Test Loss: {} \t Test accuracy: {} \t Test precision: {}".format(
                e+1,
                num_epochs,
                round(train_loss_avg, 3),
                round(test_loss_avg, 3),
                round(perf_list_test[0], 3),
                round(perf_list_test[1], 3)))

        # Add all metrics to TensorBoard
        writer.add_scalar('Training loss', train_loss_avg, float(e))
        writer.add_scalar('Training accuracy', float(perf_list_train[0]), float(e))
        writer.add_scalar('Training precision', float(perf_list_train[1]), float(e))
        writer.add_scalar('Training recall', float(perf_list_train[2]), float(e))
        writer.add_scalar('Training AUC', float(perf_list_train[3]), float(e))

        writer.add_scalar('Test loss', test_loss_avg, float(e))
        writer.add_scalar('Test accuracy', float(perf_list_test[0]), float(e))
        writer.add_scalar('Test precision', float(perf_list_test[1]), float(e))
        writer.add_scalar('Test recall', float(perf_list_test[2]), float(e))
        writer.add_scalar('Test AUC', float(perf_list_test[3]), float(e))


    # Important training/testing parameters
    tf_params = {
        "epochs": float(num_epochs),
        "lr": float(lr),
        "beta lower": beta_l,
        "beta upper": beta_h,
        "amsgrad": amsgrad,
        "epsilon": epsilon,
        "weight decay": wd,
        "training bs": float(trainbs),
        "testing bs": float(testbs),
        "view": view
    }


    # Add last performance metrics to TensorBoard
    tf_metric = {
        "Training loss": train_loss_avg,
        "Training accuracy": float(perf_list_train[0]),
        "Training precision": float(perf_list_train[1]),
        "Training recall": float(perf_list_train[2]),
        "Training AUC": float(perf_list_train[3]),
        "Test loss": test_loss_avg,
        "Test accuracy": float(perf_list_test[0]),
        "Test precision": float(perf_list_test[1]),
        "Test recall": float(perf_list_test[2]),
        "Test AUC": float(perf_list_test[3])
    }

    print()

    writer.add_hparams(tf_params, tf_metric)
    writer.close()

    # Print final performance metrics
    print("Training:")
    print("acc: {} \t prec: {} \t rec: {} \t AUC: {}".format(
        round(perf_list_train[0], 3),
        round(perf_list_train[1], 3),
        round(perf_list_train[2], 3),
        round(perf_list_train[3], 3)))
    print()

    print("Testing:")
    print("acc: {} \t prec: {} \t rec: {} \t AUC: {}".format(
        round(perf_list_test[0], 3),
        round(perf_list_test[1], 3),
        round(perf_list_test[2], 3),
        round(perf_list_test[3], 3)))
    print()

    # Find difference between predictions and labels
    listof_diff = list(np.absolute(np.array(listof_preds) - np.array(listof_labels)))
    IDs = np.transpose(np.array([listof_kepids, listof_tce_plnt_num, listof_labels, listof_preds, listof_diff]))

    # Sort list of IDs by magnitude of prediction error
    IDs = IDs[IDs[:, 4].argsort()]
    # Format: [kepid, tce_plnt_num, label, prediction, difference]

    if verbosity:
        best_5 = list(IDs[:5, :])
        worst_5 = list(IDs[-5:, :])

        # Print 5 best predictions; first rows in the array
        print("5 best predictions:")
        for pc in best_5:
            print("kepid: {} \t tce_plnt_num: {} \t label: {} \t prediction: {} \t difference: {}".format(
                int(pc[0]),
                int(pc[1]),
                int(pc[2]),
                round(pc[3], 3),
                round(pc[4], 3)))
        print()

        # Print 5 worst predictions; last rows in the array
        print("5 worst predictions:")
        for pc in worst_5:
            print("kepid: {} \t tce_plnt_num: {} \t label: {} \t prediction: {} \t difference: {}".format(
                int(pc[0]),
                int(pc[1]),
                int(pc[2]),
                round(pc[3], 3),
                round(pc[4], 3)))
        print()

    # Print end time
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("End Time =", current_time)


    # Perform testing
    if verbosity:
        model.eval()
        with torch.no_grad():
            # Create heatmap
            create_heatmap(model, input_folder, view, os.path.join(res_path, 'plots', network, view, 'heatmap_' + res_file + '.png'))

            # Save outputs and plot
            output = torch.zeros([len(test_loader.dataset), 4], dtype=torch.float32)
            counter = 0

            # Iterate through test dataset
            for batch_idx_test, (data_test, labels_test) in enumerate(test_loader):

                # Get model output
                outputs_test = model(data_test)

                # Get labels from dataset
                label_test = labels_test[0]
                label_test = label_test.view(-1, 1)
                kepid = labels_test[1]
                kepid = kepid.view(-1, 1)
                tce_plnt_num = labels_test[2]
                tce_plnt_num = tce_plnt_num.view(-1, 1)

                # Save batch to tensor
                output[counter:counter+data_test.shape[0], 0] = kepid[:,0]
                output[counter:counter+data_test.shape[0], 1] = tce_plnt_num[:,0]
                output[counter:counter+data_test.shape[0], 2] = label_test[:,0]
                output[counter:counter+data_test.shape[0], 3] = outputs_test[:,0]
                
                counter += data_test.shape[0]

            # Save testing probabilities and labels for light curves
            header = 'kepid, tce_plnt_num, true_label, out_label'
            np.savetxt(os.path.join(res_path, 'testing_probabilities', network, view, res_file + '.csv'), output, delimiter=',', header=header)
            torch.save(output, os.path.join(res_path, 'testing_probabilities', network, view, res_file + '.pt'))

            # Plot precision-recall plot
            compare_thresholds(output[:,3], output[:,2], os.path.join(res_path, 'plots', network, view, 'precision_recall_' + res_file + '.png'))

    print("Finished")

    # To open the runs for this model and view in TensorBoard:
    tb_dir = res_path + '/TensorBoard/' + network +  "/" + view + "/"
    print("To open run data for the current model and view in TensorBoard, run in terminal:")
    print("tensorboard --logdir=" + tb_dir)
