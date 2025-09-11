"""Method to train the surrogate models"""

import dill
import os
import pickle
from typing import Callable, Dict

import numpy as np
import matplotlib.pyplot as plt

import jax
from jaxtyping import Array, Float, Int

from fiesta.filters import Filter
from fiesta.train.DataManager import DataManager
from fiesta.scalers import MinMaxScalerJax
import fiesta.train.neuralnets as fiesta_nn
from fiesta.logging import logger

################
# TRAINING API #
################

class LightcurveTrainer:
    """Abstract class for training a collection of surrogate models per filter"""
   
    name: str
    outdir: str
    filters: list[Filter]
    parameter_names: list[str]

    train_X: Float[Array, "n_train"]
    train_y: Dict[str, Float[Array, "n"]]
    val_X: Float[Array, "n_val"]
    val_y: Dict[str, Float[Array, "n"]]
    
    def __init__(self, 
                 name: str,
                 outdir: str,
                 plots_dir: str = None,
                 save_preprocessed_data: bool = False) -> None:
        
        self.name = name
        # Check if directories exists, otherwise, create:
        self.outdir = outdir
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
        self.plots_dir = plots_dir
        if self.plots_dir is not None and not os.path.exists(self.plots_dir):
            os.makedirs(self.plots_dir)

        self.save_preprocessed_data = save_preprocessed_data

        # To be loaded by child classes
        self.filters = None
        self.parameter_names = None
        
        self.train_X = None
        self.train_y = None

        self.val_X = None
        self.val_y = None

    def __repr__(self) -> str:
        return f"LightcurveTrainer(name={self.name})"
    
    def preprocess(self):
        
        logger.info("Preprocessing data by minmax scaling . . .")
        self.X_scaler = MinMaxScalerJax()
        self.X = self.X_scaler.fit_transform(self.X_raw)
        
        self.y_scaler: dict[str, MinMaxScalerJax] = {}
        self.y = {}
        for filt in self.filters:
            y_scaler = MinMaxScalerJax()
            self.y[filt.name] = y_scaler.fit_transform(self.y_raw[filt.name])
            self.y_scaler[filt.name] = y_scaler
        logger.info("Preprocessing data . . . done")
    
    def fit(self,
            config: fiesta_nn.NeuralnetConfig,
            key: jax.random.PRNGKey = jax.random.PRNGKey(0),
            verbose: bool = True) -> None:
        """
        The config controls which architecture is built and therefore should not be specified here.
        
        Args:
            config (nn.NeuralnetConfig, optional): _description_. Defaults to None.
        """
        
        self.preprocess()
        if self.save_preprocessed_data:
            self._save_preprocessed_data()


        self.config = config
        self.models = {}
        input_ndim = len(self.parameter_names)

        for filt in self.filters:
            logger.info("\n \n")
            logger.info(f"Training {filt.name}...")
            logger.info(f"----------------------------------\n")
            
            # Create neural network and initialize the state
            net = fiesta_nn.MLP(config = config, input_ndim = input_ndim, key = key)

            # Perform training loop
            state, train_losses, val_losses = net.train_loop(self.train_X, self.train_y[filt.name], self.val_X, self.val_y[filt.name], verbose=verbose)
            self.models[filt.name] = net
    
            # Plot and save the plot if so desired
            if self.plots_dir is not None:
                plt.figure(figsize=(10, 5))
                ls = "-o"
                ms = 3
                plt.plot([i+1 for i in range(len(train_losses))], train_losses, ls, markersize=ms, label="Train", color="red")
                plt.plot([i+1 for i in range(len(val_losses))], val_losses, ls, markersize=ms, label="Validation", color="blue")
                plt.legend()
                plt.xlabel("Epoch")
                plt.ylabel("MSE loss")
                plt.yscale('log')
                plt.title("Learning curves")
                plt.savefig(os.path.join(self.plots_dir, f"learning_curves_{filt.name}.png"))
                plt.close()
    
    def plot_example_lc(self, lc_model):
        _, _, X, y = self.data_manager.load_raw_data_from_file(0,1) # loads validation data
        y = y.reshape(len(self.data_manager.nus), len(self.data_manager.times))
        mJys_val = np.exp(y)
        params = dict(zip(self.parameter_names, X.flatten() ))
        _, mag_predict = lc_model.predict_abs_mag(params)
        mag_val = {Filt.name: Filt.get_mag(mJys_val, self.data_manager.nus) for Filt in lc_model.Filters}

        for filt in lc_model.Filters:
    
            plt.plot(lc_model.times, mag_val[filt.name], color = "red", label="Base model")
            plt.plot(lc_model.times, mag_predict[filt.name], color = "blue", label="Surrogate prediction")
            upper_bound = mag_predict[filt.name] + 1
            lower_bound = mag_predict[filt.name] - 1
            plt.fill_between(lc_model.times, lower_bound, upper_bound, color='blue', alpha=0.2)
        
            plt.ylabel(f"mag for {filt.name}")
            plt.xlabel("$t$ in days")
            plt.legend()
            plt.gca().invert_yaxis()
            plt.xscale('log')
            plt.xlim(lc_model.times[0], lc_model.times[-1])

            if self.plots_dir is None:
                self.plots_dir = "."
            plt.savefig(os.path.join(self.plots_dir, f"{self.name}_{filt.name}_example.png"))
            plt.close()
        
    def save(self):
        """
        Save the trained model and all the used metadata to the outdir.
        """
        # Save the metadata
        meta_filename = os.path.join(self.outdir, f"{self.name}_metadata.pkl")

        save = {}

        save["times"] = self.times
        save["parameter_names"] = self.parameter_names
        save["parameter_distributions"] = self.parameter_distributions
        save["X_scaler"] = self.X_scaler
        save["y_scaler"] = self.y_scaler

        save["model_type"] = "MLP"

        with open(meta_filename, "wb") as meta_file:
            dill.dump(save, meta_file)
        
        # Save the NN
        for filt in self.filters:
            model = self.models[filt.name]
            model.save_model(outfile = os.path.join(self.outdir, f"{self.name}_{filt.name}.pkl"))
                
    def _save_preprocessed_data(self) -> None:
        logger.info("Saving preprocessed data . . .")
        np.savez(os.path.join(self.outdir, f"{self.name}_preprocessed_data.npz"), train_X=self.train_X, train_y = self.train_y, val_X = self.val_X, val_y = self.val_y)
        logger.info("Saving preprocessed data . . . done")
    
class SVDTrainer(LightcurveTrainer):
    
    def __init__(self,
                 name: str,
                 outdir: str,
                 filters: list[str],
                 data_manager_args: dict,
                 svd_ncoeff: Int = 50,
                 conversion: str = None,
                 plots_dir: str = None,
                 save_preprocessed_data: bool = False) -> None:
        """
        Initialize the surrogate model trainer that decomposes the training data into its SVD coefficients. The initialization also takes care of reading data and preprocessing it, but does not automatically fit the model. Users may want to inspect the data before fitting the model.
        
        Args:
            name (str): Name of the surrogate model. Will be used 
            outdir (str): Directory where the trained surrogate model is to be saved.
            filters (list[str]): List of the filters for which the surrogate has to be trained. These have to be either bandpasses from sncosmo or specifiy the frequency through endign with GHz or keV.
            data_manager_args (dict): data_manager_args (dict): Arguments for the DataManager class instance that will be used to read the data from the .h5 file in outdir and preprocess it.
            svd_ncoeff (int, optional) : Number of SVD coefficients to use in data reduction during training. Defaults to 50.
            conversion (str): references how to convert the parameters for the training. Defaults to None, in which case it's the identity.
            plots_dir (str, optional): Directory where the plots of the training process will be saved. Defaults to None, which means no plots will be generated.
            save_preprocessed_data (bool, optional): If True, the preprocessed data (reduced, rescaled) will be saved in the outdir. Defaults to False.
        """

        super().__init__(name = name,
                         outdir = outdir,
                         plots_dir = plots_dir,
                         save_preprocessed_data = save_preprocessed_data)
        
        self.svd_ncoeff = svd_ncoeff

        self.conversion = conversion
        
        self.data_manager = DataManager(**data_manager_args)
        self.data_manager.print_file_info()
        self.data_manager.pass_meta_data(self)
        self.load_filters(filters)
    
    def load_filters(self, filters):
        self.filters = []
        for filt in filters:
            Filt = Filter(filt)
            if Filt.nus[0] < self.data_manager.nus[0] or Filt.nus[-1] > self.data_manager.nus[-1]:
                raise ValueError(f"Filter {filt} exceeds the frequency range of the training data.")
            self.filters.append(Filt)
        
    def preprocess(self):
        """
        Preprocessing method to get the SVD coefficients of the training and validation data. This includes scaling the inputs and outputs, as well as performing SVD decomposition.
        """
        logger.info(f"Preprocessing data by decomposing training data into SVD coefficients.")
        self.train_X, self.train_y, self.val_X, self.val_y, self.X_scaler, self.y_scaler = self.data_manager.preprocess_svd(self.svd_ncoeff, self.filters, self.conversion)
        self.parameter_names += ["redshift"]
        self.parameter_distributions = self.parameter_distributions[:-1] + ", 'redshift': (0, 0.5, 'uniform')}" # TODO make adding redshift more flexible (i.e. whether to add redshift at all and its range)
        
        nan_filters = []
        for key in self.train_y.keys():
            if np.any(np.isnan(self.train_y[key])) or np.any(np.isnan(self.val_y[key])):
                logger.warning(f"Data preprocessing for {key} introduced nans. Check raw data for nans of infs or vanishing variance in a specific entry. Removing {key} from training.")
                nan_filters.append(key)

        self.filters = [filt for filt in self.filters if filt.name not in nan_filters]
        for key in nan_filters:
                del self.train_y[key]
                del self.val_y[key]
                del self.y_scaler[key]
        logger.info(f"Preprocessing data . . . done")
