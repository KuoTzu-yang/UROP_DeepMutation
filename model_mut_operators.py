import tensorflow as tf
import numpy as np
import keras

import math, random

import utils

class ModelMutationOperators():
    def __init__(self):
        self.utils = utils.GeneralUtils()
        self.check = utils.ExaminationalUtils()
        self.model_utils = utils.ModelUtils()
        self.LD_mut_candidates = ['Dense']
        self.LAm_mut_candidates = ['Dense']

    def GF_on_list(self, lst, mutation_ratio, STD):
        copy_lst = lst.copy()
        number_of_data = len(copy_lst)
        number_of_GF_weights = math.floor(number_of_data * mutation_ratio)
        permutation =  np.random.permutation(number_of_data)
        permutation = permutation[:number_of_GF_weights]

        for val in permutation:
            copy_lst[val] += (np.random.normal() * STD)

        return copy_lst

    def WS_on_list(self, lst, output_index):
        copy_lst = lst.copy()
        input_dim, output_dim = copy_lst.shape

        grabbed_lst = np.empty((input_dim), copy_lst.dtype)

        for index in range(input_dim):
            grabbed_lst[index] = copy_lst[index][output_index]
        shuffle_grabbed_lst = self.utils.shuffle(grabbed_lst)
        for index in range(input_dim):
            copy_lst[index][output_index] = shuffle_grabbed_lst[index]

        return copy_lst

    def NAI_on_list(self, lst, output_index):
        lst = lst.copy()
        input_dim, output_dim = lst.shape

        for index in range(input_dim):
            lst[index][output_index] *= -1

        return lst

    def NS_copy_lst_column(self, a, b, a_index, b_index):
        b = b.copy()
        assert a.shape == b.shape
        input_dim, output_dim = a.shape
        for col_index in range(input_dim):
            b[col_index][b_index] = a[col_index][a_index]

        return b

    def NS_on_list(self, lst, mutation_ratio):
        lst = lst.copy()
        copy_lst = lst.copy()
        shuffled_neurons = np.empty(lst.shape, dtype=lst.dtype)
        # calculate the amount of neurons need to be shuffled 
        input_dim, output_dim = lst.shape
        number_of_switch_neurons = math.floor(output_dim * mutation_ratio)
        # produce permutation for shuffling 
        permutation = np.random.permutation(output_dim)
        permutation = permutation[:number_of_switch_neurons]
        shuffled_permutation = self.utils.shuffle(permutation)

        # shuffle neurons 
        for index in range(len(permutation)):
            copy_lst = self.NS_copy_lst_column(lst, copy_lst, permutation[index], shuffled_permutation[index])

        return copy_lst 

    def LD_model_scan(self, model):
        index_of_suitable_layers = []
        layers = [l for l in model.layers]
        for index, layer in enumerate(layers):
            layer_name = type(layer).__name__
            is_in_candidates = layer_name in self.LD_mut_candidates
            has_same_input_output_shape = layer.input.shape.as_list() == layer.output.shape.as_list()
            should_be_removed = is_in_candidates and has_same_input_output_shape

            if index == 0 or index == (len(model.layers) - 1):
                continue

            if should_be_removed:
                index_of_suitable_layers.append(index)

        return index_of_suitable_layers

    def LAm_model_scan(self, model):
        index_of_suitable_spots = []
        layers = [l for l in model.layers]
        for index, layer in enumerate(layers):
            layer_type_name = type(layer).__name__
            is_in_candidates = layer_type_name in self.LAm_mut_candidates
            has_same_input_output_shape = layer.input.shape.as_list() == layer.output.shape.as_list()
            should_be_added = is_in_candidates and has_same_input_output_shape
            if should_be_added:
                index_of_suitable_spots.append(index)

        return index_of_suitable_spots

    def AFRm_model_scan(self, model):
        index_of_suitable_spots = []
        layers = [l for l in model.layers]
        for index, layer in enumerate(layers):
            if index == (len(model.layers) - 1):
                continue

            try:
                if layer.activation is not None:
                    index_of_suitable_spots.append(index)
            except:
                pass

        return index_of_suitable_spots
        


    # This function is designed for debugging purpose, 
    # detecting whether mutation operator truely modeifies the weights of given model 
    def diff_count(self, lst, mutated_lst):
        diff_count = 0
        for index in range(len(lst)):
            if mutated_lst[index] != lst[index]:
                diff_count += 1
        return diff_count

    # STD stands for standard deviation 
    def GF_mut(self, model, mutation_ratio, STD=0.1):
        GF_model = self.model_utils.model_copy(model, 'GF')
        self.check.mutation_ratio_range_check(mutation_ratio)  

        layers = [l for l in GF_model.layers]
        for index, layer in enumerate(layers):
            weights = layer.get_weights()
            new_weights = []
            if not (len(weights) == 0):
                for val in weights:
                    val_shape = val.shape
                    flat_val = val.flatten()
                    GF_flat_val = self.GF_on_list(flat_val, mutation_ratio, STD)
                    GF_val = GF_flat_val.reshape(val_shape)
                    new_weights.append(GF_val)

                layer.set_weights(new_weights) 

        return GF_model

    def WS_mut(self, model, mutation_ratio):
        WS_model = self.model_utils.model_copy(model, 'WS')
        self.check.mutation_ratio_range_check(mutation_ratio)

        layers = [l for l in WS_model.layers]
        for index, layer in enumerate(layers):
            weights = layer.get_weights()
            new_weights = []
            if not (len(weights) == 0):
                for val in weights:
                    val_shape = val.shape
                    if len(val.shape) == 2:
                        input_dim, output_dim = val_shape
                        number_of_WS_neurons = math.floor(output_dim * mutation_ratio)
                        permutation =  np.random.permutation(output_dim)
                        permutation = permutation[:number_of_WS_neurons]
                        for output_dim_index in permutation:
                            val = self.WS_on_list(val, output_dim_index)
                    new_weights.append(val)

                layer.set_weights(new_weights)

        return WS_model

    def NEB_mut(self, model, mutation_ratio):
        NEB_model = self.model_utils.model_copy(model, 'NEB')
        self.check.mutation_ratio_range_check(mutation_ratio)

        layers = [l for l in NEB_model.layers]
        for index, layer in enumerate(layers):
            weights = layer.get_weights()
            new_weights = []
            if not (len(weights) == 0):
                for val in weights:
                    val_shape = val.shape
                    if len(val.shape) == 2:
                        input_dim, output_dim = val_shape
                        number_of_NEB_neurons = math.floor(input_dim * mutation_ratio)
                        permutation = np.random.permutation(input_dim)
                        permutation = permutation[:number_of_NEB_neurons]
                        for input_index in permutation:
                            val[input_index] = 0 
                    new_weights.append(val)

                layer.set_weights(new_weights)

        return NEB_model

    def NAI_mut(self, model, mutation_ratio):
        NAI_model = self.model_utils.model_copy(model, 'NAI')
        self.check.mutation_ratio_range_check(mutation_ratio)

        layers = [l for l in NAI_model.layers]
        for index, layer in enumerate(layers):
            weights = layer.get_weights()
            new_weights = []
            if not (len(weights) == 0):
                for val in weights:
                    val_shape = val.shape
                    if len(val.shape) == 2:
                        input_dim, output_dim = val_shape
                        number_of_NAI_neurons = math.floor(output_dim * mutation_ratio)
                        permutation = np.random.permutation(output_dim)
                        permutation = permutation[:number_of_NAI_neurons]
                        for output_dim_index in permutation:
                            val = self.NAI_on_list(val, output_dim_index)
                    new_weights.append(val)

                layer.set_weights(new_weights)

        return NAI_model


    def NS_mut(self, model, mutation_ratio):
        NS_model = self.model_utils.model_copy(model, 'NS')
        self.check.mutation_ratio_range_check(mutation_ratio)

        layers = [l for l in NS_model.layers]
        for index, layer in enumerate(layers):
            weights = layer.get_weights()
            new_weights = []
            if not (len(weights) == 0):
                for val in weights:
                    val_shape = val.shape
                    if len(val.shape) == 2:
                        val = self.NS_on_list(val, mutation_ratio)
                    new_weights.append(val)
                layer.set_weights(new_weights)

        return NS_model

    def LD_mut(self, model):
        LD_model = self.model_utils.model_copy(model, 'LD')

        # Randomly select from suitable layers instead of the first one 
        index_of_suitable_layers = self.LD_model_scan(model)
        number_of_suitable_layers = len(index_of_suitable_layers)
        if number_of_suitable_layers == 0:
            print('None of layers be removed')
            print('LD will only remove the layer with the same input and output')
            return LD_model

        random_picked_layer_index = index_of_suitable_layers[random.randint(0, number_of_suitable_layers-1)]

        new_model = keras.models.Sequential()
        layers = [l for l in LD_model.layers]
        new_model = keras.models.Sequential()
        for index, layer in enumerate(layers):
            if index == random_picked_layer_index:
                continue
            new_model.add(layer)

        return new_model

    def LAm_mut(self, model):
        LAm_model = self.model_utils.model_copy(model, 'LAm')
        copied_LAm_model = self.model_utils.model_copy(model, 'insert')

        # Randomly select from suitable spots instead of the first one 
        index_of_suitable_spots = self.LAm_model_scan(model)
        number_of_suitable_spots = len(index_of_suitable_spots)
        if number_of_suitable_spots == 0:
            print('No layers be added')
            print('LAm will only add the layer with the same input and output')
            print('There is no suitable spot for the input model')
            return LAm_model

        random_picked_spot_index = index_of_suitable_spots[random.randint(0, number_of_suitable_spots-1)]

        new_model = keras.models.Sequential()
        layers = [l for l in LAm_model.layers]
        copy_layers = [l for l in copied_LAm_model.layers]
        for index, layer in enumerate(layers):
            if index == random_picked_spot_index:
                new_model.add(layer)
                # remember to load weights to the newly added layer
                copy_layer = copy_layers[index]
                new_model.add(copy_layer)
                continue
            new_model.add(layer)

        return new_model

    def AFRm_mut(self, model):
        AFRm_model = self.model_utils.model_copy(model, 'AFRm')

        # Randomly select from suitable layers instead of the first one 
        index_of_suitable_layers = self.AFRm_model_scan(model)
        number_of_suitable_layers = len(index_of_suitable_layers)
        if number_of_suitable_layers == 0:
            print('No activation be removed')
            print('Except the output layer, there is no activation function can be removed')
            return AFRm_model

        random_picked_layer_index = index_of_suitable_layers[random.randint(0, number_of_suitable_layers-1)]

        new_model = keras.models.Sequential()
        layers = [l for l in AFRm_model.layers]
        for index, layer in enumerate(layers):

            if index == random_picked_layer_index:
                layer.activation = lambda x: x
                new_model.add(layer)
                continue

            new_model.add(layer)

        return new_model