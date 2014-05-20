from flask import Flask, request, jsonify, Response
from flask.ext.restful import Resource, Api
import psycopg2, psycopg2.extras, copy, json, subprocess, random, logging, io, sys, os, StringIO, uuid, csv
from src import helper

class bulkData(Resource):
	def get(self, tree_name, bulk_id):
		#Check Tree
		name = helper.valid_tree_name(tree_name)
		conn = 	helper.setConnection()
		if conn is False:
			return jsonify(dict(status=400, success=False, message='Too many connections'))

		cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
		psycopg2.extras.register_json(conn)
		psycopg2.extensions.register_adapter(dict,psycopg2.extras.Json)

		if not helper.tree_exists(conn, name+'_bulk'):
			conn.close()
			return jsonify(dict(status=400, success=False, message='No tree named '+name+' found'))

		try:
			uuid.UUID(bulk_id).hex
		except:
			return jsonify(dict(status=400, success=False, message= 'Bulk id improperly formatted.'))


		#Pull row from tree_name_line
		cur.execute('SELECT * from '+name+'_bulk WHERE id= %s', (bulk_id,))
		lines = cur.fetchone()
		if lines is None:
			return jsonify(dict(status=400, success=False, message= 'No line with the id '+bulk_id))			
		
		conn.close()

		return jsonify({'status': 200, 'success':True, 'tree': name, 'bulk': lines, 'bulk_id':bulk_id})
	
	def delete(self, tree_name, bulk_id):
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

		#Pull bulk listing
		cur.execute('SELECT * from '+name+'_bulk WHERE id = %s', (bulk_id,))
		bulk = cur.fetchone()

		if not bulk:
			conn.close()
			return jsonify(dict(status=400, success=False, message='No bulk transaction with that id.'))

		#Remove line from tree_name_bulk
		lines = bulk['lines']
		sql = ("id = '%s' OR "*len(lines)) % tuple(lines)
		cur.execute("DELETE from "+name+"_line WHERE "+sql[:-4])
		cur.execute('DELETE from '+name+'_bulk WHERE  id = %s', (bulk_id,))
		conn.commit()
		conn.close()

		return jsonify({'status':200, 'success':True, 'message':'bulk transaction '+bulk_id+' has been removed.', 'data':bulk})

	def put(self):
		return jsonify({'status':400, 'success':False, 'message':'Move along... nothing to see here.'})

	def post(self):
		return jsonify({'status':400, 'success':False, 'message':'Move along... nothing to see here.'})