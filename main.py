import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from typing import NoReturn
# from fasapi.staticfiles import StaticFiles

from controller import DeviceManager
from routers import main_router

context = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    
    Args:

    Notes:
        https://fastapi.tiangolo.com/fa/advanced/events/
        https://github.com/tiangolog/fastapi/discussions/9664 (see example by kmalkraj)
    """
    device_mgr = DeviceManager()
    device_mgr.start()
    device_controller = device_mgr.get_controller()
    app.context = {
        "device_controller": device_controller
    }
    # app.backend_context = conext
    print("Liefespan context added, %s" % app.context)
    yield
    # do shutdown stuff


def main(port: int, host: str) -> NoReturn:
    """
    Starts the FastAPI application

    Args:
        port: the port to serve the application on
        host: the server hosting the application
    """

    app = FastAPI(lifespan=lifespan)
    # app = FastAPI()
    app.include_router(main_router.router)
    # app.mount("/static", StaticFiles(directory="assets"), name="static")
    print("Starting application server...")
    uvicorn.run(app, port=port, host=host)


if __name__ == "__main__":
    # start the application server
    # main(8080, "localhost")
    pi_hostip = "192.168.0.202"
    main(8080, pi_hostip)