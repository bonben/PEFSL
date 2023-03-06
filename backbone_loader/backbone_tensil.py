

import sys
import os
import json
import numpy as np

file_dir = os.path.dirname(__file__)
print(file_dir)

sys.path.append(file_dir+"/tensil/drivers/")
from tensil.drivers.tcu_pynq.driver import Driver
from tensil.drivers.tcu_pynq.architecture import Architecture
from tensil.drivers.tcu_pynq.data_type import DataType

class backbone_tensil_wrapper:

    def __init__(self,overlay,path_tarch,path_tmodel,debug=False):
        """
        Args :
            - path_bit : path qui mêne au bitstream, e.g : home/xilinx/bitstream.bit
            - path_tarch : path qui mène au tarch, e.g : home/xilinx/model.tarch
            - path_tmodel : path qui mène aui tmodel, e.g : home/xilinx/model.tmodel
        """
        print(f"dma 0 : {overlay.axi_dma_0}")

        if not hasattr(overlay, 'axi_dma_0'):
            raise RuntimeError("DMA was not found in overlay")
        with open(path_tarch) as f:
            js=json.load(f)
            js["data_type"]=DataType[js["data_type"]]
            self.tarch=Architecture(**js)
            
        self.tcu = Driver(self.tarch, overlay.axi_dma_0,debug=debug)
        print("tcu succefullt loaded")
        self.tcu.load_model(path_tmodel)

    def __call__(self,img):
        assert img.shape[0]==1
        assert len(img.shape)==4
        assert img.shape[-1]==3

        img=img[0]
        c,h,w=img.shape

        
        #img=np.transpose(img.reshape((c, h, w)), axes=[1, 2, 0])
        img=np.pad(img, [(0, 0), (0, 0), (0, self.tcu.arch.array_size - 3)], 'constant', constant_values=0)
        img=img.reshape((-1, self.tcu.arch.array_size))

        inputs = {'input.1': img}
        outputs = self.tcu.run(inputs)
        
        return outputs['Output'][None,:]
    