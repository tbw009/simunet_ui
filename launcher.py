"""Process launcher for waveform simulations.

This module defines a multiprocessing process that prepares simulation
models, attaches remote clients, and executes waveform computations.
"""

import sys
import time
import multiprocessing as mp
import threading
import numpy as np
from project import Project

from simunetcore import logger
from simunetcore import Waveform
from simunetcore import factory
from simunetcore import aws
from simunetcore import mqtt


class WaveformLauncher(mp.Process):
    """Process class that launches and monitors a waveform simulation."""

    def __init__(self, project, aws_endpoint, mqtt_endpoint, result_dict, stdout=None):
        """Initialize the waveform launcher process."""
        super().__init__()
        self.project = project
        self.result_dict = result_dict
        self.aws_endpoint = aws_endpoint
        self.mqtt_endpoint = mqtt_endpoint
        self.stdout = stdout

    def _simulation_started(self, wf):
        """Callback executed when waveform simulation starts."""
        msg = ("Started waveform '{}' using '{}' base steps.\n"
            "    t_start = {:.3E}\n"
            "    t_end = {:.3E}\n"
            "    frame_length = {:.3E}\n"
            "    min_frame_length = {:.3E}\n"
            "    max_frame_length = {:.3E}\n"
            "    max_iter_frame  = {:.3E}\n"
            "    points_per_frame = {:.3E}\n"
            "    max_iter  = {:.3E}\n"
            "    iter_threshold = {:.3E}\n"
            "    alpha  = {:.3E}\n"
            "    beta  = {:.3E}\n"
            "    epsilon = {:.3E}").format(
            wf.simulation_id, wf.step_type, wf.t_start, wf.t_end, 
            wf.frame_length, wf.min_frame_length, wf.max_frame_length, 
            wf.max_iter_frame, wf.points_per_frame, wf.max_iter, 
            wf.iter_threshold, wf.alpha, wf.beta, wf.epsilon)
        print(msg)

    def _frame_finished(self, wf):
        """Callback executed when a simulation frame finishes."""
        [sim_time, num_frame, frame_state, t_frame_start, 
         t_frame_end, frame_duration, num_iter_frame, 
         frame_error, convergence, model_id, variable] = wf.statistics[-1]
        
        msg = ("{} frame #{:d} from {:.3E}s to {:.3E}s ({:.3E}s) "
               "in {:.3E}s after {:d} iterations (Max error: {:.3E} "
               "| {}.{}).").format(
               frame_state, num_frame, t_frame_start, t_frame_end,  
               t_frame_end-t_frame_start, frame_duration, num_iter_frame, 
               frame_error, self.project.models[model_id]["model"]["name"], 
               variable)
        print(msg)
        
    def _simulation_finished(self, wf):
        """Callback executed when waveform simulation completes."""
        msg = ("Finished in {:.3E}s after {:d} iterations "
               "({:d} overall), {:d} frames converged, {:d} "
               "frames canceled, {:d} frames restarted.").format(
                wf.duration, wf.num_iter_used, wf.num_iter_all, 
                wf.num_converged_frames, wf.num_canceled_frames, 
                wf.num_restarted_frames)
        print(msg)

    def run(self):
        """Execute the waveform simulation in a separate process."""
        if self.stdout:
            sys.stdout = self.stdout
        
        simulation_id = self.project.meta["id"]

        # Return if the model list is empty
        if len(self.project.models) == 0:
           logger.info("Nothing to compute.")
           return

        # Store start time of the function
        start_time = time.time()

        # Load factory
        repository = factory.Factory()

        # Create Model dictionary
        models = {}
        clients = {}
        logger.info( "Creating models and remote clients")
        for model_id in self.project.models:
            # Get model class name and data
            class_name = self.project.models[model_id]["class"]
            model_data = self.project.models[model_id]["model"]
            repo_path = self.project.models[model_id]["path"]

            # Register model
            if class_name not in repository:
                with open("./{}/model.py".format(repo_path)) as f:
                    source = f.read()
                    repository.register(source)

            # Create model from data
            models[model_id] = repository[class_name].from_data(model_data)
            warmup = False
            
            # Create corresponding remote clients, set warmup flag if neccessary
            if class_name == "AWSModel":
                logger.info("Creating AWS client for model '{}'.".format(model_id))
                clients[model_id] = aws.createLambdaClient(self.aws_endpoint)
                models[model_id].endpoint["compress"] = False
                warmup = True
                
            elif class_name == "MQTTModel":
                logger.info("Creating MQTT client for model '{}'.".format(model_id))
                clients[model_id] = mqtt.createMQTTClient(
                    self.mqtt_endpoint, 
                    client_id="model-{}-{}".format(simulation_id, model_id))
                warmup = True
            else:
                clients[model_id] = None

            # Warm up the models
            if warmup:
                task=threading.Thread(
                    target=models[model_id].compute,
                    kwargs={
                        "client": clients[model_id],
                        "simulation_id": simulation_id,
                        "model_id": model_id,
                        "invocation_type": "warmup"
                    })
                task.start()

        # Create Waveform
        wf = Waveform(
            models, 
            self.project.edges, 
            self.project.var_map, 
            simulation_id)
        
        # Attach callbacks
        wf.on_simulation_started = self._simulation_started
        wf.on_frame_finished = self._frame_finished
        wf.on_simulation_finished = self._simulation_finished

        # Create compute kwargs
        for model_id in self.project.models:
            wf.compute_kwargs[model_id]= {
                "client": clients[model_id]
            }

        # Log compute order and cycles
        logger.info("Compute order: {}.".format(list(wf.compute_order())))
        logger.info("Compute cycles: {}.".format(list(wf.compute_cycles())))

        # Store meta data in wf
        wf.tag = self.project.meta
  
        # Set t_start and t_end and create output time frame
        t_start = self.project.simulation["t_start"]
        t_end = self.project.simulation["t_end"]
        numpoints = self.project.simulation["num_points"]

        # Create output timestamps
        t_out = np.linspace(t_start, t_end, numpoints)
        
        # Auto config flag
        auto_config = self.project.simulation["auto_config"]

        try:
            if auto_config:
                wf.compute(\
                    t_start = t_start,
                    t_end   = t_end,
                    t_out   = t_out,
                    verbose = False)
            else:
                wf.compute(\
                    t_start          = t_start,
                    t_end            = t_end,
                    t_out            = t_out,
                    frame_length     = self.project.simulation["frame_length"],
                    min_frame_length = self.project.simulation["min_frame_length"],
                    max_frame_length = self.project.simulation["max_frame_length"],
                    max_iter_frame   = self.project.simulation["max_iter_frame"],
                    max_iter         = self.project.simulation["max_iter"],
                    points_per_frame = self.project.simulation["points_per_frame"],
                    iter_threshold   = self.project.simulation["iter_threshold"], 
                    alpha            = self.project.simulation["alpha"], 
                    beta             = self.project.simulation["beta"], 
                    epsilon          = self.project.simulation["epsilon"],
                    step_type        = self.project.simulation["step_type"],
                    verbose          = False)
            
        except Exception as ex: 
            # Raise exception
            logger.error(ex)          
            raise
        
        finally:
            logger.info("Stopping remote clients.")
            
            # Stop mqtt clients
            for model_id in self.project.models:
                if self.project.models[model_id]["class"] == "MQTTModel":
                    if model_id in clients:
                        clients[model_id].disconnect()
                        logger.info("Disconnected MQTT client for model '{}'.".format(model_id))
            
            # copy results
            result = dict()
            for model_id in self.project.models:
                result[model_id] = wf.models[model_id].__dict__
            
            self.result_dict["result"] = result
            self.result_dict["statistics"] = wf.statistics
            self.result_dict["convergence"] = wf.convergence

            # Log finished event
            logger.info("Finished in {:.3E}s!".format(time.time() - start_time))

if __name__ == '__main__':
    # Create project
    project = Project()
    project.load("./projects/controller_2l.sim")

    # Get multiprocessing manager to create data dict
    manager = mp.Manager()
    result_dict = manager.dict()
    result_dict["result"] = {}
    result_dict["statistics"] = {}
    result_dict["convergence"] = []

    launcher = WaveformLauncher(project, None, None, result_dict)
    launcher.start()
    launcher.join()
