# -*- coding: utf-8 -*-
import csv
import numpy as np
import argparse
import logging
import time
from operator import itemgetter
from collections import defaultdict
import networkx as nx
from mapnetwork import *
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


# Main Entry Point
def main(draw):
    """Find the fraudulent payment requests.
    -------------
    draw: True or False to draw top n networks

    read past transaction file, build network
    for transaction requests, if approved, update network
    """

    #
    # PARSE VARS FROM COMMAND LINE
    #

    fname_batch = ""
    fname_stream = ""
    output1 = ""
    output2 = ""
    output3 = ""


    # Get the input and output filenames from the command line
    parser = antifraud_arg_parser()
    args = parser.parse_args()

    if args.outfiles:
        if len(args.outfiles) < 5:
            print "Retry. Need more input"
        else:
            fname_batch = args.outfiles[0]
            fname_stream = args.outfiles[1]
            output1, output2, output3 = args.outfiles[2:]

    else:
        print "Provide some input"


    #
    # NOW BUILD THE RECORD FROM EXISTING CUSTOMERS
    #

    fromto = []        # tuple of (from, to)
    cols = []          # header line
    ds = set()         # user ==> friends
    G = nx.Graph()     # our real hero


    log.debug("Building record from past users data.")
    start = time.clock()
    cols, fromtoBATCH = readFile(fname_batch)
    log.debug("Record built for %s past payments! in %s", len(fromto), time.clock() - start)


    # BUILD RELATIONSHIP MAP

    # Go through the list of tuples containing past transactions
    # make key--> value maps of transaction from each user
    # create a map where key is each user, and value is a set of user's friends
    # If A is a friend of B, then B is a friend of A

    log.debug("Building relationship map ")

    ds = defaultdict(set)     # Could have used a list. Sets for faster lookup
    for k, v in fromtoBATCH[0:500]:
        ds[k].add(v)
        ds[v].add(k)

    G.add_nodes_from(ds.keys())
    G.add_edges_from(fromtoBATCH[0:500])
    log.debug("Done building relationship network!")


    log.info("Sanity check, nodes: %d", nx.number_of_nodes(G) == len(ds))
    log.info("Total records: %s unique users: %s unique nodes: %s", len(fromto), len(ds), nx.number_of_nodes(G))
    # print time.clock() - start



    #
    # GET TRANSACTION REQUESTS
    #
    log.debug("Making features!")

    o1 = open(output1, 'w')
    o2 = open(output2, 'w')
    o3 = open(output3, 'w')
    t1, t2, t3 = 0, 0, 0

    log.debug("Processing Payments...!")
    cols, fromtoSTREAM = readFile(fname_stream)
    n_verified = {1:0, 2:0, 3:0}    # hold no. of unverified users per feature
    counter = 0
    # Check for fraudulent transactions
    for frm, to in fromtoSTREAM[0:500]:

        # If either of the user has no histry of transaction, flag false
        if ((frm not in ds) or (to not in ds)):
            o1.write("unverifed\n")
            o2.write("unverifed\n")
            o3.write("unverifed\n")
            n_verified[1] += 1
            n_verified[2] += 1
            n_verified[3] += 1
        elif (frm == to):
            o1.write("trusted\n")
            o2.write("trusted\n")
            o3.write("trusted\n")
        else:
#            test(G, ds, frm, to)

            #
            # FEATURE ONE
            #
            start1 = time.clock()
            if (frm in ds[to]):
                o1.write("trusted\n")
            else:
                o1.write("unverified\n")
                n_verified[1] += 1

            t1 += time.clock() - start1

            #
            # FEATURE TWO
            #

            start2 = time.clock()
            A_child = ds[frm]
            C_child = ds[to]
            # check for intersection
            if ((frm in ds[to]) | (len(A_child.intersection(C_child)) > 0)):
                o2.write('trusted\n')
            else:
                o2.write('unverified\n')
                n_verified[2] += 1

            t2 += time.clock() - start2

            #
            # FEATURE THREE
            #

            start3 = time.clock()
            shortest_path = -1

            # if both nodes exist
            if (G.has_node(frm) and G.has_node(to)):
                # and path between from, to exists
                try:
                    shortest_path = nx.shortest_path_length(G, frm, to)
                    # and length of shortest path is <=4
                    if(shortest_path >= 0 and shortest_path <= 4):
                        # flag true
                        o3.write('trusted\n')
                        # To update network for trusted transactions
                        G.add_edge(frm, to)
                        ds[frm].add(to)
                        ds[to].add(frm)
                        fromto.append((frm,to))
                    else:
                        # path_length > 4, flag
                        o3.write('unverified\n')
                        n_verified[3] += 1
                except:
                    # nodes exist, but path between them does not
                    o3.write('unverified\n')
                    n_verified[3] += 1
            else:
                # Either of nodes do not exist, in which case flag
                o3.write('unverified\n')
                n_verified[3] += 1

            t3 += time.clock() - start3
            counter += 1

            if (counter % 300000 == 0):
                log.debug("Processed %s payments", counter)

    o1.close()
    o2.close()
    o3.close()

    # Done! SANITY CHECK

    log.debug("Done Processing Payments...!")
    log.info("Sanity check, nodes: %d", nx.number_of_nodes(G) == len(ds))
    log.info("Total records: %s unique users: %s unique nodes: %s", len(fromto), len(ds), nx.number_of_nodes(G))
    log.debug("Avg. time spent on features (1, 2, 3): %s %s %s", t1*1.0 / (counter - n_verified[1]), t2 * 1.0 / (counter - n_verified[2]), t3 * 1.0 / (counter - n_verified[3]))

    #
    # Check functions
    #

    print "Top 5 nodes: ", top_n_users(ds, 5)
    print "#unverifed transactions per feature" , n_verified

    if (draw):
        draw_network(G, ds, 5, level = True)
        #transaction_plot(ds)
    return



if __name__ == "__main__":
    main(draw = False)

# TODO
# Add weights to each edge. 1 deg ~8, 2 deg ~ 4, 3 ~ 2, 4 ~1, >4 ~ 0 ...
# Timestamps, emojis
