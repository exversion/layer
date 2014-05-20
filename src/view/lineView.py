from flask import Flask, request, jsonify, Response
from flask.ext.restful import Resource, Api
import psycopg2, psycopg2.extras, copy, json, subprocess, random, logging, io, sys, os, StringIO, uuid, csv
from src import helper

class lineData(Resource):
	def get(self, tree_name, line_id):
		#Check Tree
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

		#Pull row from tree_name_line
		try:
			uuid.UUID(line_id).hex
		except:
			return jsonify(dict(status=400, success=False, message= 'Line id improperly formatted.'))

		cur.execute('SELECT * from '+name+'_line WHERE id= %s', (line_id,))

		line = cur.fetchone()
		if line is None:
			return jsonify(dict(status=400, success=False, message= 'No line with the id '+line_id))			
		conn.close()

		return jsonify({'status': 200, 'success':True, 'tree': name, 'line': line, 'line_id': line_id})

	def delete(self, tree_name, line_id):
		#check that table with tree_name exists
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

		#Find bulk listing
		cur.execute('SELECT * from '+name+'_bulk WHERE lines @> ARRAY[%s]', (line_id,))
		bulk = cur.fetchone()

		#Remove line from tree_name_line
		cur.execute('DELETE from '+name+'_line WHERE id= %s RETURNING *', (line_id,))
		line = cur.fetchone()
		conn.commit()

		if not line:
			conn.close()
			return jsonify(dict(status=400, success=False, message='No line with that id.'))

		#Update bulk to reflect deletion
		if bulk:
			bulk['lines'].remove(line_id)
			cur.execute('UPDATE '+name+'_bulk SET lines = %s WHERE id = %s', (bulk['lines'],bulk['id']))
			conn.commit()
		conn.close()
		
		return jsonify({'status':200, 'success':True, 'message':'line with id '+line_id+' has been removed.', 'data': line})