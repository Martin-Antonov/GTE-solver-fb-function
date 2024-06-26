from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os 
from fractions import Fraction
import string
import argparse 
import subprocess
import io

def process_lrs_output(string_input = None, fpath = 'tmp/out'):
    """
    create:
        - text output of equilibria in decimal and fractional format
        - input for clique_enumeration
    """

    global store
    store = {}

    if string_input is not None:
        # string_input takes precedence
        buf = io.StringIO(string_input)
    else: 
        # read from fpath
        buf = open(fpath, 'r')

    # x is an dictionary with integer line numbers as keys (so indexing from 1)
    x, i = {}, 1
    for line in buf.readlines():
        x[i] = line.split()
        i+=1

    buf.close()

    ######################################################
    # Number of extreme equilibria
    ######################################################
    # changed with use of lrsnash to i-5
    numberOfEq = int(x[i-5][4])

    store['number_of_extreme_eq'] = numberOfEq

    # store mixed strategies as arrays of string probabilities 
    e1, e2 = {}, {}

    # store payoffs 
    p1, p2 = {}, {}

    ######################################################
    # DICTIONARIES for mixed strategies 
    ######################################################
    # Mixed strategies strings as keys (e.g. '1/2,1/4,1/4')
    # Indices as values
    dict1, dict2 = {}, {}

    # store indices for mixed strategies for input to clique algorithm
    index1, index2 = {}, {}
    # next index for input to clique algorithm
    c1, c2 = 1, 1

    eq = -1 # index of current equilibrium (shared by e1,e2,p1,p2,index1,index2) 

    count = 0 # how many equilibria of II to match with one

    # first line of out with a vertex (counting from 1 as used in range)
    first_line = 2

    # deal with follwing possible, dodgy lrs output (lrslib-062) for 3rd line, like
    # *Input linearity in row 3 is redundant--skipped2  0  1/2  1/2  0  1
    # which results in an x[3] like
    # ['*Input', 'linearity', 'in', 'row', '3', 'is', 'redundant--skipped2', '0', '1/2', '1/2', '0', '1']
    # Note that there should be a new line after skipped, in which case the fix would be cleaner

    if x[first_line+1][0] == "*Input":
        del x[3][0:6]
        x[3][0] = x[3][0].replace('redundant--skipped','')

    for j in range(first_line,len(x)-5):

        if not x[j]:
            count = 0 # reset count, ready for next set of II's strategies
            continue
        elif x[j][0] == "2": 
            processII = True
            count += 1 # one more of II's strategies to pair with I's
            eq += 1
        elif x[j][0] == "1": 
            processII = False
        else:
            print("skipping line: %s", x[j])
            continue

        l = len(x[j])
        ##########################################
        # Player II
        ##########################################
        if processII : # loop through all mixed strategies of II
            e2[eq] = x[j][1:l-1]
            p1[eq] = x[j][l-1] # payoffs swapped in lrs output

            e2string = ','.join(e2[eq])

            if e2string not in dict2.keys():
                dict2[e2string] = c2
                c2 += 1
            index2[eq] = dict2[e2string] 
        else:
            #################################################
            # Player I
            #################################################
            # Now match all these count-many strategies of II 
            # with # subsequent strategy of I

            e1[eq] = x[j][1:l-1]
            p2[eq] = x[j][l-1] # payoffs swapped in lrs output

            e1string = ','.join(e1[eq])

            if e1string not in dict1.values():
                dict1[e1string] = c1
                c1 += 1
            index1[eq] = dict1[e1string] 

            for i in range(1,count):
                e1[eq-i] = e1[eq] 
                p2[eq-i] = p2[eq]
                index1[eq-i] = index1[eq] 

    rat = [] # list to contain list of strings (for pretty printing)
    dec = [] # list to contain list of string (for pretty printing)

    for i in range(numberOfEq):
        # convert probability strings to fractions to floats to strings

        e1decstr = ['{0:F}'.format(float(Fraction(s))) for s in e1[i]]
        e2decstr = ['{0:F}'.format(float(Fraction(s))) for s in e2[i]]

        # initialize empty rows
        rat.append([])
        dec.append([])
        #
        rat[i].append("EE")
        dec[i].append("EE")
        # EE index
        rat[i].append(str(i+1))
        dec[i].append(str(i+1))
        #
        rat[i].append("P1:")
        dec[i].append("P1:")
        # PI strategy index (for connected components)
        rat[i].append("("+str(index1[i])+")")
        dec[i].append("("+str(index1[i])+")")
        # PI strategy probabilities
        for entry in e1[i]:
            rat[i].append(entry)
        for entry in e1decstr:
            dec[i].append(entry)
        rat[i].append("EP=")
        dec[i].append("EP=")
        # PI payoff
        rat[i].append(str(p1[i]))
        dec[i].append(str(float(Fraction(str(p1[i])))))
        #
        rat[i].append("P2:")
        dec[i].append("P2:")
        # PII strategy index (for connected components)
        rat[i].append("("+str(index2[i])+")")
        dec[i].append("("+str(index2[i])+")")
        # PII strategy probabilities
        for entry in e2[i]:
            rat[i].append(entry)
        for entry in e2decstr:
            dec[i].append(entry)
        rat[i].append("EP=")
        dec[i].append("EP=")
        # PII payoff
        rat[i].append(str(p2[i]))
        dec[i].append(str(float(Fraction(str(p2[i])))))

    store['decimal_output'] = dec
    store['rational_output'] = rat

    return store, index1, index2


def clique_enumeration(numberOfEq, index1, index2):

    assert numberOfEq == len(index1) == len(index2)

    # open clique enumeration input file
    fcin = open(os.path.join(os.getcwd(),'solver/input/clique_input.txt'), 'w')
    # print indices to clique enumeration input file 
    for i in range(numberOfEq):
        fcin.write("{0} {1}\n".format(index1[i],index2[i]))
    # close file
    fcin.close()
    # do clique enumeration
    os.system(os.path.join(os.getcwd(),'solver/bin/clique') +
              " <" + os.path.join(os.getcwd(),"solver/input/clique_input.txt") +
              " >" + os.path.join(os.getcwd(),"solver/input/clique_output.txt"))
    # open clique enumeration output file
    fcout = open(os.path.join(os.getcwd(), 'solver/input/clique_output.txt'), 'r')
    clique_output = fcout.read()
    #############################################################
    return clique_output


def print_output(store):
    result = ""
    result += "%d x %d payoff matrix A:\n" % (store["nrow"], store["ncol"])
    result += pretty_print(store['m1'])
    result += "\n\n"
    result += "%d x %d payoff matrix B:\n" % (store["nrow"], store["ncol"])
    result += pretty_print(store['m2'])
    result += "\n\n"
    result += "EE = Extreme Equilibrium, EP = Expected Payoff\n"
    result += "Decimal Output\n"
    result += pretty_print(store['decimal_output'])
    result += "\n\n"
    result += "Rational Output\n"
    result += pretty_print(store['rational_output'])
    result += "\n"
    result += store['clique_output']
    return result


def pretty_print (my_matrix):
    """
    pretty printing of a 2d matrix so that columns are justified
    requires input to really be a matrix (dimension 2), not just a list
    """

    # create list of max lengths in each column
    max_lens = [max([len(str(r[i])) for r in my_matrix])
                            for i in range(len(my_matrix[0]))]

    result = "\n".join(["".join([str(e).rjust(l + 2)
                        for e, l in zip(r, max_lens)]) for r in my_matrix])
    return result


def parse_input_game(fpath):
    """
    takes a path to an input file for lrsnash

    returns nrow, ncol, m1, m2

    where m1 and m2 are both lists of lists representing the payoff matrices
    """

    f = open(fpath, 'r')

    # list of individual lines
    lines = f.readlines()

    # drop any blank lines
    lines = [l for l in lines if l != '\n']

    # extract the dimensions
    try:
        nrow, ncol = [int(e) for e in lines[0].split()]
    except:
        print("First row of input file should be the number of rows, a space, and then the number of columns")

    # get rid of first row of input
    lines = lines[1:]

    # check that the number of lines is correct
    assert len(lines) == 2*nrow, "nrow = %d, so expected %d rows in the matrics, but got %d" % (nrow,2*nrow,len(lines))

    m1 = lines[0:nrow]
    m2 = lines[nrow:]

    m1 = [r.split() for r in m1]
    m2 = [r.split() for r in m2]

    return nrow, ncol, m1, m2


# if __name__ == "__main__":
def execute():
    parser = argparse.ArgumentParser(description='Bimatrix Solver')
    # choices = ['ex1', '75_eq', 'rock_paper_scissors']
    # choices = [input_path]
    # choices = [os.path.join('example_input',c + '.txt') for c in choices]
    #
    # parser.add_argument('--input_path', '-i',
    #                     default=choices[0],
    #                     help='Path to game input text file, examples: %s' % " ".join(choices))
    #
    # parser.add_argument('--store_lrs_output', '-o', action='store_true',
    #                     help='Store intermediate lrs output file')
    #
    # args = parser.parse_args()
    args = os.path.join(os.getcwd(), 'solver/input/game_to_solve.txt')
    # assert os.path.isfile(args), "%s is not a file" % args

    nrow, ncol, m1, m2 = parse_input_game(args)

    result = subprocess.check_output([os.path.join(os.getcwd(), 'solver/bin/lrsnash'), args])
    result_string = result.decode('utf-8')
    # print(result_string)

    # if args.store_lrs_output:
    #     text_file = open("tmp/out", "w")
    #     text_file.write(result_string)
    #     text_file.close()

    store, index1, index2 = process_lrs_output(result_string)
    store['ncol'] = ncol
    store['nrow'] = nrow
    store['m1'] = m1
    store['m2'] = m2
    store['clique_output'] = clique_enumeration(store['number_of_extreme_eq'], index1, index2)

    # print in original "banach.lse.ac.uk" format
    result = print_output(store)
    
    # save dictionary to a yaml file
    # TODO: tidy up contents of dictionary (e.g. strings to numbers)
    # with open('tmp/out.yaml', 'w') as outfile:
    #     yaml.safe_dump(store, outfile)

    return result
