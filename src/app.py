#!flask/bin/python

from flask import Flask, request, jsonify, Response
from flask.ext.restful import Resource, Api
import psycopg2, psycopg2.extras, copy, json, subprocess, random, logging, io, sys, os, StringIO, uuid, csv

import helper
from view import treeView, createBranchView, branchView, lineView, bulkView, schemaView, schemaRemove



def create_app():

	app = Flask(__name__)
	api = Api(app, catch_all_404s=True)

	logging.basicConfig(filename='exlayer.log', level=logging.DEBUG)



	@app.route('/')

	def index():
		conn = 	helper.setConnection()
		if conn is False:
			return jsonify(dict(status=400, success=False, message='Too many connections'))

		#Are our basic tables setup? If not, set them up automatically
		if not helper.layer_set_up(conn):
			cur = conn.cursor()
			try:
				#Setup branches 
				cur.execute('CREATE TABLE exlayer_branches (id serial, branch_name text, tree_name text, meta json, created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW())')
				#Setup schema
				cur.execute('CREATE TABLE exlayer_schema (id uuid DEFAULT uuid_generate_v1mc(), tree_name text, branch_id int, fields text, meta json, created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW())')
				conn.commit()
			except:
				return jsonify({'status': 400, 'success':False, 'message':'Sorry, layer could not setup. Check DB settings and permissions and try again', 'db':app.config['DBNAME'], 'user':app.config['DBUSER']})				

		return jsonify({'status': 200, 'success':True, 'message':'Hello. My name is Layer!'})



	@app.route('/create/', methods = ['POST'])

	def create_tree():

		# {'name':"", 'meta':{description':"", 'owner':""} 'schema':[

			## {"name":"", "title":"", "type":"","format":"", "description":""}

		# ]}

		data = json.loads(request.data)

		name = data.get('name', None)

		meta = data.get('meta', None)

		schema = data.get('schema', None)

		conn = 	helper.setConnection()
		if conn is False:
			return jsonify(dict(status=400, success=False, message='Too many connections'))

		cur = conn.cursor()



		#Make sure tree name is valid

		name = helper.valid_tree_name(name)

		

		#If the tables already exist with that name return an error

		if helper.tree_exists(conn, name+'_line'):

			conn.close()

			return jsonify(dict(status=400, success=False, message='Cannot create tree because '+name+' is invalid or already in use'))



		#Create tree_name_line, tree_name_bulk and add line to branches and schema

		## TREE_NAME_LINE

		## id uuid DEFAULT uuid_generate_vlmc()

		## branch_id int

		## old_state json

		## new_state json

		## primary_key varchan(455)

		## meta json

		## created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()



		cur.execute('CREATE TABLE '+name+'_line'+' (id uuid DEFAULT uuid_generate_v1mc(), branch_id int, old_state json, new_state json, primary_key varchar(455), meta json, created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW())')



		## TREE_NAME_BULK

		## id uuid DEFAULT uuid_generate_v1mc()

		## branch_id int

		## states json

		## lines text[]

		## meta json

		## created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()



		cur.execute('CREATE TABLE '+name+'_bulk'+' (id uuid DEFAULT uuid_generate_v1mc(), branch_id int, states json, lines text[], meta json, created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW())')



		#Do some inserts

		branch_name = 'master'

		cur.execute('INSERT into exlayer_branches (branch_name, tree_name, meta) VALUES (%s,%s,%s) RETURNING exlayer_branches.id', (branch_name, name,json.dumps(meta)))

		conn.commit()



		#get row id

		branch_id = cur.fetchone()[0]

		

		# If schema has been defined

		if schema:

			cur.execute('INSERT into exlayer_schema (tree_name, branch_id, fields) VALUES (%s,%s)', (name,branch_id.json.dumps(schema)))

			conn.commit()



		conn.close()

		return jsonify(dict(status=200, success=True, tree_name=name, meta=meta, schema=schema, branch_id=branch_id))

		#return jsonify({'name': '', 'index': 'id', 'location':'127.0.0.1:5000','owner':'Marianne'})


	api.add_resource(treeView.dataTree, '/<tree_name>/')
	api.add_resource(lineView.lineData, '/<tree_name>/line/<line_id>/')
	api.add_resource(bulkView.bulkData, '/<tree_name>/bulk/<bulk_id>/', methods=['GET','DELETE'])
	api.add_resource(createBranchView.createBranch, '/<tree_name>/branch/')
	api.add_resource(branchView.branchData, '/<tree_name>/branch/<branch_identifier>/')
	api.add_resource(schemaView.schemaData, '/<tree_name>/schema/<branch_identifier>/')
	api.add_resource(schemaRemove.removeSchema, '/<tree_name>/schema/<branch_identifier>/<schema_id>/',methods=['DELETE'])
	
	app.config.from_pyfile(os.path.dirname('../config/config.py')+'/../config/config.py')

	#@app.before_request
    #	def write_access_log():
    #		return 'Path: '+request.path

	return app



