import torch
import torch.nn as nn

## PLEASE replace this linear network with a convolutional NN according to the paper's architecture
## Make sure it outputs a binary value between 0 and 1, and takes in a variable number of inputs
## depending on whether param_global or param_local was chosen.

class Net_CNN_Local(nn.Module):
    def __init__(self, per_layer_fc):
        super(Net_CNN_Local, self).__init__()

        self.conv_in = nn.Conv1d(201, 16, 5)        # Da fuck????
        self.conv_1 = nn.Conv1d(16, 16, 5)          # Da fuck????
        self.conv_2 = nn.Conv1d(32, 32, 5)          # Da fuck????
        self.conv_3 = nn.Conv1d(32, 32, 5)          # Da fuck????

        self.maxpool_1 = nn.MaxPool1d(7, stride=2)
        self.maxpool_out = nn.MaxPool1d(7, stride=2)

        self.fc_in = nn.Linear(per_layer_fc[0], per_layer_fc[1], bias=True)
        self.fc_1 = nn.Linear(per_layer_fc[1], per_layer_fc[2], bias=True)
        self.fc_2 = nn.Linear(per_layer_fc[2], per_layer_fc[3], bias=True)
        self.fc_3 = nn.Linear(per_layer_fc[3], per_layer_fc[4], bias=True)
        self.fc_out = nn.Linear(per_layer_fc[4], per_layer_fc[5], bias=True)

    def forward(self, h):
        c1 = torch.relu(self.conv_in(h))
        c2 = torch.relu(self.conv_1(c1))
        m1 = self.maxpool_1(c2)             # Need relu?
        c3 = torch.relu(self.conv_2(m1))
        c4 = torch.relu(self.conv_3(c3))
        m2 = self.maxpool_out(c4)           # Need relu?
        
        h1 = torch.relu(self.fc_in(m2))
        h2 = torch.relu(self.fc_1(h1))
        h3 = torch.relu(self.fc_2(h2))
        h4 = torch.relu(self.fc_3(h3))
        y = torch.sigmoid(self.fc_out(h4))
        return y

    def reset(self):
        self.conv_in.reset_parameters()
        self.conv_1.reset_parameters()
        self.conv_2.reset_parameters()
        self.conv_3.reset_parameters()

        #self.maxpool_1.reset_parameters()          # Maxpool doesn't need reset since it doesn't have any learnable weights?
        #self.maxpool_out.reset_parameters()

        self.fc_in.reset_parameters()
        self.fc_1.reset_parameters()
        self.fc_2.reset_parameters()
        self.fc_3.reset_parameters()
        self.fc_out.reset_parameters()