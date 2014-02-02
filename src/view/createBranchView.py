from flask import Flask, request, jsonify, Response
from flask.ext.restful import Resource, Api
import psycopg2, psycopg2.extras, copy, json, subprocess, random, logging, io, sys, os, StringIO, uuid, csv
from src import helper

class createBranch(Resource):
	def post(self, tree_name):
		#{'branch_name':"", 'meta':{}}

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

		#decode JSON body
		data = json.loads(request.data)
		branch_name = data.get('branch_name', None)
		if branch_name is None or branch_name == '':
			branch_name = name + str(random.randint(0,9999))

		#check if branch exists with this name already
		branch_test = helper.branch_exists(conn, branch_name)
		if branch_test:
			conn.close()
			return jsonify(dict(status=400, success=False, message='Branch named '+branch_name+' already exists.', branch_id=branch_test))

		meta = data.get('meta', {})
		cur.execute('INSERT into exlayer_branches (branch_name, tree_name, meta) VALUES (%s,%s,%s) RETURNING exlayer_branches.id', (branch_name, name,json.dumps(meta)))
		conn.commit()
		branch_id = cur.fetchone()['id']
		conn.close()

		return jsonify({'status': 200, 'success':True, 'tree': name, 'branch_name': branch_name, 'branch_id':branch_id})

