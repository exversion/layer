from flask import Flask
from flask.ext.testing import TestCase
from src import app as layer
from src import helper
from config import config
import json

class TestTree(TestCase):

	def create_app(self):
		app = layer.create_app()
		app.config['TESTING'] = True
		return app

	def test_valid_tree_name_good(self):
		valid = helper.valid_tree_name('test')
		assert valid == 'test'

	def test_valid_tree_name_bad1(self):
		valid = helper.valid_tree_name('test 1')
		assert valid == 'test_1'

	def test_valid_tree_name_bad2(self):
		valid = helper.valid_tree_name('test!')
		assert valid == 'test'

	def test_valid_tree_name_bad3(self):
		valid = helper.valid_tree_name('test__2')
		assert valid == 'test_2'

	def test_valid_tree_name_bad4(self):
		valid = helper.valid_tree_name('exlayer_branches')
		assert valid == False

	def test_valid_tree_name_bad5(self):
		valid = helper.valid_tree_name('')
		assert valid == False

	def test_valid_tree_name_bad6(self):
		valid = helper.valid_tree_name(None)
		assert valid == False

	def test_valid_tree_name_bad7(self):
		valid = helper.valid_tree_name(' test ')
		assert valid == 'test'

	def test_valid_tree_name_bad8(self):
		valid = helper.valid_tree_name('TEST')
		assert valid == 'test'

	def test_valid_tree_name_bad9(self):
		valid = helper.valid_tree_name('test#')
		assert valid == 'testnum'

	def test_tree_exists1(self):
		conn = helper.setConnection()
		exists = helper.tree_exists(conn, 'test')
		assert exists == True

	def test_tree_exists2(self):
		conn = helper.setConnection()
		exists = helper.tree_exists(conn, 'exlayer_test_fail')
		assert exists == False

	def test_dump_command(self):
		command = helper.dump_command('test', 'test.sql')
		assert command == 'export PGPASSWORD='+config.DBPASSWORD+'\npg_dump '+config.DBNAME+' -t test_line -t test_bulk -h '+config.DATABASE_HOST+' --username='+config.DBUSER+' -f test.sql'

	def test_pretty_return(self):
		command = helper.pretty_return({'old_state':json.dumps('{"test":"Is this a test?"}', ensure_ascii=False), 'new_state':json.dumps('{"test":"Yes it is"}', ensure_ascii=False), 'meta':json.dumps('{"test":Yay"}', ensure_ascii=False)})
		print command
		assert command == {'new_state':'{"test":"Is this a test?"}','old_state':'{"test":"Yes it is"}','meta':'{"test":Yay"}'}
	#def test_creation(self):
	#	response = self.client.post('/create/', data=dict(tree_name='test'))
	#	self.assertEquals(response.json, dict(success=True, tree_name='test'))