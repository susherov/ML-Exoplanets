import torch.nn as nn
import torch


class FCNet(nn.Module):
    def __init__(self, view, device):
        '''
        Fully Connected Neural Network
        size : size of data
        view : view of TCE data -> 'global' | 'local' | 'both'
        '''
        super(FCNet, self).__init__()
        self.view = view
        self.device = device

        if view == 'both':
            # Local view FC layers
            self.a1 = nn.Linear(201, 100)
            self.a2 = nn.Linear(100, 10)

            # Global view FC layers
            self.b1 = nn.Linear(2001, 200)
            self.b2 = nn.Linear(200, 10)

            # Combined layers
            self.c1 = nn.Linear(20, 10)
            self.c2 = nn.Linear(10, 1)

        elif view == 'local':
            self.fca1 = nn.Linear(201, 400)
            self.fca2 = nn.Linear(400, 200)
            self.fca3 = nn.Linear(200, 100)
            self.fca4 = nn.Linear(100, 50)
            self.fca5 = nn.Linear(50, 20)
            self.fca6 = nn.Linear(20, 1)

        elif view == 'global':
            self.fcb1 = nn.Linear(2001, 4000)
            self.fcb2 = nn.Linear(4000, 1000)
            self.fcb3 = nn.Linear(1000, 200)
            self.fcb4 = nn.Linear(200, 50)
            self.fcb5 = nn.Linear(50, 20)
            self.fcb6 = nn.Linear(20, 1)

        # Dropout layer
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        '''
        x : data input of size (batch size, 2201)
        '''

        x = x.to(self.device)
        local_data = x[:, :201]
        global_data = x[:, 201:]

        if self.view == "both":
            # Local View
            d1 = torch.relu(self.a1(local_data))
            d2 = torch.relu(self.a2(self.dropout(d1)))

            # Global View
            e1 = torch.relu(self.b1(global_data))
            e2 = torch.relu(self.b2(self.dropout(e1)))

            # Combine Views
            combine = torch.cat((d2, e2), 1)
            g1 = torch.relu(self.c1(combine))

            y = torch.sigmoid(self.c2(g1))

        elif self.view == 'local':
            b1 = torch.relu(self.fca1(local_data))
            b2 = torch.relu(self.fca2(self.dropout(b1)))
            b3 = torch.relu(self.fca3(self.dropout(b2)))
            b4 = torch.relu(self.fca4(self.dropout(b3)))
            b5 = torch.relu(self.fca5(self.dropout(b4)))

            y = torch.sigmoid(self.fca6(b5))

        elif self.view == 'global':
            b1 = torch.relu(self.fcb1(global_data))
            b2 = torch.relu(self.fcb2(self.dropout(b1)))
            b3 = torch.relu(self.fcb3(self.dropout(b2)))
            b4 = torch.relu(self.fcb4(self.dropout(b3)))
            b5 = torch.relu(self.fcb5(self.dropout(b4)))

            y = torch.sigmoid(self.fcb6(b5))

        return y

    def reset(self):
        '''
        Reset parameters if training net more than once
        '''
        self.a1.reset_parameters()
        self.a2.reset_parameters()
        self.b1.reset_parameters()
        self.b2.reset_parameters()
        self.c1.reset_parameters()
        self.c2.reset_parameters()
        self.fca1.reset_parameters()
        self.fca2.reset_parameters()
        self.fca3.reset_parameters()
        self.fca4.reset_parameters()
        self.fca5.reset_parameters()
        self.fca6.reset_parameters()
        self.fcb1.reset_parameters()
        self.fcb2.reset_parameters()
        self.fcb3.reset_parameters()
        self.fcb4.reset_parameters()
        self.fcb5.reset_parameters()
        self.fcb6.reset_parameters()





















