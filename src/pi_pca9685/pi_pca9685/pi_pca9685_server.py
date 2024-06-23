import rclpy
import time
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from pi_pca9685_interfaces.action import PCA
from adafruit_servokit import ServoKit

class PCA9685_Servo:
    def __init__(self):
        self.kit = ServoKit(channels=16)
        
    def set_angle(self, servo_id, angle):
        self.kit.servo[servo_id].angle = angle


class PCA9685ActionServer(Node):
    def __init__(self):
        super().__init__('pi_pca9685_server')
        
        self.servo_controller = PCA9685_Servo()

        self._action_server = ActionServer(
            self,
            PCA,
            'pi_pca9685_server',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            handle_accepted_callback=self.handle_accepted_callback,
            cancel_callback=self.cancel_callback,
            callback_group=ReentrantCallbackGroup())

    def destroy(self):
        self._action_server.destroy()
        super().destroy_node()

    def goal_callback(self, goal_request):
        self.get_logger().info('Received goal request')
        return GoalResponse.ACCEPT

    def handle_accepted_callback(self, goal_handle):
        self.get_logger().info('Handle Goal Accept')
        goal_handle.execute()

    def cancel_callback(self, goal):
        self.get_logger().info('Received cancel request')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing goal...')
        
        server_servo_commands = goal_handle.request.pca
        feedback_msg = PCA.Feedback()
        result = PCA.Result()
        self.get_logger().info(f'Received goal: {server_servo_commands}')
        
        servo_id, servo_angle = server_servo_commands.split(',')
        servo_id = int(servo_id)
        angle = int(servo_angle)

        self.get_logger().info(f'Setting servo {servo_id} to angle {angle}')
        self.servo_controller.set_angle(servo_id, angle)

        feedback_msg.feedback = f'Servo {servo_id} set to angle {angle}'
        goal_handle.publish_feedback(feedback_msg)
        self.get_logger().info('Submit Feedback')
        result.success = True
        self.get_logger().info('Returned the Result')
        goal_handle.succeed()
        self.get_logger().info('Goal succeeded')
        return result

def main(args=None):
    rclpy.init(args=args)

    action_server = PCA9685ActionServer()

    executor = MultiThreadedExecutor()
    rclpy.spin(action_server, executor=executor)

    action_server.destroy()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
