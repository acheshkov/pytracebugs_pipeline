import torch
from torch import nn
from torch.nn import functional as F


class VariationalAutoencoder(nn.Module):
    def __init__(self, input_size, aux_size=400, hidden_size=20):
        super(VariationalAutoencoder, self).__init__()

        self.input_size = input_size

        self.fc1 = nn.Linear(input_size, aux_size)
        self.fc21 = nn.Linear(aux_size, hidden_size)
        self.fc22 = nn.Linear(aux_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, aux_size)
        self.fc4 = nn.Linear(aux_size, input_size)

    def encode(self, x):
        h1 = F.relu(self.fc1(x))
        return self.fc21(h1), self.fc22(h1)

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5*logvar)
        eps = torch.randn_like(std)
        return mu + eps*std

    def decode(self, z):
        h3 = F.relu(self.fc3(z))
        return torch.sigmoid(self.fc4(h3))

    def forward(self, x):
        mu, logvar = self.encode(x.view(-1, self.input_size))
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar

# Reconstruction + KL divergence losses summed over all elements and batch
def loss_function(recon_x, x, mu, logvar):
    #BCE = F.binary_cross_entropy(recon_x, x.view(-1, input_size), reduction='sum')
    #BCE = F.binary_cross_entropy(recon_x, x, reduction='sum')
    MSE = F.mse_loss(recon_x, x, reduction='sum')

    # see Appendix B from VAE paper:
    # Kingma and Welling. Auto-Encoding Variational Bayes. ICLR, 2014
    # https://arxiv.org/abs/1312.6114
    # 0.5 * sum(1 + log(sigma^2) - mu^2 - sigma^2)
    KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())

    #return BCE + KLD
    return MSE + KLD
