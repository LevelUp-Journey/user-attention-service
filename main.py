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
    ip = socket.gethostbyname(hostname)

    data = f"""<?xml version="1.0" encoding="UTF-8"?>
<instance>
    <instanceId>{hostname}:{settings.APP_NAME}:{settings.PORT}</instanceId>
    <hostName>{hostname}</hostName>
    <app>{settings.APP_NAME}</app>
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
            f"{settings.EUREKA_SERVER}/apps/{settings.APP_NAME}",
            content=data,
            headers=headers,
        )
        print("Eureka registration status:", response.status_code)


def send_heartbeat():
    hostname = socket.gethostname()
    while True:
        try:
            with httpx.Client() as client:
                response = client.put(
                    f"{settings.EUREKA_SERVER}/apps/{settings.APP_NAME}/{hostname}:{settings.APP_NAME}:{settings.PORT}"
                )
                print("Heartbeat sent, status:", response.status_code)
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
    await register_with_eureka()
    # Start heartbeat in a thread
    threading.Thread(target=send_heartbeat, daemon=True).start()


@app.get("/")
def read_root():
    return {"hello": "world"}


@app.post("/suggestions")
def create_suggestion(
    suggestion: CreateSuggestion,
    session: Session = Depends(get_session),
):
    db_suggestion = Suggestion(comment=suggestion.comment)

    session.add(db_suggestion)
    session.commit()

    session.refresh(db_suggestion)

    return {"data": db_suggestion}


@app.get("/suggestions")
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
