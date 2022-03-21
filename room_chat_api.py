import socket
import logging
import json
from fastapi import FastAPI, Request, status, Form
from fastapi.responses import JSONResponse, ORJSONResponse, Response
from fastapi.templating import Jinja2Templates
from room import *
from constants import *
from users import *

MY_IPADDRESS = ""

# This is an extremely rare case where I have global variables. The first is the documented way to deal with running the app in uvicorn, the second is the 
# instance of the rmq class that is necessary across all handlers that behave essentially as callbacks. 


app = FastAPI()
room_list = RoomList()
users = UserList()
templates = Jinja2Templates(directory="")
logging.basicConfig(filename='chat.log', level=logging.INFO)

@app.get("/")
async def index():
    """ Default page
    """
    return {"message": {"from": "kevin", "to": "you"}}

@app.get("/page/send", status_code=200)
async def send_form(request: Request):
    """ HTML GET page form sending a message
    """
    pass

@app.post("/page/send", status_code=201)
async def get_form(request: Request, room_choice: str = Form(...), message: str = Form(...), alias: str = Form(...)):
    """ HTML POST page for sending a message
    """
    pass

@app.get("/page/messages", status_code=200)
async def form_messages(request: Request, room_name: str = DEFAULT_PUBLIC_ROOM):
    """ HTML GET page for seeing messages
    """
    pass

@app.post("/page/messages", status_code=201)
async def form_messages(request: Request, room_name: str = Form(...)):
    """ HTML POST page for seeing messages in a different room or different quantities
    """
    pass


@app.get("/messages/", status_code=200)
async def get_messages(request: Request, alias: str, room_name: str, messages_to_get: int = GET_ALL_MESSAGES):
    """ API for getting messages
        NOTE: Refer to get_messages() in the room.py file
    """
    pass

@app.get("/users/", status_code=200)
async def get_users():
    """ API for getting users
        NOTE: Might want to consider using get_all_users() from the users.py
    """
    pass

@app.post("/alias", status_code=201)
async def register_client(client_alias: str):
    """ API for adding a user alias
        NOTE: Refer to the users.py on what might be called here
    """
    pass

@app.post("/room")
async def create_room(room_name: str, owner_alias: str, room_type: int = ROOM_TYPE_PRIVATE):
    """ API for creating a room
        NOTE: Refer to the room.py -> RoomList -> Create() or add() to know what the API should do
            add() maybe for adding the room to the MongoDB
    """
    room_list.add(room_list.create(room_name = room_name, owner_alias = owner_alias, room_type = room_type))

@app.post("/message/", status_code=201)
async def send_message(room_name: str, message: str):
    """ API for sending a message
        NOTE: Refer to send_message() in room.py, may help
    """
    current_room = room_list.get(room_name)
    current_room.send_message(message = message)

def main():
    logging.basicConfig(filename='chat.log', level=logging.INFO)
    MY_IPADDRESS = socket.gethostbyname(socket.gethostname())
    MY_NAME = input("Please enter your name: ")

if __name__ == "__main__":
    main()
