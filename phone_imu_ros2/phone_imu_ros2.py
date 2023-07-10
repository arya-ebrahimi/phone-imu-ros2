import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Quaternion, Vector3
import websocket
import json
import time
import math


class IMU(Node):
    def __init__(self, ip):
        super().__init__('phone_imu_ros2')
                
        self.publisher_ = self.create_publisher(Imu, 'imu', 10)
        

        self.last_quaternion = None
        self.last_angular_vel = None
        self.last_linear_acc = None
        
        self.last_time = time.time()
        
        self.connect('ws://'+ip+'/sensors/connect?types=["android.sensor.orientation","android.sensor.gyroscope","android.sensor.linear_acceleration"]')

        
     
        
    def send_data(self):
        if (self.last_angular_vel != None and 
            self.last_linear_acc != None and
            self.last_quaternion != None): 
            
            msg = Imu()
            msg.header.stamp.sec=int(time.time())
            
            quaternion = Quaternion()
            quaternion.x = self.last_quaternion[0]
            quaternion.y = self.last_quaternion[1]
            quaternion.z = self.last_quaternion[2]
            quaternion.w = self.last_quaternion[3]
            
            msg.orientation = quaternion
            
            
            
            angular_vel = Vector3()
            angular_vel.x = self.last_angular_vel[0]
            angular_vel.y = self.last_angular_vel[1]
            angular_vel.z = self.last_angular_vel[2]
            
            msg.angular_velocity = angular_vel
            
            linear_acc = Vector3()
            linear_acc.x = self.last_linear_acc[0]
            linear_acc.y = self.last_linear_acc[1]
            linear_acc.z = self.last_linear_acc[2]
            
            msg.linear_acceleration = linear_acc
            
                        
            self.publisher_.publish(msg=msg)    
        
    def on_message(self, ws, message):
        values = json.loads(message)['values']
        type = json.loads(message)['type']
        
        if type == 'android.sensor.orientation':
            self.last_quaternion = self.quaternion_from_euler(values[0], values[1], values[2])

        elif type == 'android.sensor.gyroscope':
            self.last_angular_vel = values

        elif type == 'android.sensor.linear_acceleration':
            self.last_linear_acc = values
            
        if (time.time() - self.last_time > 0.2):
            self.send_data()
            self.last_time = time.time()

            

    def on_error(self, ws, error):
        print("error occurred")
        print(error)
        

    def on_close(self, ws, close_code, reason):
        print("connection close")
        print("close code : ", close_code)
        print("reason : ", reason  )

    def on_open(self, ws):
        print("connected")


    def connect(self, url):
        ws = websocket.WebSocketApp(url,
                                on_open=self.on_open,
                                on_message=self.on_message,
                                on_error=self.on_error,
                                on_close=self.on_close)

        ws.run_forever()
    
    def quaternion_from_euler(self, roll, pitch, yaw):
        qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
        qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
        qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
 
        return [qx, qy, qz, qw]


def main(args=None):
    rclpy.init(args=args)
    
    ip = '172.22.12.3:8080'
    node = IMU(ip=ip)
    
    try:
        rclpy.spin(node)
    except SystemExit:
        rclpy.logging.get_logger("Quitting").info('Done')
    
    node.destroy_node()
    rclpy.shutdown()
    
    
if __name__ == '__main__':
    main()
