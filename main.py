import socket
import threading
import time
import xml.etree.ElementTree as ET
from typing import Annotated, Generator

import httpx
from fastapi import Depends, FastAPI, Header
from sqlmodel import Session, select
from sqlmodel.main import SQLModel

from config import settings
from src.db_config import engine
from src.models import CommonHeader, CreateSuggestion, Suggestion

app = FastAPI(title="User Attention Service")


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


async def register_with_eureka():
    hostname = socket.gethostname()

    # Obtener IP pública o IP local correcta
    try:
        # Intentar obtener la IP pública
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("https://api.ipify.org?format=text")
            ip = response.text.strip()
            print(f"Using public IP: {ip}")
    except Exception as e:
        print(f"Could not get public IP, using local IP. Error: {e}")
        # Fallback: obtener IP local que se usa para conectarse al exterior
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = socket.gethostbyname(hostname)
        finally:
            s.close()
        print(f"Using local IP: {ip}")

    app_name_upper = settings.APP_NAME.upper()
    instance_id = f"{ip}:{app_name_upper}:{settings.PORT}"

    data = f"""<?xml version="1.0" encoding="UTF-8"?>
<instance>
    <instanceId>{instance_id}</instanceId>
    <hostName>{ip}</hostName>
    <app>{app_name_upper}</app>
    <ipAddr>{ip}</ipAddr>
    <status>UP</status>
    <port enabled="true">{settings.PORT}</port>
    <dataCenterInfo class="com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo">
        <name>MyOwn</name>
    </dataCenterInfo>
</instance>"""

    headers = {"Content-Type": "application/xml"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.EUREKA_SERVER}/apps/{app_name_upper}",
            content=data,
            headers=headers,
        )
        print(f"Eureka registration status: {response.status_code}")
        print(f"Registered as: {app_name_upper} with instance ID: {instance_id}")


def send_heartbeat():
    # Obtener IP local/pública
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get("https://api.ipify.org?format=text")
            ip = response.text.strip()
    except Exception:
        # Fallback a IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = socket.gethostbyname(socket.gethostname())
        finally:
            s.close()

    app_name_upper = settings.APP_NAME.upper()
    instance_id = f"{ip}:{app_name_upper}:{settings.PORT}"

    while True:
        try:
            with httpx.Client() as client:
                response = client.put(
                    f"{settings.EUREKA_SERVER}/apps/{app_name_upper}/{instance_id}"
                )
                print(
                    f"Heartbeat sent to {app_name_upper}, status:", response.status_code
                )
        except Exception as e:
            print("Heartbeat failed:", e)
        time.sleep(30)


async def get_service_url(app_name: str) -> str | None:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.EUREKA_SERVER}/apps/{app_name}")
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            instance = root.find(".//instance")
            if instance is not None:
                ip_elem = instance.find("ipAddr")
                port_elem = instance.find("port")
                if ip_elem is not None and port_elem is not None:
                    ip = ip_elem.text
                    port = port_elem.text
                    return f"http://{ip}:{port}"
    return None


# Configuration for database
@app.on_event("startup")
async def startup():
    SQLModel.metadata.create_all(engine)
    print("Database tables created")
    try:
        await register_with_eureka()
        # Start heartbeat in a thread
        threading.Thread(target=send_heartbeat, daemon=True).start()
    except Exception as e:
        print(f"Failed to register with Eureka: {e}")


@app.get("/api/v1/user-services")
def read_root():
    return {"hello": "world"}


@app.post("/api/v1/suggestions")
def create_suggestion(
    suggestion: CreateSuggestion,
    session: Session = Depends(get_session),
):
    db_suggestion = Suggestion(comment=suggestion.comment)

    session.add(db_suggestion)
    session.commit()

    session.refresh(db_suggestion)

    return {"data": db_suggestion}


@app.get("/api/v1/suggestions")
def read_suggestions(
    headers: Annotated[CommonHeader, Header()], session: Session = Depends(get_session)
):
    db_suggestions = session.exec(select(Suggestion)).all()
    return {"data": db_suggestions, "headers": headers}


@app.get("/discover/{app_name}")
async def discover_service(app_name: str):
    url = await get_service_url(app_name)
    if url:
        return {"service_url": url}
    return {"error": "Service not found"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
