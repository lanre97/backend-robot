from fastapi import FastAPI, BackgroundTasks, HTTPException
from amqtt.broker import Broker
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from amqtt.client import MQTTClient
from json import dumps
import asyncio

from test import test as testCode
from robot import test as robotCode

class PublishData(BaseModel):
    topic: str
    message: str

class TestCode(BaseModel):
    code: str

broker_config = {
    'listeners': {
        'default': {
            'type': 'tcp',
            'bind': '127.0.0.1:1884',
        },
        "ws-mqtt": {
          "bind": "0.0.0.0:9000",
          "type": "ws",
          "max_connections": 10,
        },
    },
    'sys_interval': 60,
    'auth': {
        'allow-anonymous': True,
         "plugins": ["auth_anonymous"],
    },
    "topic-check": {
        "enabled": True,
        "plugins": ["topic_acl"],
        "acl": {
            "anonymous": [
               "test/topic",
               "robot/mapCoordinatesToRobot",
               "robot/logs",
               "robot/mapRobotToCoordinates",
               "test/mapCoordinatesToRobot", "test/logs", "test/mapRobotToCoordinates"
            ],
        }
    },
}
broker = Broker(broker_config)
client = MQTTClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.start()
    await client.connect('mqtt://127.0.0.1:1884/')
    try:
        yield
    finally:
        await broker.shutdown()
        await client.disconnect()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lista de orígenes permitidos, ajusta esto según sea necesario
    allow_credentials=True,
    allow_methods=["*"],  # Lista de métodos permitidos
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI over MQTT"}

def sanitize_code(code):
  #remove imports
  code = code.replace("import", "")
  return code

async def init(x: float, y: float, z: float):
  print(f"Initializing with x={x}, y={y}, z={z}")

async def move(x: float, y: float, z: float):
  print(f"Moving to x={x}, y={y}, z={z}")
  data = {
    "x": x,
    "y": y,
    "z": z
  }
  await publish_data('robot/mapCoordinatesToRobot', dumps(data))


async def rawMove(vertical: float, horizontal: float, angle: float):
  print(f"Moving to vertical={vertical}, horizontal={horizontal}, angle={angle}")
  data = {
    "vertical": vertical,
    "horizontal": horizontal,
    "angle": angle
  }
  await publish_data('robot/mapRobotToCoordinates', dumps(data))

async def stop():
  print("Stopping")

async def log(message: str):
  print(f"Log: {message}")
  await  publish_data('robot/logs', message)

async def sleep(seconds: float):
  print(f"Sleeping for {seconds} seconds")
  await asyncio.sleep(seconds)


async def publish_data(topic, data):
  print(f"Publishing data to topic {topic}")
  if isinstance(data, str):
    data = data.encode('utf-8')  # Convertir la cadena str a bytes
  print(f"Data: {data}")
  await client.publish(topic, data)
  print(f"Data published to topic {topic}")

@app.post("/test")
async def test(data: TestCode):
  try:
    asyncio.create_task(testCode(client,  data.code))
    return {"status": "Code executed"}
  except Exception as e:
    print(f"Error executing code: {e}")
    raise HTTPException(status_code=400, detail=f"Error executing code: {e}")
    
@app.post("/robot")
async def test(data: TestCode):
  try:
    asyncio.create_task(robotCode(client,  data.code))
    return {"status": "Code executed"}
  except Exception as e:
    print(f"Error executing code: {e}")
    raise HTTPException(status_code=400, detail=f"Error executing code: {e}")
