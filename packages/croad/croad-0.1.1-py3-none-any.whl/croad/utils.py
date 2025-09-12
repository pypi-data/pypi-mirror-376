import time
import numpy as np
import pymap3d as pm
from pathlib import Path
from numpy import ndarray
from rosbags.highlevel import AnyReader
import autonomous_proto
from rosbags.rosbag2 import Writer
from rosbags.typesys import Stores, get_typestore
from rosbags.typesys.stores.ros2_humble import (
    std_msgs__msg__UInt8MultiArray as UInt8MultiArray,
    std_msgs__msg__MultiArrayLayout as MultiArrayLayout,
    std_msgs__msg__MultiArrayDimension as MultiArrayDimension,
)

def read_bag_nav_llh_humble(bag_path: Path):
    llh_list = []
    timestamps = []
    with AnyReader([bag_path]) as reader:
        connections = [c for c in reader.connections if 'navigation' in c.topic]
        for connection, timestamp, rawdata in reader.messages(connections=connections):
            msg = reader.deserialize(rawdata, connection.msgtype)
            if hasattr(msg, 'data'):
                nav = autonomous_proto.Navigation.FromString(bytes(msg.data))
                llh_list.append((nav.position.lat, nav.position.lon, nav.position.alt))
                timestamps.append(timestamp)
    return llh_list, timestamps

def llh_to_enu(
        llh_list : list[tuple[float, float, float]],
        llh_origin: tuple[float, float, float] = None,
):
    if len(llh_list) == 0:
        return []
    if llh_origin is None:
        llh_origin = llh_list[0]
    return [
        pm.geodetic2enu(llh_origin[0], llh_origin[1], llh_origin[2], llh[0], llh[1], llh[2])
        for llh in llh_list
    ]

def save_nav_points_to_bag(
        points: ndarray,
        origin_llh: tuple[float, float, float],
):
    if len(points) == 0:
        return
    nav = autonomous_proto.Navigation()
    nav.header.info.count = 0
    nav.header.info.module_name = autonomous_proto.MessageInfoModuleNameValue.undefined
    nav.header.info.topic_name = autonomous_proto.MessageInfoTopicNameValue.undefined

    with Writer(Path('croad_' + time.strftime("%Y_%m_%d_%H_%M_%S")), version=8) as writer:
        type_store = get_typestore(Stores.ROS2_HUMBLE)
        topic = 'navigation'
        msg_type = UInt8MultiArray.__msgtype__
        connection = writer.add_connection(topic, msg_type, typestore=type_store)
        timestamp = int(time.time() * 1e9)
        for p in points:
            lat, lon, alt = pm.enu2geodetic(p[0], p[1], 0, origin_llh[0], origin_llh[1], origin_llh[2])
            nav.position.lat = lat
            nav.position.lon = lon
            nav.position.alt = alt
            timestamp += 20000000
            data = np.frombuffer(nav.SerializeToString(), dtype=np.uint8)
            dims = [MultiArrayDimension(label='', size=data.size, stride=1)]
            layout = MultiArrayLayout(dim=dims, data_offset=0)
            message = UInt8MultiArray(layout=layout, data=data)
            writer.write(connection, timestamp, type_store.serialize_cdr(message, msg_type))
