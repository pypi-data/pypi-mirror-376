import threading

from common.utills.time import current_time
from common.utills.enums import IDType
from otium_user_management_server.settings import (
    DATACENTER_ID,
    SERVER_ID,
)



class IDGenerator:
    def __init__(
            self,
            id_type: IDType,
            data_center_id=0,
            server_id=0,
            epoch=1732088762000,
    ):
        self.id_type = id_type.value
        self.data_center_id = int(data_center_id)
        self.server_id = int(server_id)
        self.epoch = epoch

        self.sequence = 0
        self.last_time_stamp = -1
        self.lock = threading.Lock()

        self.data_center_id_bits = 1
        self.server_id_bits = 3
        self.id_type_bits = 7
        self.sequence_bits = 12

        self.max_data_center_id = -1 ^ (-1 << self.data_center_id_bits)
        self.max_server_id = -1 ^ (-1 << self.server_id_bits)
        self.max_id_type = -1 ^ (-1 << self.id_type_bits)
        self.max_sequence = -1 ^ (-1 << self.sequence_bits)

        self.id_type_shift = self.sequence_bits
        self.server_id_shift = self.id_type_shift + self.id_type_bits
        self.data_center_id_shift = self.server_id_shift + self.server_id_bits
        self.time_stamp_shift = self.data_center_id_shift + self.data_center_id_bits

    def _id_generate(self):
        with self.lock:
            time_stamp = current_time()

            if time_stamp < self.last_time_stamp:
                raise Exception(f"Time Error current time : {time_stamp} last time stamp : {self.last_time_stamp}")

            if time_stamp == self.last_time_stamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                if self.sequence == 0:
                    while time_stamp <= self.last_time_stamp:
                        time_stamp = current_time()
            else:
                self.sequence = 0

            self.last_time_stamp = time_stamp

            _id = ((time_stamp - self.epoch) << self.time_stamp_shift) | \
                  (self.data_center_id << self.data_center_id_shift) | \
                  (self.server_id << self.server_id_shift) | \
                  (self.id_type << self.id_type_shift) | \
                  self.sequence

            return _id

    def id_generate_str(self):
        return str(self._id_generate())


_instances: dict[IDType, IDGenerator] = {}
_instance_lock = threading.Lock()
def generate_id(id_type_enum: IDType):
    global _instances, _instance_lock
    instance_key = id_type_enum
    
    with _instance_lock:
        if instance_key not in _instances:
            try:
                data_center_id = DATACENTER_ID
                server_id = SERVER_ID
            except AttributeError as e:
                raise AttributeError("Missing data_center_id, server_id") from e
        
            _instances[instance_key] = IDGenerator(id_type_enum, data_center_id, server_id)
        generate_instance = _instances[instance_key]
    return generate_instance._id_generate()