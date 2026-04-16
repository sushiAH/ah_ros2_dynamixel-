"""
dynamixelをros2で扱うためのnode
Dyna messageをsubscribe
service(server client方式)でfeedback dataを返す
外部yamlファイルから各モーターのidをリストで読み取る
それぞれの設定を書き込む
モード値
0 current control(電流制御)
1 vel
3 pos
4 extended pos
"""

import rclpy
from rclpy.node import Node
import math
import numpy as np
import atexit
import time
import threading

#自作ライブラリ
from dyna_interfaces.msg import DynaTarget, DynaFeedback
import os
import sys

target_dir = os.path.abspath("/home/aratahorie/ah_python_libraries")
sys.path.append(target_dir)
from dyna_lib import *


class DynaHandler(Node):

    def __init__(self):
        super().__init__("dyna_handler_node")
        # 立ち上げたdynamixelのidとinstanceを保管するためのdict
        self.id_instance_dict = {}

        #---- Params ----
        self.declare_parameter("port_name", "/dev/ttyUSB0")
        SERIAL_PORT_NAME = self.get_parameter("port_name").value

        self.declare_parameter("motor_ids", [0, 0])
        motor_ids = self.get_parameter("motor_ids").value
        print(motor_ids)

        for id in motor_ids:
            prefix = f'motors.id{id}'

            #パラメータ初期化
            self.declare_parameter(f'{prefix}.operating_mode', 3)
            self.declare_parameter(f'{prefix}.profile_vel', 0)
            self.declare_parameter(f'{prefix}.profile_accel', 0)

            #値を取得
            mode = self.get_parameter(f'{prefix}.operating_mode').value
            profile_vel = self.get_parameter(f'{prefix}.profile_vel').value
            profile_accel = self.get_parameter(f'{prefix}.profile_accel').value

            self.id_instance_dict[id] = dxl_controller(SERIAL_PORT_NAME, id,
                                                       mode)
            self.id_instance_dict[id].write_profile_vel(profile_vel)

            time.sleep(0.01)

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
        #self.dxl_1 = dxl_controller(SERIAL_PORT_NAME, 0, 1)
        #self.dxl_2 = dxl_controller(SERIAL_PORT_NAME, 1, 1)

        self.dyna_feedback_publisher = self.create_publisher(
            DynaFeedback, "/feedback", 10)

        self.subscription_pos
        self.subscription_extpos
        self.subscription_vel

        publish_period = 0.01

        #self.dyna_publish_timer = self.create_timer(publish_period,
        #                                            self.publish_feedback)

        # dynamixel velocity gain
        self.dyna_vel_gain = (0.229 * 2.0 * math.pi) / 60.0

    def dyna_target_pos_callback(self, msg):
        if msg.id not in self.id_instance_dict:
            return

        self.id_instance_dict[msg.id].write_pos(msg.target)

    def dyna_target_extpos_callback(self, msg):
        if msg.id not in self.id_instance_dict:
            return

        self.id_instance_dict[msg.id].write_pos(msg.target)

    def dyna_target_vel_callback(self, msg):
        if msg.id not in self.id_instance_dict:
            return

        self.id_instance_dict[msg.id].write_vel(msg.target)


def main(args=None):
    rclpy.init(args=args)  # rclpyライブラリの初期化

    dyna_handler_node = DynaHandler()
    rclpy.spin(dyna_handler_node)  # ノードをスピンさせる
    dyna_handler_node.destroy_node()  # ノードを停止する
    rclpy.shutdown()


if __name__ == "__main__":
    main()
