import torch
import torch.nn as nn


class Autoencoder(nn.Module):
    def __init__(self, input_size, hidden_size):
        super().__init__()
        self.encoder_hidden_layer = nn.Linear(in_features= input_size, out_features=hidden_size)
        self.encoder_output_layer = nn.Linear(in_features=hidden_size, out_features=hidden_size)
        
        self.decoder_hidden_layer = nn.Linear(in_features=hidden_size, out_features=hidden_size)
        self.decoder_output_layer = nn.Linear(in_features=hidden_size, out_features= input_size)

    def forward(self, features):
        activation = self.encoder_hidden_layer(features)
        activation = torch.relu(activation)

        code = self.encoder_output_layer(activation)
        code = torch.relu(code)

        activation = self.decoder_hidden_layer(code)
        activation = torch.relu(activation)
        activation = self.decoder_output_layer(activation)
        reconstructed = torch.relu(activation)

        return reconstructed
