"""
dynamixelをros2で扱うためのnode
一括送信式
"""

import rclpy
from rclpy.node import Node
import math
import numpy as np
import atexit

#自作ライブラリ
from my_robot_interfaces.msg import DynaTarget
import os
import sys

target_dir = os.path.abspath("/home/aratahorie/ah_python_libraries")
sys.path.append(target_dir)
from dyna_lib import *

SERIAL_PORT_NAME = "/dev/ttyUSB1"


class DynaHandler(Node):

    def __init__(self):
        super().__init__("dyna_handler")
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

        self.subscription_pos
        self.subscription_extpos
        self.subscription_vel

        # 立ち上げたdynamixelのidとinstanceを保管するためのdict
        self.id_instance_dict = {}

        self.dt = 0.1
        self.timer = self.create_timer(self.dt, self.sync_write_loop)

    def dyna_target_pos_callback(self, msg):
        pos_mode_num = 3

        if msg.id not in self.id_instance_dict:
            # instanceの立ち上げ
            self.id_instance_dict[msg.id] = dxl_controller(
                SERIAL_PORT_NAME, msg.id, pos_mode_num)

    def dyna_target_extpos_callback(self, msg):
        extpos_mode_num = 4

        if msg.id not in self.id_instance_dict:
            # instanceの立ち上げ
            self.id_instance_dict[msg.id] = dxl_controller(
                SERIAL_PORT_NAME, msg.id, extpos_mode_num)

    def dyna_target_vel_callback(self, msg):
        vel_mode_num = 1

        if msg.id not in self.id_instance_dict:
            # instanceの立ち上げ
            self.id_instance_dict[msg.id] = dxl_controller(
                SERIAL_PORT_NAME, msg.id, vel_mode_num)

    def sync_write_loop(self):

        self.group_write.clearParam()


def main():
    rclpy.init()  # rclpyライブラリの初期化

    dyna_handler_node = DynaHandler()
    rclpy.spin(dyna_handler_node)  # ノードをスピンさせる
