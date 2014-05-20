from flask import Flask, request, jsonify, Response
from flask.ext.restful import Resource, Api
import psycopg2, psycopg2.extras, copy, json, subprocess, random, logging, io, sys, os, StringIO, uuid, csv
from src import helper

class schemaData(Resource):
	def get(self, tree_name, branch_identifier):
		#Get all schema changes
		name = helper.valid_tree_name(tree_name)
		conn = 	helper.setConnection()
		if conn is False:
			return jsonify(dict(status=400, success=False, message='Too many connections'))
		cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
		psycopg2.extras.register_json(conn)
		if not helper.tree_exists(conn, name+'_line'):
			conn.close()
			return jsonify(dict(status=400, success=False, message='No tree named '+name+' found'))

		#If branch name is provided instead of id, grab id
		branch_id, branch_name = helper.ensure_branch_id(conn, name, branch_identifier)
		if branch_id == False:
			conn.close()
			return jsonify(dict(status=400, success=False, message=str(branch_identifier)+' is not a valid branch name or id for tree '+name+'.'))

		#select all commits from tree_name_line table
		cur.execute('SELECT * from exlayer_schema WHERE tree_name = %s AND branch_id = %s ORDER BY created_at DESC LIMIT 200', (name, branch_name))
		changes = cur.fetchall() 

		return jsonify({'status': 200, 'success':True, 'tree': name, 'schema_changes': changes})


	def post(self, tree_name, branch_identifier):
		#Register a schema change
		name = helper.valid_tree_name(tree_name)
		conn = 	helper.setConnection()
		if conn is False:
			return jsonify(dict(status=400, success=False, message='Too many connections'))

		cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
		psycopg2.extras.register_json(conn)
		psycopg2.extensions.register_adapter(dict,psycopg2.extras.Json)

		if not helper.tree_exists(conn, name+'_line'):
			conn.close()
			return jsonify(dict(status=400, success=False, message='No tree named '+name+' found'))

		#decode JSON body
		data = json.loads(request.data)

		branch_id, branch_name = helper.ensure_branch_id(conn, name, branch_identifier)
		if branch_id == False:
			conn.close()
			return jsonify(dict(status=400, success=False, message=str(branch_identifier)+' is not a valid branch name or id for tree '+name+'.'))

		#{'field':'name', 'meta':{'type':'delete', 'data':[{'column_value':'', 'ids':[]}]}}

		field = data.get('field','')
		meta = data.get('meta', {})
		cur.execute('INSERT into exlayer_schema (tree_name, branch_id, fields, meta) VALUES (%s,%s,%s,%s) RETURNING exlayer_schema.id', (name, branch_name, field, json.dumps(meta)))
		conn.commit()
		schema_id = cur.fetchone()['id']
		conn.close()

		return jsonify({'status': 200, 'success':True, 'tree': name, 'branch_name': branch_name, 'schema_id':schema_id})

