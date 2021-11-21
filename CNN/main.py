## CNN
## Scaffolding by Sam - if you don't know what I meant in the long text sections, ask me
## src/nn_gen.py has the neural network copied from A3, using linear layers. Need to replace that with
## convolutional layers

import numpy as np  # loading in b values
import json, sys
import matplotlib.pyplot as plt
import torch.optim as optim
import random
import os
import torch

sys.path.append('src')
sys.path.append('helper_gen')

# from nn_gen import Net
import helper_gen as f
from nn_gen import Net_CNN_Local

if __name__ == '__main__':
    args = f.make_parser()

    save_location = str(args.res_path)

    json_file = open(args.param)
    hp = json.load(json_file)
    json_file.close()

    num_epochs = int(hp['optim']['num_epochs'])
    per_layer_conv = hp['model']['per_layer_conv']
    per_layer_fc = hp['model']['per_layer_fc']
    learning_rate = float(hp['optim']['learning_rate'])
    wd = int(hp['optim']['wd'])
    momentum = float(hp['optim']['momentum'])
    nesterov = int(hp['optim']['nesterov'])

    model = Net_CNN_Local(per_layer_fc).to("cpu")

    num_inputs = 201
    num_fake_curves = 10

    if args.param == 'param/param_global.json':
        num_inputs = 2001


    loss_fn = torch.nn.CrossEntropyLoss(reduction='mean')

    ## List of optimizers
    optimizer = optim.SGD(model.parameters(), lr=learning_rate, momentum=momentum, nesterov=nesterov)
    # optimizer = optim.SGD(model.parameters(), lr=1e-1)
    # optimizer = optim.SGD(model.parameters(), lr=1e-1, momentum=0.98)
    # optimizer= optim.Adagrad(model.parameters(), lr=1e-1, lr_decay=0)
    # optimizer= optim.Adadelta(model.parameters(), lr=1e+1, rho=0.99)
    # optimizer= optim.RMSprop(model.parameters(), lr=1e0, alpha=0.9, momentum=0.1, centered=False)
    # optimizer = optim.Adam(model.parameters(), lr=4e-4, betas=(0.9, 0.99), amsgrad=False)
    # optimizer = optim.Adam(model.parameters(), lr=4e-4)


    ######################### Data generation ####################
    ## Generate random local-looking data that looks like a y=x**2 curve (with some random fluctuations):
    # Note: This is untested, might have some mistakes here
    fake_planets = []
    fake_non_planets = []
    light_curve_linspace = np.linspace(-1, 1, num=num_inputs)

    for i in range(num_fake_curves):
        # PLEASE multiply light_curve_linspace values (x) by (x**2) * rand
        # where rand is a random number between 0.9 and 1.1 to get somewhat random looking data.
        f_planet = lambda x: (x ** 2) * random.uniform(0.8, 1.2)
        light_curve_planets = f_planet(light_curve_linspace)

        f_non_planet = lambda x: abs(x) * random.uniform(0.8, 1.2)
        light_curve_non_planets = f_non_planet(light_curve_linspace)

        fake_planets.append(light_curve_planets)
        fake_non_planets.append(light_curve_non_planets)

    fake_planets = np.array(fake_planets)

    print(fake_planets.shape)
    print(fake_planets)

    plt.plot(light_curve_linspace, fake_planets[0,:], label="Fake planet example", color="orange")

    plt.legend()
    plt.show()

    '''
    
  
    # Convert fake light curve to a np array, then to a tensor
    fake_curve_np = np.array(fake_curve_array, dtype=np.float32)
    fake_curve_tensor = torch.from_numpy(fake_curve_np).float()

    ######################### Bad data generation ####################
    # Here copy the above code called 'Data generation', but replace the function
    # from x**2 to something else but similar, like x**(3/2) or abs(x).
    # Then label the correct data with a 1, and the incorrect data with a 0
    # Combine and mix both datas into one tensor used to train the NN
    # For this you might want to keep 20% of the good data (x**2) unlabeled to be used
    # as testing data.
    # Call the training data tensor: training_tensor
'''
    # Placeholder:
    training_tensor = 0

    listof_loss = []
    prob_list = []

    for epoch in range(int(num_epochs)): # num epochs should already be an int

        prob = model(training_tensor.reshape(-1,1).float()) 

        ## loss is the sum of differences between the data labels and the prediction of the model
        ## PLEASE code that in. --> Made a loss module in nn_gen.py 
        # Does Cross entropy loss do this???

        loss_current = loss_fn(prob, 'known_labels_here')
        listof_loss.append(loss_current.item())

        optimizer.zero_grad()
        loss_current.backward()
        optimizer.step()

        # PLEASE Print out loss every few iterations
        if verbosity and (epoch%5 == 0) :
            print('Epoch: {} \t Training Predictions: {}'.format(epoch, prob))
            print("KL Loss: \t {}".format(loss_current))
    # PLEASE add the final, trained, probability distribution and save as a csv file to outputs/prob_dist.csv























