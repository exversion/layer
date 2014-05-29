import psycopg2, re, json, datetime, collections, psycopg2.extras

from config import config



def setConnection():
	#try:
		conn = psycopg2.connect("host='"+config.DATABASE_HOST+"' dbname='"+config.DBNAME+"' user='"+config.DBUSER+"' password='"+config.DBPASSWORD+"'")
		return conn
	#except:
		#return False

def layer_set_up(conn):
	cur = conn.cursor()

	cur.execute("select * from information_schema.tables where table_name=%s", ('exlayer_branches',))

	return bool(cur.rowcount)

def valid_tree_name(name):

	reserved = ['exlayer_branches']



	if name:

		name = name.lower()

		name = name.strip()

		if name == '' or name is None or name is False:

			return False

		if name in reserved:

			return False

		#Really wish python had the -> operator like in Clojure :(

		name = re.sub("#", "num", name)

		name = re.sub(r'[^A-Za-z0-9_ ]', "", name)

		name = re.sub(r'\s',"_", name)

		name = re.sub(r'_{2,}',"_",name)

	else:

		return False

	return name



def dump_command(name, filepath):

	return 'export PGPASSWORD=%s\npg_dump %s -t %s -t %s -h %s --username=%s -f %s' % (config.DBPASSWORD, config.DBNAME, name+'_line', name+'_bulk', config.DATABASE_HOST, config.DBUSER, filepath)



def tree_exists(conn, name):

	cur = conn.cursor()

	cur.execute("select * from information_schema.tables where table_name=%s", (name,))

	return bool(cur.rowcount)

def branch_exists(conn, name):

	try:
		cur = conn.cursor()

		cur.execute("select id from exlayer_branches where branch_name=%s", (name,))

		branch = cur.fetchone()

		if branch is not None:

			return branch[0]

	except:
		return False

	return False



def convert_uni(data):

	if isinstance(data, basestring):

		return str(data)

	elif isinstance(data, collections.Mapping):

		return dict(map(convert_uni, data.iteritems()))

	elif isinstance(data, collections.Iterable):

		return type(data)(map(convert_uni, data))

	else:

		return data



def missing_columns(row):

	#{'branch':'', data':[{'old_state':'', 'new_state':'', 'primary_key':'', 'meta':''}]}

	if not 'meta' in row:

		row['meta'] = ''

	row['new_state'] = json.dumps(row['new_state'], ensure_ascii=False)

	row['old_state'] = json.dumps(row['old_state'], ensure_ascii=False)

	row['meta'] = json.dumps(row['meta'], ensure_ascii=False)

	row['created_at'] = datetime.datetime.now()

	return row



def ensure_branch_id(conn, tree_name, branch_identifier):

	cur = conn.cursor()

	#fix for parameters coming in as strings 

	try:

		branch_identifier.isdigit()

		branch_identifier = int(branch_identifier)

	except:

		pass



	#Is the identifier a number?

	if isinstance( branch_identifier, ( int, long ) ):

		#Is there a branch with that id number?

		cur.execute("select id, branch_name from exlayer_branches where tree_name=%s AND id=%s", (tree_name, branch_identifier))

		branch = cur.fetchone() 

		if branch is not None:

			return (int(branch[0]), branch[1])



	#Get the branch_id of the branch with name = identifier

	cur.execute("select id, branch_name from exlayer_branches where tree_name=%s AND branch_name = %s", (tree_name, str(branch_identifier)))

	branch = cur.fetchone()

	if branch is not None:

		return (branch[0], branch[1])

	return (False, False)



def missing_columns_no_encoding(row):

	#{'branch':'', data':[{'old_state':'', 'new_state':'', 'primary_key':'', 'meta':''}]}

	if not 'meta' in row:

		row['meta'] = ''

	row['created_at'] = str(datetime.datetime.now())

	row['id'] = str(row['id'])

	return row



def pretty_return(row):

	row['new_state'] = json.loads(row['new_state'])

	row['old_state'] = json.loads(row['old_state'])

	row['meta'] = json.loads(row['meta'])

	return row

