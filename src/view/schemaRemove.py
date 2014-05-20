from flask import Flask, request, jsonify, Response
from flask.ext.restful import Resource, Api
import psycopg2, psycopg2.extras, copy, json, subprocess, random, logging, io, sys, os, StringIO, uuid, csv
from src import helper

class removeSchema(Resource):
	def get(self, tree_name, branch_identifier, schema_id):
		return jsonify({'status':400, 'success':False, 'message':'Move along... nothing to see here.'})

	def delete(self, tree_name, branch_identifier, schema_id):
		#Delete a specific schema change
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

		#Remove line from schema
		cur.execute('DELETE from exlayer_schema WHERE id= %s RETURNING *', (schema_id,))
		line = cur.fetchone()
		conn.commit()

		if not line:
			conn.close()
			return jsonify(dict(status=400, success=False, message='No schema change with that id.'))

		
		return jsonify({'status':200, 'success':True, 'message':'schema change with id '+schema_id+' has been removed.', 'data': line})