import torch
import torch.nn as nn

import dgl
from dgl.nn import SumPooling

import matplotlib.pyplot as plt
from networks.src.ISAT import ISATconvolution
from networks.src.Linear import Linears

class network(nn.Module):
    def __init__(self, config):
        super(network, self).__init__()

        hidden_dim = config.get('hidden_dim', 64)
        gcn_layers = config.get('conv_layers', 4)
        dropout = config.get('dropout', 0.1)
        linear_layers = config.get('linear_layers', 4)
        target_dim = config['target_dim']

        self.embedding_rnode_lin = nn.Sequential(
            nn.Linear(config['node_dim'], hidden_dim, bias=False)
        )
        self.embedding_inode_lin = nn.Sequential(
            nn.Linear(1, hidden_dim, bias=False)
        )
        self.embedding_edge_lin = nn.Sequential(
            nn.Linear(config['edge_dim'], hidden_dim, bias=False)
        )
        self.ISATconv = ISATconvolution(hidden_dim, hidden_dim, hidden_dim, nn.LeakyReLU(), gcn_layers,dropout, False, True, 0.1)
        
        self.linears = Linears(hidden_dim, target_dim, nn.ReLU(), linear_layers, dropout, False, False, last=True)
        self.reduce = SumPooling()
    
    def forward(self, **kargs):
        graph =  kargs['Smiles_graphs']
        r_node = kargs['Smiles_r_node']
        i_node = kargs['Smiles_i_node']
        r_edge = kargs['Smiles_r2r_edge']
        d_edge = kargs['Smiles_d2d_edge']

        graph_elu1 =  kargs['elu1_smiles_graphs']
        r_node_elu1 = kargs['elu1_smiles_r_node']
        i_node_elu1 = kargs['elu1_smiles_i_node']
        r_edge_elu1 = kargs['elu1_smiles_r2r_edge']
        d_edge_elu1 = kargs['elu1_smiles_d2d_edge']

        graph_elu2 =  kargs['elu2_smiles_graphs']
        r_node_elu2 = kargs['elu2_smiles_r_node']
        i_node_elu2 = kargs['elu2_smiles_i_node']
        r_edge_elu2 = kargs['elu2_smiles_r2r_edge']
        d_edge_elu2 = kargs['elu2_smiles_d2d_edge']

        ratio1 = kargs.get('ratio1_var', 0.5)
        ratio2 = kargs.get('ratio2_var', 0.5)

        r_node = r_node.float()
        r_node = self.embedding_rnode_lin(r_node)
        i_node = i_node.float()
        i_node = self.embedding_inode_lin(i_node)
        r_edge = r_edge.float()
        r_edge = self.embedding_edge_lin(r_edge)
        
        real_graph=graph.node_type_subgraph(['r_nd'])
        real_graph.set_batch_num_nodes(graph.batch_num_nodes('r_nd'))
        real_graph.set_batch_num_edges(graph.batch_num_edges('r2r'))
        
        r_node, score = self.ISATconv(graph, r_node, r_edge, i_node, d_edge)
        
        h = self.reduce(real_graph, r_node)
        if kargs.get('get_feature',False):
            return {'feature':h}
        h = self.linears(h)

        if kargs.get('get_score',False):
            return {'prediction':h, 'positive':score}

        return h
        
    def loss_fn(self, scores, targets):
        return nn.MSELoss()(targets[~torch.isnan(targets)],scores[~torch.isnan(targets)])
