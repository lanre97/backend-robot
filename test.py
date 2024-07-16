from json import dumps
import asyncio
import re

client = None
task = None

async def init(x: float, y: float, z: float):
  print(f"Initializing with x={x}, y={y}, z={z}")

async def move(x: float, y: float, z: float):
  print(f"Moving to x={x}, y={y}, z={z}")
  data = {
    "x": x,
    "y": y,
    "z": z
  }
  await publish_data('test/mapCoordinatesToRobot', dumps(data))


async def rawMove(vertical: float, horizontal: float, angle: float):
  print(f"Moving to vertical={vertical}, horizontal={horizontal}, angle={angle}")
  data = {
    "vertical": vertical,
    "horizontal": horizontal,
    "angle": angle
  }
  await publish_data('test/mapRobotToCoordinates', dumps(data))

async def stop():
  print("Stopping")

async def log(message: str):
  print(f"Log: {message}")
  await  publish_data('test/logs', message)

async def sleep(seconds: float):
  print(f"Sleeping for {seconds} seconds")
  await asyncio.sleep(seconds)

async def publish_data(topic, data):
  global client
  print(f"Publishing data to topic {topic}")
  if isinstance(data, str):
    data = data.encode('utf-8')  # Convertir la cadena str a bytes
  print(f"Data: {data}")
  await client.publish(topic, data)
  print(f"Data published to topic {topic}")

def mapFunctionsToAsync(code):
    # Lista de funciones que deberían ser precedidas por 'await'
    functions = ["init", "move", "rawMove", "stop", "log", "sleep"]

    # Construir la expresión regular que captura estas funciones no precedidas por 'await'
    regex_pattern = r"(?<!await\s)\b(" + "|".join(functions) + r")\s*\("

    # Función para reemplazar las coincidencias
    def replacer(match):
        function_name = match.group(1)
        return f"await {function_name}("

    # Usar re.sub() para reemplazar en el código fuente
    new_code = re.sub(regex_pattern, replacer, code)

    return new_code

async def execute(code):
  # Ejecutar el código asincrónico directamente dentro de una función asincrónica.
    local_dict = locals()
    indented_code = "\n    ".join(code.splitlines())
    exec_code = f"""
async def _async_exec():
    {indented_code}
"""
    print(exec_code)
    exec(exec_code, globals(), local_dict)  # Usar locals() para incluir funciones definidas localmente
    await local_dict["_async_exec"]()  # Ejecutar la función asíncrona generada
   

async def test(testClient, code):
    global client
    client = testClient
    task = asyncio.create_task(execute(mapFunctionsToAsync(code)))
    await asyncio.sleep(10)
    try:
      task.cancel()
      await task
    except asyncio.CancelledError:
      print("Task was cancelled")
    finally:
      print("Test finished")
      await log("Test finished")
    

