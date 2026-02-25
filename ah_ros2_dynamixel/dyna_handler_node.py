"""
dynamixelをros2で扱うためのnode
Dyna messageをsubscribe
service(server client方式)でfeedback dataを返す
"""

import rclpy
from rclpy.node import Node
import math
import numpy as np
import atexit

#自作ライブラリ
from dyna_interfaces.msg import DynaTarget, DynaFeedback
import os
import sys

target_dir = os.path.abspath("/home/aratahorie/ah_python_libraries")
sys.path.append(target_dir)
from dyna_lib import *

SERIAL_PORT_NAME = "/dev/ttyUSB2"


class DynaHandler(Node):

    def __init__(self):
        super().__init__("dyna_handler")

        self.declare_parameter("port_name", "/dev/ttyUSB0")
        SERIAL_PORT_NAME = self.get_parameter("port_name").value

        self.subscription_pos = self.create_subscription(
            DynaTarget,  # メッセージの型
            "/dyna_target_pos",  # 購読するトピック名
            self.dyna_target_pos_callback,  # 呼び出すコールバック関数
            10,
        )

        self.subscription_extpos = self.create_subscription(
            DynaTarget,  # メッセージの型
            "/dyna_target_extpos",  # 購読するトピック名
            self.dyna_target_extpos_callback,  # 呼び出すコールバック関数
            10,
        )

        self.subscription_vel = self.create_subscription(
            DynaTarget,  # メッセージの型
            "/dyna_target_vel",  # 購読するトピック名
            self.dyna_target_vel_callback,  # 呼び出すコールバック関数
            10,
        )

        #一定feedback用に立ち上げ
        self.dxl_1 = dxl_controller(SERIAL_PORT_NAME, 0, 1)
        self.dxl_2 = dxl_controller(SERIAL_PORT_NAME, 1, 1)

        self.dyna_feedback_publisher = self.create_publisher(
            DynaFeedback, "/feedback", 10)

        self.subscription_pos
        self.subscription_extpos
        self.subscription_vel

        # 立ち上げたdynamixelのidとinstanceを保管するためのdict
        self.id_instance_dict = {}

        publish_period = 0.01
        self.dyna_publish_timer = self.create_timer(publish_period,
                                                    self.publish_feedback)

        # dynamixel velocity gain
        self.dyna_vel_gain = (0.229 * 2.0 * math.pi) / 60.0

    def dyna_target_pos_callback(self, msg):
        pos_mode_num = 3

        if msg.id not in self.id_instance_dict:
            # instanceの立ち上げ
            self.id_instance_dict[msg.id] = dxl_controller(
                SERIAL_PORT_NAME, msg.id, pos_mode_num)

        self.id_instance_dict[msg.id].write_pos(msg.target)

    def dyna_target_extpos_callback(self, msg):
        extpos_mode_num = 4

        if msg.id not in self.id_instance_dict:
            # instanceの立ち上げ
            self.id_instance_dict[msg.id] = dxl_controller(
                SERIAL_PORT_NAME, msg.id, extpos_mode_num)

        self.id_instance_dict[msg.id].write_pos(msg.target)

    def dyna_target_vel_callback(self, msg):
        vel_mode_num = 1

        if msg.id not in self.id_instance_dict:
            # instanceの立ち上げ
            self.id_instance_dict[msg.id] = dxl_controller(
                SERIAL_PORT_NAME, msg.id, vel_mode_num)

        self.id_instance_dict[msg.id].write_vel(msg.target)

    def publish_feedback(self):
        """一定間隔で、dynamixelからのfeedback_dataを受取、publishする"""
        V_r = np.int32(self.dxl_1.read_vel()) * self.dyna_vel_gain  # rps
        V_l = -(np.int32(self.dxl_2.read_vel()) * self.dyna_vel_gain)

        feedback_data = DynaFeedback()

        feedback_data.data[0] = V_r
        feedback_data.data[1] = V_l

        self.dyna_feedback_publisher.publish(feedback_data)


def main(args=None):
    rclpy.init(args=args)  # rclpyライブラリの初期化

    dyna_handler_node = DynaHandler()
    rclpy.spin(dyna_handler_node)  # ノードをスピンさせる
    dyna_handler_node.destroy_node()  # ノードを停止する
    rclpy.shutdown()


if __name__ == "__main__":
    main()
