layer
=====

a RESTful webservice for data version control. Written in python, using Flask and Twilio's API framework

Requirements
-------------
Layer is built to run on top of Postgres 9.3.

Configuration
-------------
Change the settings in config.sample and rename to config.py. Once running on your Flask server of choice, pointing the browser to http://localhost:1337/ will setup the basic tables Layer needs.

Interacting with Layer
----------------------
Any data sent to Layer should be sent as valid JSON in the body of the request.

Meta Data
---------
All Layer tables have a column for meta data. This allows you to store whatever extra information about the trees, branches, or transactions your applications might need. Meta data can include commit messages, id numbers of users or computers that made the change, the time of the change, etc.

Layer does not at this time allow you to query inside meta data columns.

Creating a Tree
---------------
Like git, each data project has it's own tree in which changes are tracked. Unlike git, the developer has much more control over what is worth generating a new tree for. For example, Layer can be set up to track each table in a database as its own tree, or all changes to the database can lumped into one tree and each table registered as a specific branch.

Layer will generate two tables for each tree, one for individual changes to the data (lines), one for bulk transactions (bulk). Branches, on the other hand, are registered in the exlayer_branches table. Layer can support millions of branches, but not millions of trees.

To create a tree send the following POST request

> curl -H "Content-Type: application/json" --data 
> '{"name":"my_tree","meta":{"description":"This is a 
> tree","owner":"me"}}' http://localhost:1337/create/

Registering a Change
--------------------

> curl -H "Content-Type: application/json" --data '{"branch":11, 
> "data": [{"old_state":{"name": "test"}, "new_state": {"name": 
> "tester"}, "primary_key":1, "meta":{}}]}'
> http://localhost:1337/my_tree/

Changes in layer are stored in tables with the following schema:

id | branch_id | old_state | new_state | primary_key | meta | created_at
--:|:---------:|:---------:|:---------:|:-----------:|:----:|:----------

branch_id: id of the branch
old_state: the data before the change
new_state: the current state of the data
primary_key: the information which identifies this specific piece of data in the data store being version controlled. For a traditional database this might be a uuid or an integer row number. For Google Docs this might be a row/column assignment.
meta: any meta data to store along side the change
created_at: self explanatory :)

When adding data to layer you can use either the branch id or the branch name. If no branch is specified, layer will add the data to the most recent branch for that tree. If no old_state is provided layer will lookup the last state in that branch with that primary key and automatically assign that as the old_state. If no old records for that primary key are found layer will insert a blank object.

Bulk Transactions
-----------------
Bulk transactions are registered automatically when data is pushed to layer. However, you can turn them off by setting bulk to false like so:

> curl -H "Content-Type: application/json" --data '{"branch":11, "bulk":0, 
> "data": [{"old_state":{"name": "test"}, "new_state": {"name": 
> "tester"}, "primary_key":1, "meta":{}}]}'
> http://localhost:1337/my_tree/ 

You can store meta data for bulk transaction (for example, a commit message explaining the nature of the changes) by adding a meta parameter like so:

> curl -H "Content-Type: application/json" --data '{"branch":11, 
> "meta": {"commit_message": "Hey this is a commit message"}
> "data": [{"old_state":{"name": "test"}, "new_state": {"name": 
> "tester"}, "primary_key":1, "meta":{}}]}'
> http://localhost:1337/my_tree/

Creating and Using Branches
---------------------------
Layer automatically creates a master branch for each new tree. To create additional branches run the following request:

> curl -H "Content-Type: application/json" --data '{"branch_name":
> "my_branch","meta":{}}]}' http://localhost:1337/my_tree/branch/

Layer will return the id number of the newly created branch.

Like git, branches allow you to track changes to different versions of the same data.

Accessing Commit Information
----------------------------
Data can be pulled from the tree or from individual branches. Layer will return all the bulk transactions, and the 200 most recent line changes.

To pull information from the tree run this request:

> curl http://localhost:1337/my_tree/

To pull information from a specific branch you would run the following request:

> curl http://localhost:1337/my_tree/branch/my_branch/

Pulling the Details of Transactions
-----------------------------------
Getting details of a bulk

> curl http://localhost:1337/my_tree/bulk/[id]/

Getting details of an individual line

> curl http://localhost:1337/exversion/line/[id]/

Deleting Changes
----------------
If for some reason to want to remove changes layer has record you can do so with the following request:

> curl -X DELETE http://locahost:1337/my_tree/line/[id]/

or:

> curl -X DELETE http://locahost:1337/my_tree/bulk/[id/

Deleting a Tree
---------------
To delete a whole tree:

> curl -X DELETE http://locahost:1337/my_tree/

Layer will automatically backup all tree information before deleting. The backup files can be found in the backup folder in the src directory.


ToDos
-----
- Add support for changes to schema
- Add pagination to getting changes
- Add deletes for full branches

