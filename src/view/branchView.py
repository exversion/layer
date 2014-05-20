from flask import Flask, request, jsonify, Response
from flask.ext.restful import Resource, Api
import psycopg2, psycopg2.extras, copy, json, subprocess, random, logging, io, sys, os, StringIO, uuid, csv
from src import helper

class branchData(Resource):
	def get(self, tree_name, branch_identifier):
		#check that table with tree_name exists
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
		cur.execute('SELECT * from '+name+'_line WHERE branch_id = %s ORDER BY created_at DESC LIMIT 200', (branch_id,))
		lines = cur.fetchall() 

		#select all bulk updates from tree_name_bulk table
		cur.execute('SELECT id, lines, meta, created_at from '+name+'_bulk WHERE branch_id = %s ORDER BY created_at DESC', (branch_id,))
		bulk = cur.fetchall()
		conn.close()

		return jsonify({'status': 200, 'success':True, 'tree': name, 'recent_changes': lines, 'bulk_updates':bulk})


