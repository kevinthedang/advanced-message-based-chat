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
USER_GENERAL_LIST = 'general_users'

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

@app.get("/messages/", status_code=200)
async def get_messages(request: Request, alias: str, room_name: str, messages_to_get: int = GET_ALL_MESSAGES):
    """ API for getting messages
        NOTE: Refer to get_messages() in the room.py file
    """
    logging.info("starting messages method")
    if (queue_instance := ChatRoom(room_name = room_name, member_list = users, owner_alias = DEFAULT_OWNER_ALIAS)) is None:
        return JSONResponse(status_code=415, content=f'ChatRoom does not exist.')
    messages, message_objects, total_mess = queue_instance.get_messages(num_messages = messages_to_get)
    logging.info(f'inside messages handler, after getting messages for queue: {alias}\n messages are {messages}')
    for message in message_objects:
        logging.info(f'Message: {message.message} == message props: {message.mess_props} host is {request.client.host}')
        logging.info(request.json())
    logging.info("End Messages")
    return messages

@app.get("/users/", status_code=200)
async def get_users():
    """ API for getting users
        NOTE: Might want to consider using get_all_users() from the users.py
    """
    try:
        users = UserList()
    except:
        users = UserList(USER_GENERAL_LIST)
    if users.get_all_users() is not None:
        return "success"
    else:
        return Response(status_code=410, content="user_list was empty")

@app.post("/alias", status_code=201)
async def register_client(client_alias: str):
    """ API for adding a user alias
        NOTE: Refer to the users.py on what might be called here
        NOTE: Code to register a user/alias. Simple method calls
    """
    try:
        users = UserList()
    except:
        users = UserList(USER_GENERAL_LIST)
    if users.get(client_alias) is None:
        users.register(client_alias)
        return "success"
    else:
        return Response(status_code=410, content="User exists already")

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
    if current_room.send_message(message = message) is True:
        return 'success'
    else:
        return JSONResponse(status_code=410, content="unroutable error")

def main():
    logging.basicConfig(filename='chat.log', level=logging.INFO)
    MY_IPADDRESS = socket.gethostbyname(socket.gethostname())
    MY_NAME = input("Please enter your name: ")

if __name__ == "__main__":
    main()
