#!/usr/bin/env python3
"""
 Copyright (c) 2018 Intel Corporation.

 Permission is hereby granted, free of charge, to any person obtaining
 a copy of this software and associated documentation files (the
 "Software"), to deal in the Software without restriction, including
 without limitation the rights to use, copy, modify, merge, publish,
 distribute, sublicense, and/or sell copies of the Software, and to
 permit persons to whom the Software is furnished to do so, subject to
 the following conditions:

 The above copyright notice and this permission notice shall be
 included in all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import sys
import logging as log
from openvino.inference_engine import IENetwork, IECore


class Network:
    """
    Load and configure inference plugins for the specified target devices 
    and performs synchronous and asynchronous modes for the specified infer requests.
    """

    def __init__(self):
        self.plugin = None
        self.network = None
        self.input_blob = None
        self.output_blob = None
        self.exec_network = None
        self.infer_request = None

        
    def load_model(self, model, device="CPU", cpu_extension=None):
        # Load Model
        model_xml = model
        model_bin = os.path.splitext(model_xml)[0] + ".bin"

        # Initialize the plugin
        self.plugin = IECore()
        
        # Add a CPU extension, if applicable
        if cpu_extension and "CPU" in device:
            self.plugin.add_extension(cpu_extension, device)
            
        self.network = IENetwork(model=model_xml, weights=model_bin)

        # Check for supported layers
        model_layers = self.network.layers.keys()
        supported_layers = self.plugin.query_network(self.network, 'CPU')

        unsupported_layers = [layer for layer in model_layers if layer not in supported_layers]
        
        # If unsupported layers are found we print them and terminate the program.
        if len(unsupported_layers) != 0:
            print('Unsupported layers found!')

            for lay in unsupported_layers:
                print('*', lay)

            # Abort the script run
            print('Terminating the script ...')
            sys.exit()
        
        # Load the IENetwork into the plugin
        self.exec_network = self.plugin.load_network(self.network, device)

        # Get the input and output layers
        self.input_blob = next(iter(self.network.inputs))
        self.output_blob = next(iter(self.network.outputs))
        
        return self.exec_network

    
    def get_input_shape(self):
        # Get expected shape for being able to run the network
        
        return self.network.inputs[self.input_blob].shape

    def exec_net(self, image):
        # Run the network with the specified image
        
        self.exec_network.start_async(request_id=0, inputs={self.input_blob:image})
        return

    def wait(self):
        # Wait until the last async request is finished

        status = self.exec_network.requests[0].wait(-1)
        return status

    def get_output(self):
        # Get the output of the request
        
        out = self.exec_network.requests[0].outputs[self.output_blob]
        return out