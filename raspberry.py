import paho.mqtt.client as mqtt
import serial
import threading
import time

ser1 = serial.Serial('COM3', 9600, timeout=1)
ser1.reset_input_buffer()
ser = serial.Serial('COM4', 9600, timeout=1)
ser.reset_input_buffer()

hostname = "8.tcp.ngrok.io"
broker_port = 15762

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code: " + str(rc))
    client.subscribe("robot/mapCoordinatesToRobot")
    client.subscribe("robot/mapRobotToCoordinates")
    client.subscribe("robot/logs")
    client.subscribe("$SYS/#")
    
def on_message(client, userdata, msg):
    print("Message received on topic " + msg.topic)
    payload_str = msg.payload.decode('utf-8')  # Convertir el payload a string

    if msg.topic == "robot/mapCoordinatesToRobot":
        data = eval(payload_str)  # Deserializar el payload a diccionario
        print("Mapping coordinates to robot")
        x = data["x"]
        y = data["y"]
        z = data["z"]
        serialized_data = f"mapCoordinatesToRobot {x} {y} {z}\n"
        write_to_serial(serialized_data, ser, ser1)
    elif msg.topic == "robot/mapRobotToCoordinates":
        data = eval(payload_str)  # Deserializar el payload a diccionario
        print("Mapping robot to coordinates")
        vertical = data["vertical"]
        horizontal = data["horizontal"]
        angle = data["angle"]
        serialized_data = f"mapRobotToCoordinates {vertical} {horizontal} {angle}\n"
        write_to_serial(serialized_data, ser, ser1)
    elif msg.topic == "robot/logs":
        print("Logging")
        serialized_data = f"log {payload_str}\n"
        write_to_serial(serialized_data, ser, ser1)
    elif msg.topic == "$SYS/#":
        print("System message")
        print(payload_str)

def write_to_serial(data, serial_port1, serial_port2):
    def write_data(port, data):
        port.write(data.encode())
        time.sleep(1)
    
    thread1 = threading.Thread(target=write_data, args=(serial_port1, data))
    thread2 = threading.Thread(target=write_data, args=(serial_port2, data))
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()

def read_serial(serial_port, name):
    while True:
        if serial_port.in_waiting > 0:
            line = serial_port.readline().decode('utf-8', errors='ignore').rstrip()
            print(f"{name}: {line}")

client.on_connect = on_connect
client.on_message = on_message

# Iniciar los hilos para leer los puertos seriales
serial_thread_1 = threading.Thread(target=read_serial, args=(ser, "Arduino COM4"))
serial_thread_1.daemon = True
serial_thread_1.start()

serial_thread_2 = threading.Thread(target=read_serial, args=(ser1, "Arduino COM3"))
serial_thread_2.daemon = True
serial_thread_2.start()

client.connect(hostname, broker_port, 60)

client.loop_forever()
