import numpy as np
import glob
import ast
import ntpath
import pickle
import configparser
import logging, sys

from collections import Counter

'''
****************************************
************** PARAMETERS **************
****************************************
'''

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

config = configparser.ConfigParser()
config.read('config.ini')

# random

np.random.seed(int(config['random']['seed']))

# images

IMAGES_PATH = config['images']['path']
LABELS = ast.literal_eval(config['images']['labels'])

# dataset

DATASET_PATH = config['dataset']['path']
PARTITION_PREFIX = config['dataset']['partition_prefix']
LABELS_PREFIX = config['dataset']['labels_prefix']
UNIFORM = ast.literal_eval(config['dataset']['uniform'])
INTERACTION_TYPES = ast.literal_eval(config['dataset']['interaction_types'])

if(INTERACTION_TYPES):

    # Interaction types (from 0 to 13 (12))

    N_LABELS = len(Counter(LABELS.values()))

else:

    # Neutrino types (from 0 to 3)

    DELIMITED_LABELS = ast.literal_eval(config['images']['delimited_labels'])
    N_LABELS = len(Counter(DELIMITED_LABELS.values()))

# train

TRAIN_FRACTION = float(config['train']['fraction'])

# validation

VALIDATION_FRACTION = float(config['validation']['fraction'])

# test

TEST_FRACTION = float(config['test']['fraction'])

if((TRAIN_FRACTION + VALIDATION_FRACTION + TEST_FRACTION) > 1):
    logging.error('(TRAIN_FRACTION + VALIDATION_FRACTION + TEST_FRACTION) must be <= 1')
    exit(-1)

'''
****************************************
*************** DATASETS ***************
****************************************
'''

partition = {'train' : [], 'validation' : [], 'test' : []} # Train, validation, and test IDs
labels = {}                                                # ID : label

if UNIFORM:

    # calculate uniform constants

    logging.info('Calculating uniform constants...')

    COUNTS = np.zeros(N_LABELS, dtype=int)
    MIN_DIR = [float("inf"), '']

    for path in glob.iglob(IMAGES_PATH + '/*'):

        label = ntpath.basename(path) # label
        label_dir = glob.iglob(path + '/*')
        len_dir = float(len(list(label_dir)))

        if INTERACTION_TYPES:

            # Interaction types (from 0 to 12 (13))

            COUNTS[LABELS[label]] += 1

            if len_dir < MIN_DIR[0]:

                MIN_DIR[0] = len_dir
                MIN_DIR[1] = label

        else:

            # Neutrino types: from 0 to 3

            COUNTS[DELIMITED_LABELS[label]] += 1

            if len_dir < MIN_DIR[0]:

                MIN_DIR[0] = len_dir
                MIN_DIR[1] = label

# Iterate through label folders

logging.info('Filling datasets...')

for path in glob.iglob(IMAGES_PATH + '/*'):

    logging.debug('path: %s', path)

    label = ntpath.basename(path) # label
    label_dir = glob.iglob(path + '/*')

    if UNIFORM:

        # Calculate fraction

        if INTERACTION_TYPES:

            # Interaction types (from 0 to 13 (12))

            fraction = (MIN_DIR[0]) * (COUNTS[LABELS[MIN_DIR[1]]] / COUNTS[LABELS[label]]) / len(list(label_dir))

        else:

            # Neutrino types (from 0 to 3)

            fraction = (MIN_DIR[0]) * (COUNTS[DELIMITED_LABELS[MIN_DIR[1]]] / COUNTS[DELIMITED_LABELS[label]]) / len(list(label_dir))

        logging.debug('fraction: %f', fraction)  
 
    count = 0
    label_dir = glob.iglob(path + '/*')
 
    # Iterate through the files under the directory

    for fil in label_dir:

        if UNIFORM:

            # only use a uniform subset

            random_value = np.random.uniform(0,1)

            if(random_value >= fraction):
                continue

        ID = fil[:-7].split('/')[-1]  # it is basically the filename without '.txt.gz'

        random_value = np.random.uniform(0,1)

        # Fill training set

        if(random_value < TRAIN_FRACTION):
            partition['train'].append(ID)
            count += 1

        # Fill validation set

        elif(random_value < (TRAIN_FRACTION + VALIDATION_FRACTION)):
            partition['validation'].append(ID)
            count += 1

        # Fill test set

        elif(random_value < (TRAIN_FRACTION + VALIDATION_FRACTION + TEST_FRACTION)):
            partition['test'].append(ID)
            count += 1

        labels[ID] = label

    logging.debug('%d images', count)

# Print dataset statistics

logging.info('Number of training examples: %d', len(partition['train']))
logging.info('Number of validation examples: %d', len(partition['validation']))
logging.info('Number of test examples: %d', len(partition['test']))

# Serialize partition and labels

logging.info('Serializing datasets...')

partition_file = open(DATASET_PATH + PARTITION_PREFIX + '.p', 'w')
pickle.dump(partition, partition_file)
partition_file.close()

labels_file = open(DATASET_PATH + LABELS_PREFIX + '.p', 'w')
pickle.dump(labels, labels_file)
labels_file.close()

