
import numpy as np

packet_cnt = 0
start_time = 0



def set_cmd_cb(resp):
    print('Command result: {}'.format(resp))

rms_formuula = lambda x: np.sqrt(np.mean(x ** 2, axis=1))
