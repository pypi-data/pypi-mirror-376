from ast import literal_eval
import inspect
import os
from pathlib import Path

import jax.numpy as jnp
import yaml

from fiesta.logging import logger
from fiesta.inference.prior_dict import ConstrainedPrior
import fiesta.inference.prior as fiesta_prior


ALL_PRIORS = dict(inspect.getmembers(fiesta_prior, inspect.isclass))

########################################
# SYSTEMATIC UNCERTAINTY SETUP METHODS #
########################################

def setup_systematics_basic(likelihood, prior: ConstrainedPrior, error_budget: float = 0.3):

    # enable one variable sys. uncertainty parameter
    if "sys_err" in prior.naming:
        likelihood._setup_sys_uncertainty_free()
        logger.info(f"Likelihood is using a collective freely sampled systematic uncertainty as specified in the prior.")
    # fix systematic uncertainty to set value
    else:
        likelihood._setup_sys_uncertainty_fixed(error_budget=error_budget)
        logger.info(f"Likelihood is using a collective fixed systematic uncertainty {error_budget}.")
    
    return likelihood, prior
    
def setup_systematic_from_file(likelihood, prior: ConstrainedPrior, systematics_file: str):
    # read systematic uncertainty setup from file
    if not os.path.exists(systematics_file):
        raise OSError(f"Provided systematics file {systematics_file} could not be found.")
    sys_params_per_filter, time_nodes_per_filter, additional_priors = process_file(systematics_file, likelihood.filters)
    
    # setup the likelihood
    likelihood._setup_sys_uncertainty_from_file(sys_params_per_filter, time_nodes_per_filter)
    logger.info(f"Likelihood is using systematic uncertainty sampling as specified in {systematics_file}.")
    
    # setup the prior
    if not isinstance(prior, ConstrainedPrior):
        prior = ConstrainedPrior(prior.priors)
    prior_list = prior.priors
    if "sys_err" in prior.naming:
        logger.warning(f"When providing a systematics_file, 'sys_err' should not be listed in the prior. Removing 'sys_err' from prior list.")
        index = [ind for ind, p in enumerate(prior_list) if 'sys_err' in p.naming]
        prior_list.pop(index[0])
    prior_list.extend(prior.constraints)
    prior_list.extend(additional_priors)
    prior = ConstrainedPrior(priors=prior_list, conversion_function=prior.conversion)
    logger.info(f"Prior is now updated to sample systematic uncertainty parameters {[sys_prior.naming[0] for sys_prior in additional_priors]}.")
    
    return likelihood, prior


def process_file(systematic_file, filters):
    
    yaml_dict = yaml.safe_load(Path(systematic_file).read_text())
    additional_priors = []
    sys_params_per_filter = {}
    time_nodes_per_filter = {}

    if "collective" in yaml_dict.keys():
        if len(yaml_dict.keys())>1:
            raise ValueError(f"'collective' sys. uncertainty can only be specified if no other sys. uncertainty setup is given in {systematic_file}.")
        
        nodes, t_range, sys_prior_type, sys_prior_params = fetch_prior_params(yaml_dict["collective"])
        
        sys_parameters = []

        for j in range(1, nodes+1):
            naming = f"syserr_collective_{j}"
            sys_parameters.append(naming)
            
            sys_prior = ALL_PRIORS[sys_prior_type](**sys_prior_params, naming=[naming])
            additional_priors.append(sys_prior)

        for filt in filters:
            sys_params_per_filter[filt] = sys_parameters
            time_nodes_per_filter[filt] = t_range
    
    elif "individual" in yaml_dict.keys():
        if len(yaml_dict.keys())>1:
            raise ValueError(f"'individual' sys. uncertainty for each filter can only be specified if no other sys. uncertainty setup is given in {systematic_file}.")
        
        nodes, t_range, sys_prior_type, sys_prior_params = fetch_prior_params(yaml_dict["individual"])
        
        sys_parameters = []

        for filt in filters:

            for j in range(1, nodes+1):
                naming = f"syserr_{filt}_{j}"
                sys_parameters.append(naming)
                
                sys_prior = ALL_PRIORS[sys_prior_type](**sys_prior_params, naming=[naming])
                additional_priors.append(sys_prior)
        
            sys_params_per_filter[filt] = sys_parameters
            time_nodes_per_filter[filt] = t_range
    
    else:
        yaml_dict = check_filter_compatability(yaml_dict, filters)
        for key in yaml_dict.keys():
            nodes, t_range, sys_prior_type, sys_prior_params = fetch_prior_params(yaml_dict[key])
            
            sys_parameters = []
            for j in range(1, nodes+1):
                naming = f"syserr_{key}_{j}"
                sys_parameters.append(naming)
                
                sys_prior = ALL_PRIORS[sys_prior_type](**sys_prior_params, naming=[naming])
                additional_priors.append(sys_prior)
            
            for filt in yaml_dict[key]["filters"]:
                sys_params_per_filter[filt] = sys_parameters
                time_nodes_per_filter[filt] = t_range
   
    return sys_params_per_filter, time_nodes_per_filter, additional_priors


def check_filter_compatability(yaml_dict, filters):

    filters_checked = list(filters)
    for key in yaml_dict.keys():
        if key=="remaining":
            continue

        ill_specified_filters = set(yaml_dict[key]["filters"]) - set(filters)

        if ill_specified_filters:
            logger.warning(f"Filters {ill_specified_filters} in systematics file are not part of the lightcurve data. Removing them from the sys. error group {key}.")
            for ill_filter in ill_specified_filters:
                yaml_dict[key]["filters"].remove(ill_filter)
        
        for filt in yaml_dict[key]["filters"]:
            filters_checked.remove(filt)
    
    if not filters_checked:
        try:
            del yaml_dict["remaining"]
        except KeyError:
            pass
    
    else:
        if "remaining" not in yaml_dict.keys():
            raise KeyError(f"Sys error groups in systematic file do not include the following filters {filters_checked}. Set up a 'remaining' group to include those.")
        yaml_dict["remaining"]["filters"] = filters_checked
    
    return yaml_dict

def fetch_prior_params(yaml_entry: dict):

    nodes = yaml_entry["time_nodes"]
    t_range = yaml_entry.get("time_range", None)    

    if t_range is not None:

        type, t0, t1 = t_range.split(" ")

        if type == "log":
            t_range = jnp.geomspace(float(t0), float(t1), nodes)
        elif type == "linear":
            t_range = jnp.linspace(float(t0), float(t1), nodes)
        else:
            raise ValueError(f"Range specified in systematics file must either be 'linear' or 'log', not {type}.")


    sys_prior_type = yaml_entry["prior"]
    if sys_prior_type not in ALL_PRIORS:
        raise ValueError(f"Prior type specified in systematic file not implemented in  fiesta.inference.prior. Allowed priors are {ALL_PRIORS}.")
    sys_prior_params = yaml_entry["params"]
    return nodes, t_range, sys_prior_type, sys_prior_params