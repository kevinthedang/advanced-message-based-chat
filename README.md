# Advanced Basic Message Chat
This implementation of a message chat will utilize MongoDB

## Requirements
* Pika and FastAPI required on the machine
    * ```pip install -r requirements.txt``` to install required libraries

## To Connect to Server
* ```python -m uvicorn mess_chat:app --reload```

## Libraries Used
* [Python Pika](https://pypi.org/project/pika/#:~:text=Pika%20is%20a%20RabbitMQ%20%28AMQP%200-9-1%29%20client%20library,RabbitMQ%E2%80%99s%20extensions.%20Python%202.7%20and%203.4%2B%20are%20supported.)

## Microservices / API's
* [RabbitMQ](https://www.rabbitmq.com/#features)
* [FastAPI](https://fastapi.tiangolo.com/)
* [MongoDB](https://docs.mongodb.com/manual/?_ga=2.213141972.1346719986.1645739830-1894126807.1645739830)

## Useful Information
* [Basic Message Chat Implementation](https://github.com/kevinthedang/message-based-chat)
* [Django Tutorial](https://docs.djangoproject.com/en/4.0/intro/tutorial01/)