# This contains some helper functions for the antifraud.py

import csv
import numpy as np
import argparse
import logging
import time
from operator import itemgetter
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt

#
# HELPER FUNCTIONS
#


def antifraud_arg_parser():
    """
    Parse input arguments
    -------------
    """

    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description='PayMO Antifraud at Digital Wallet')
    parser.add_argument('outfiles', metavar='f', type=str, nargs='+',
                        help='input and output files')
    return parser



def readFile(fname):
    """
    Load files for transaction
    -------------
    Parameters:
    fname: filename
    """

    fromto = []
    cols = []
    with open(fname , 'r') as f:
        cols = f.readline().split(",")[0:4]     # Headline
        for line in f:
            tm, frm, to, am = line.split(",")[0:4]
            frm = int(frm.lstrip())
            to = int(to.lstrip())
            fromto.append((frm,to))
    return cols, fromto


def feature_one(ds, tup):
    """FEATURE 1
    transaction is allowed if the degree of separation, d == 1

    Let's say we have customer A wanting to pay Customer B
    In feature 1, we ask if the user A is a friend of B or viceversa
    Friends: someone who a user had transactions before


    >>>

    """
    #            try:
    #                if (nx.shortest_path_length(G, frm, to) == 1):
    #                    o1.write("trusted\n")
    #                else:
    #                    o1.write("unverified\n")
    #            except:
    #                o1.write("unverified\n")

    return tup[0] in ds[tup[1]]


def feature_two(ds, tup):
    """ FEATURE 2
    Transaction is allowed if the degree of separation, d <= 2
    -------------
    Parameters:
    ds: a map with user --> first_degree friends
    tup: a tuple with (from, to)

    """
    #            try:
    #                if (nx.shortest_path_length(G, frm, to) == 2):
    #                    o2.write("trusted\n")
    #                else:
    #                    o2.write("unverified\n")
    #            except:
    #                o2.write("unverified\n")

    A_child = ds[tup[0]]
    C_child = ds[tup[1]]
    return ((len(A_child.intersection(C_child)) > 0) | (tup[0] in ds[tup[1]]))



def feature_three(graph, tup):
    """ FEATURE 3
    transaction is allowed if the degree of separation, d <=4
    -------------
    Parameters:
    graph: a newtworkx graph object
    tup: a tuple with (from, to)

    >>>

    """
    shortest_path = find_shortest_path(graph, tup[0], tup[1])
    return len(shortest_path) <= 4


def find_shortest_path(graph, start, end, path=[]):
    """ Finds the shortest path between nodes within a graph
    https://www.python.org/doc/essays/graphs/
    -------------
    Parameters:
    graph : map with key, val
    start : starting node
    end : end node
    >>>
    """
    path = path + [start]
    if start == end:
        return path
    if not graph.has_key(start):
        return None
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    return shortest



# Who is the most valuable node?
# Who are the top ten nodes with max number of first degree connection,
# n-degree connection?
# number of common friends between user A, user B


def common_friends(ds, tup):
    """ Find common friends among two users
    return intersection of two sets
    -------------
    Parameters:
    ds : map with key, val pairs where val is an iterable.
    n : top n users with large 1st degree friend count, ascending

    """
    A_child = ds[tup[0]]
    B_child = ds[tup[1]]
    return A_child.intersection(B_child)


def top_n_users(ds, n):
    """ Find the most valuable nodes in terms of transactions
    For each node, find the lenth of value set

    returns tuple of top n users with their corresponding 1-deg. friend count
    -------------
    Parameters:
    ds : map with key, val pairs where val is an iterable.
    n : top n users with large 1st degree friend count, ascending

    """
    out = []
    for key, val in ds.iteritems():
        out.append((key, len(val)))
    out = sorted(out, key=itemgetter(1), reverse=True)
    return out[0:n]


def draw_network(G, ds, n = 5, label = False):
    """ Draw network graph with top n nodes
    -------------
    Parameters:

    G: NetworkX graph
    ds : map with key as G's nodes, val pairs where val as edges.
    n: number of top users
    labels: True or False. Adds text label to each node
    """

    top_n = top_n_users(ds,5)
    top_n = [int(i[0]) for i in top_n]
    H = G.subgraph(top_n)
    for m in top_n:
        child = ds[m]
        for item in child:
            H.add_edge(m,item)

    print "Drawing figure..."

    fig = plt.figure()
    nx.draw(H,pos=nx.spring_layout(H), node_size = 1, alpha = 0.25,
            width = 0.25, with_labels = label)
    fig.suptitle('Top 5 nodes by 1st degree connection', fontsize=20)
#    plt.savefig("images/TopN.png", format="PNG")
    plt.show()



def test_cout(G, ds, frm, to):
    """ STDOUT with elements for few test items
    """
    print "Common friends among ", "(", frm, ",", to, ")", common_friends(ds, (frm,to))
    try:
        print "shortest_path, len: ", nx.shortest_path(G, frm, to), nx.shortest_path_length(G, frm, to)
    except:
        print "No node warning!"



def transaction_plot(ds):
    """ Make some plots with transaction data
    -------------
    Parameters:
    ds : map with key, val pairs where val is an iterable.

    """
    import seaborn as sns
    import pandas as pd
    df = pd.DataFrame()
#    for key, val in ds.iteritems():
#        df[key] = len(val)
#    plt.show()
