import rclpy
from rclpy.node import Node
import math
import os
import sys
import threading
import time

# 自作メッセージ型のインポート（環境に合わせて調整してください）
from dyna_interfaces.msg import DynaTarget, DynaFeedback

# 自作ライブラリのパス設定
target_dir = os.path.abspath("/home/aratahorie/ah_python_libraries")
if target_dir not in sys.path:
    sys.path.append(target_dir)

# dxl_controller クラスが定義されているファイルをインポート
from dyna_lib import dxl_controller


class DynaHandler(Node):

    def __init__(self):
        super().__init__("dyna_handler_node")

        # モーターIDとインスタンスの管理
        self.id_instance_dict = {}

        # 指令値のバッファ（最新値を保持）
        self.pos_buffer = {}
        self.vel_buffer = {}

        # ---- Parameters ----
        self.declare_parameter("port_name", "/dev/ttyUSB0")
        serial_port = self.get_parameter("port_name").value

        self.declare_parameter("motor_ids", [1, 2])  # デフォルト値
        motor_ids = self.get_parameter("motor_ids").value
        self.get_logger().info(
            f"Initializing motors: {motor_ids} on {serial_port}")

        # 各モーターの初期化
        for dxl_id in motor_ids:
            prefix = f'motors.id{dxl_id}'
            self.declare_parameter(f'{prefix}.operating_mode', 3)
            self.declare_parameter(f'{prefix}.profile_vel', 200)
            self.declare_parameter(f'{prefix}.profile_accel', 50)

            mode = self.get_parameter(f'{prefix}.operating_mode').value
            p_vel = self.get_parameter(f'{prefix}.profile_vel').value
            p_accel = self.get_parameter(f'{prefix}.profile_accel').value

            # インスタンス生成（内部でTorque ON / Mode設定が行われる）
            self.id_instance_dict[dxl_id] = dxl_controller(
                serial_port, dxl_id, mode)
            self.id_instance_dict[dxl_id].write_profile_vel(p_vel)
            self.id_instance_dict[dxl_id].write_profile_accel(p_accel)
            time.sleep(0.01)

        # ---- Subscriptions ----
        # 各モードのトピックを購読し、バッファに保存する
        self.create_subscription(DynaTarget, "/dyna_target_pos", self.pos_cb,
                                 10)
        self.create_subscription(DynaTarget, "/dyna_target_extpos", self.pos_cb,
                                 10)
        self.create_subscription(DynaTarget, "/dyna_target_vel", self.vel_cb,
                                 10)

        # ---- Publisher ----
        #self.feedback_pub = self.create_publisher(DynaFeedback, "/feedback", 10)

        # ---- Timers ----
        # 1. 一括送信タイマー (10ms = 100Hz)
        self.create_timer(0.01, self.sync_write_timer_callback)

        # 2. フィードバック取得タイマー (20ms = 50Hz)
        #self.create_timer(0.02, self.publish_feedback)

    # --- Callbacks ---
    def pos_cb(self, msg):
        if msg.id in self.id_instance_dict:
            self.pos_buffer[msg.id] = msg.target

    def vel_cb(self, msg):
        if msg.id in self.id_instance_dict:
            self.vel_buffer[msg.id] = msg.target

    # --- Core Logic: SyncWrite ---
    def sync_write_timer_callback(self):
        """バッファにある指令をSyncWriteで一括送信する"""

        # ライブラリ側のLockを使い、通信中の衝突を完全に防ぐ
        with dxl_controller._lock:

            # Position一括送信
            if self.pos_buffer:
                for dxl_id, target in self.pos_buffer.items():
                    # 拡張位置モード(4)のオフセット計算などはライブラリ側のadd_sync内に集約
                    self.id_instance_dict[dxl_id].add_sync_param_pos(target)

                # パケット送信
                dxl_controller.groupSyncWrite_pos.txPacket()
                dxl_controller.groupSyncWrite_pos.clearParam()
                self.pos_buffer.clear()

            # Velocity一括送信
            if self.vel_buffer:
                for dxl_id, target in self.vel_buffer.items():
                    self.id_instance_dict[dxl_id].add_sync_param_vel(target)

                dxl_controller.groupSyncWrite_vel.txPacket()
                dxl_controller.groupSyncWrite_vel.clearParam()
                self.vel_buffer.clear()

        #def publish_feedback(self):
        #    """全モーターの状態を読み取ってPublishする"""
        #    # 軸数が多い場合はここもSyncReadにするのが理想ですが、まずはLock付き通常Readで実装
        #    for dxl_id, dxl in self.id_instance_dict.items():
        #        msg = DynaFeedback()
        #        msg.id = dxl_id
        #        msg.present_pos = dxl.read_pos()
        #        msg.present_vel = dxl.read_vel()
        #        self.feedback_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = DynaHandler()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # 終了時にポートを閉じる処理などが必要ならここに追加
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
