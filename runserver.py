from flask import Flask
from src import app
from config import config

layer = app.create_app()

if __name__ == '__main__':
	layer.config['SERVER_NAME'] = 'localhost:1338'
	layer.run(debug = True)
	layer.run()