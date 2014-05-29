from flask import Flask, request, jsonify, Response
from flask.ext.restful import Resource, Api
import psycopg2, psycopg2.extras, copy, json, subprocess, random, logging, io, sys, os, StringIO, uuid, csv
from src import helper

logging.basicConfig(filename='exlayer.log', level=logging.DEBUG)

class dataTree(Resource):
	def get(self, tree_name):
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

		#select all commits from tree_name_line table
		cur.execute('SELECT * from '+name+'_line ORDER BY created_at DESC LIMIT 200')
		lines = cur.fetchall() 

		#select all bulk updates from tree_name_bulk table
		cur.execute('SELECT id, lines, meta, created_at from '+name+'_bulk')
		bulk = cur.fetchall()
		conn.close()

		return jsonify({'status': 200, 'success':True, 'tree': name, 'recent_changes': lines, 'bulk_updates':bulk})

	def post(self, tree_name):
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

		#Is there a branch?
		branch = data.get('branch_name', None)
		branch_id, branch_name = helper.ensure_branch_id(conn, name, branch)

		if not branch_id:
			#Assume this is the origin branch and pull id
			cur.execute('SELECT id from exlayer_branches WHERE tree_name=%s', (name,))
			branch_id = cur.fetchone()['id']

		#Check the branch is registered
		if not helper.branch_exists(conn, branch_name):
			conn.close()
			return jsonify(dict(status=400, success=False, message='No branch named '+str(branch_name)+' found'))


		#{'branch':'', data':[{'old_state':'', 'new_state':'', 'primary_key':'', 'meta':''}]}

		#Iterate
		updates = data.get('data', None)
		error = []
		lines = []
		ids = []
		inserted = [] 
		states = []

		if updates is None:
			conn.close()
			return jsonify(dict(status=400, success=False, message='Poorly formatted request.'))

		for u in updates:
			#If no new_state put object in ERROR array
			if not 'new_state' in u:
				error.append(u)
				continue
			if not 'primary_key' in u:
					error.append(u)
					continue
			#If no old_state search table for row_id and grab data
			if not 'old_state' in u:
				cur.execute('SELECT new_state from '+name+'_line'+' WHERE primary_key=%s', (u['primary_key'],))
				u['old_state'] = cur.fetchone()
			#generate uuid
			u['id'] = uuid.uuid1()
			ids.append(str(u['id']))

			#No point adding old_state info if it's an insert
			if 'old_state' in u:
				states.append({'primary_key':u['primary_key'], 'id':str(u['id']), 'old_state':u['old_state'], 'new_state':u['new_state']})
			else:
				states.append({'primary_key':u['primary_key'], 'id':str(u['id']), 'old_state':{}, 'new_state':u['new_state']})

			#separate to avoid double encoding issues
			l = helper.missing_columns_no_encoding(copy.deepcopy(u))
			inserted.append(l)

			#Fill missing columns
			u = helper.missing_columns(u)
			u['branch_id'] = branch_id

			#Insert into line table
			lines.append({k:v.encode('utf8') if isinstance(v, unicode) else v for k,v in u.items()})

		#use COPY to do a super fast bulk insert
		cols = ['id','branch_id','old_state','new_state','primary_key','meta','created_at']
		strcsv = StringIO.StringIO()
		w = csv.DictWriter(strcsv, cols, quoting=csv.QUOTE_NONNUMERIC, quotechar="'", doublequote=False, escapechar="\\")

		#w.writeheader()
		w.writerows(lines)
		strcsv.seek(0)
		sql = "COPY %s FROM STDIN DELIMITERS ',' CSV QUOTE ''''" % (name+'_line',)
		cur.copy_expert(sql, strcsv)
		#cur.copy_from(strcsv, name+'_line', sep=',', columns=cols)
		#Allow bulk transactions to be turned off by setting bulk to False
		if data.get('bulk', True):
			bulk_id = None

			#Get meta
			bulk_meta = data.get('meta', {})

			#Insert in bulk table
			cur.execute('INSERT into '+name+'_bulk (branch_id, states, lines, meta) VALUES (%s,%s,%s, %s) RETURNING '+name+'_bulk.id', (branch_id, psycopg2.extras.Json(states), ids, psycopg2.extras.Json(bulk_meta)))
			conn.commit()

			bulk_id = cur.fetchone()['id']
			conn.close()
			return jsonify({'status':200, 'success':True, 'bulk':bulk_id, 'inserted': inserted, 'errored': error})
		
		conn.commit()
		conn.close()
		return jsonify({'status':200, 'success':True, 'inserted': inserted, 'errored': error})

	def put(self, tree_name):
        #Does table with name exist?
		name = helper.valid_tree_name(tree_name)
		conn = 	helper.setConnection()
		if conn is False:
			return jsonify(dict(status=400, success=False, message='Too many connections'))
		cur = conn.cursor()

		if not helper.tree_exists(conn, name+'_line'):
			conn.close()
			return jsonify(dict(status=400, success=False, message='No tree named '+name+' found'))

		#Pull PUT DATA
		data = json.loads(request.data)
		#Is there a schema?

		#Pull existing data
		return jsonify({name:tree_name})

		#update owner, location, or id_column

	def delete(self, tree_name):
		#Does tree_name even exist?
		name = helper.valid_tree_name(tree_name)
		conn = 	helper.setConnection()
		if conn is False:
			return jsonify(dict(status=400, success=False, message='Too many connections'))
		cur = conn.cursor()

		if not helper.tree_exists(conn, name+'_line'):
			conn.close()
			return jsonify(dict(status=400, success=False, message='No tree named '+name+' found'))

		#Write backup file
		try:
			os.system(helper.dump_command(name, os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'backups', name+'.sql'))))
		except:
			logging.debug('Backup of '+name+' tables failed')
			conn.close()
			return jsonify(dict(status=400, message='Not able to delete tree named '+name+' at this time. Please check the logs for more information'))

		#Backup branch info
		try:
			branches_file = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'backups', name+'_branches.csv'))
			bf = io.open(branches_file,'w')
			sql = "COPY (select * from exlayer_branches where tree_name = '%s') TO STDOUT WITH CSV HEADER" % (name,)
			cur.copy_expert(sql, bf)
			bf.close()

		except Exception, e:
			logging.debug('Backup of '+name+' branches failed: '+str(e))
			conn.close()
			return jsonify(dict(status=400, message='Not able to delete tree named '+name+' at this time. Please check the logs for more information'))

		#Delete tree_name_line, tree_name_bulk and tree_name_schema
		cur.execute('DROP TABLE '+name+'_line, '+name+'_bulk')
		#Remove branches
		cur.execute('DELETE from exlayer_branches where tree_name=%s', (name,))
		conn.commit()
		conn.close()

		return jsonify(dict(status=200, success=True, message='Tree '+name+' has been successfully deleted. A backup can be found in the backups directory.'))
