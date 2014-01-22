from flask import Flask
from src import app
from config import config


if __name__ == '__main__':
	layer = app.create_app()
	layer.config['SERVER_NAME'] = 'localhost:1337'
	layer.run(debug = True)