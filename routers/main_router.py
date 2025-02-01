from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def index(request: Request):
    device_controller = request.app.context["device_controller"]
    context = {
        "request": request,
        "app_name": "SporeHut System",
        "deviceconfigs": device_controller.get_device_configs()
    }
    return templates.TemplateResponse('index.html', context)


@router.post("/toggle/{device_id}")
def toggle_state(device_id: str, request: Request):
    print("sending toggle state message to controller for %s" % device_id)
    device_controller = request.app.context["device_controller"]
    device_controller.toggle_on_off(device_id)
    context = {"request": request, "deviceconfigs": device_controller.get_device_configs()}
    # context = device_controller.toggle_on_off("LAMP")

    return templates.TemplateResponse("deviceconfigs.html", context)