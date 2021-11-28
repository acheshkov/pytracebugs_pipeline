import torch
from torch import nn
from torch.nn import functional as F


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


class VAESimplex(nn.Module):
    def __init__(self, input_size, aux_size=400, hidden_size=20):
        super(VAESimplex, self).__init__()

        self.input_size = input_size

        self.fc1  = nn.Linear(self.input_size, aux_size)
        self.fc21 = nn.Linear(aux_size, hidden_size)
        self.fc22 = nn.Linear(aux_size, hidden_size)
        self.fc3  = nn.Linear(hidden_size, aux_size)
        self.fc4  = nn.Linear(aux_size, input_size)

    def encode(self, x):
        h1 = F.relu(self.fc1(x))
        return self.fc21(h1), self.fc22(h1)

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5*logvar)
        if self.training:
            eps = torch.randn_like(std)
        else:
            eps = torch.zeros_like(std)
        return mu + eps*std

    def decode(self, z):
        h3 = F.relu(self.fc3(z))
        return torch.sigmoid(self.fc4(h3))

    def forward(self, x):
        mu, logvar = self.encode(x.view(-1, self.input_size))
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar


class VAEMultiplex(nn.Module):
    def __init__(self, input_shape):
        super(VAEMultiplex, self).__init__()

        self.input_shape = input_shape
        hei, wid = self.input_shape

        self.conv1 = nn.Conv2d(in_channels=1, out_channels=2, kernel_size=(hei//2+1, wid//2+1))
        self.conv2 = nn.Conv2d(in_channels=2, out_channels=4, kernel_size=(hei//4+1, wid//4+1))
        self.fc31  = nn.Linear((hei*wid)//4, 1024)
        self.fc32  = nn.Linear((hei*wid)//4, 1024)
        self.fc4   = nn.Linear(1024, (hei*wid)//4)
        self.up5   = nn.ConvTranspose2d(4, 4, 2, 2)
        self.up6   = nn.ConvTranspose2d(4, 1, 2, 2)

    def encode(self, x):
        h1 = F.relu(self.conv1(x))
        h2 = F.relu(self.conv2(h1))
        f2 = torch.flatten(h2, start_dim=1)
        h31 = self.fc31(f2)
        h32 = self.fc32(f2)
        return h31, h32 

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5*logvar)
        eps = torch.randn_like(std)
        return mu + eps*std

    def decode(self, z):
        f4 = F.relu(self.fc4(z))
        hei, wid = self.input_shape
        h4 = torch.reshape(f4, (f4.shape[0], 4, hei//4, wid//4))
        h5 = F.relu(self.up5(h4))
        h6 = F.relu(self.up6(h5))
        return torch.sigmoid(h6)

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar
