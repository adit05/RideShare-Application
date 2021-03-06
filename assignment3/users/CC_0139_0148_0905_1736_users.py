import os
import re
import ast
import requests
import json
import csv
import collections
from flask_api import status
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, DateTime
from flask_marshmallow import Marshmallow
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from flask import Flask, jsonify, request, abort,redirect, url_for, session
from flask import Flask, request, jsonify,Response
from sqlalchemy import and_, or_, not_
from sqlalchemy import update


app=Flask(__name__)
basedir= os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(basedir,'db.sqlite1')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False 
db = SQLAlchemy(app)
ma=Marshmallow(app)

Area = []
f = open('AreaNameEnum.csv')
try:
    enum = csv.reader(f)
    next(f)     # Skip the first 'title' row.
    for row in enum:
    	a = [int(row[0]),row[1]]
    	Area.append(a)
   
finally:
    # Close files and exit cleanly
    f.close()

class User(db.Model):
	__tablename__ ='User'
	id = db.Column(db.Integer,primary_key=True)
	username=db.Column(db.String(25),unique=True)
	password=db.Column(db.String(40),unique=True)

	def __init__(self,username,password):
		self.username=username
		self.password=password

class UserSchema(ma.Schema):
	class Meta:
		fields=('id','username','password')

user_schema=UserSchema()
users_schema=UserSchema(many=True)
'''
class Ride(db.Model):
	__tablename__='Ride'
	rideId = db.Column(db.Integer,primary_key=True)
	created_by=db.Column(db.String(25))
	source=db.Column(db.String(50))
	destination=db.Column(db.String(50))
	timestamp=db.Column(db.String(50))
	users=db.Column(db.String(500))

	def __init__(self,created_by,timestamp,source,destination,users):
		self.created_by=created_by
		self.timestamp=timestamp
		self.source=source
		self.destination=destination
		
		self.users=users

class RideSchema(ma.Schema):
	class Meta:
		fields=('rideId','created_by','timestamp','source','destination','users')

ride_schema=RideSchema()
rides_schema=RideSchema(many=True)
'''
# 1. ADD USER API- working perfectly
@app.route('/api/v1/users',methods=['PUT'])
def addUser():
	x = requests.post('http://localhost:80/api/v1/_count1',json={"type":"api"})
	if request.method=='PUT':
		username=request.json['username']
		password=request.json['password']
		Exists = db.session.query(User).filter_by(username=username)

		if (Exists.scalar() is not None ):
			return Response(status=400)
		else:
			length = len(password)
			if (length == 40):
				reg = r'[0-9a-fA-F]+'
				m = re.match(reg,password)
				if not m:
					return Response(status=400)
				data={"table" : "User" , "method":"put","username":username,"password":password}
				response=(requests.post('http://localhost:80/api/v1/db/write',json=data))
				return Response(status=201)
			else:
				return Response(status=400)
	else:
		return Response(status=405)


# 2. DELETE USER- working perfectly
@app.route('/api/v1/users/<username>',methods=['DELETE'])
def deleteUser(username):
	x = requests.post('http://localhost:80/api/v1/_count1',json={"type":"api"})
	if request.method=='DELETE':
		Exists = db.session.query(User).filter_by(username=username)
		if (Exists.scalar() is not None):
			data={"table":"User","method":"delete","username":username}
			print(data)
			response=(requests.post('http://localhost:80/api/v1/db/write',json=data))
			return Response(status=200)
		else:
			return Response(status=400)
	else:
		return Response(status=405)


# 8. Write to db
@app.route('/api/v1/db/write',methods=['POST'])
def writetodb():
	req=request.get_json()
	table=req['table']
	method=req['method']
	if (table=="Ride" and method=="post"):
		created_by=req['created_by']
		timestamp=req['timestamp']
		source=req['source']
		destination=req['destination']
		users=req['users']
		newRide=Ride(created_by,timestamp,source,destination,users)
		db.session.add(newRide)
		db.session.commit()
		return Response(status=201)
	elif (table=="User" and method=="put"):
		username=req['username']
		password=req['password']
	
		newUser=User(username,password)
		db.session.add(newUser)
		db.session.commit()
		return Response(status=201)

	elif (table=="User" and method=="delete"):
		#print("hi")
		username=req['username']
		user = User.query.filter_by(username=username).first_or_404()
		#print("######################"+str(user))
		#ri=User.query.get(user)
		db.session.delete(user)
		db.session.commit()
		return Response(status=200)
	
		
	elif(table=="Ride" and method=="delete"):
		ride_Id=req['rideId']
		ri=Ride.query.get(ride_Id)
		db.session.delete(ri)
		db.session.commit()
		#return user_schema.jsonify()
		return Response(status=200)
		

	


# 9. Read db
@app.route('/api/v1/db/read',methods=['POST'])
def Read():
	table = request.json['table']
	where = request.json['where']
	length = len(where)
	if (table=="Ride" and length==1):
		rideId = where[0]
		details = db.session.query(Ride).filter_by(rideId=rideId)
		rideId = details.rideId
		created_by = details.created_by
		users = details.users
		timestamp = details.timestamp
		source = details.source
		destination = details.destination
		users = users.split(';')
		result = {"rideId":rideId,"created_by":created_by,"users": users,"timestamp":timestamp,"source":source,"destination":destination}
		return result
	elif (table=="Ride" and length==2):
		source=where[0]
		destination=where[1]
		upcoming = db.session.query(Ride).filter_by(and_(source=source,destination=destination))
		result = []
		for i in upcoming:
			rideId = i.rideId
			username=i.username
			timestamp=i.timestamp
			up = {"rideId":rideId,"username":username,"timestamp":timestamp}
			result.append(up)
		return result
	elif (table=="User"):
		all_users=User.query.all()
		result=users_schema.dump(all_users)
		return jsonify(result)


# assignment 2- list users -working perfectly
@app.route('/api/v1/users', methods = ['GET'])
def usernameDisplay():
	x = requests.post('http://localhost:80/api/v1/_count1', json={"type":"api"})
	if request.method=='GET':
		users=[]
		all_users=User.query.all()
		result=users_schema.dump(all_users)
		print(result)
		#return jsonify(result)
		if(len(result) is not None):
			
			for i in result:
				a=i['username']
				users.append(a)
			print(users)

			#print(result)
			return jsonify(users)

		else:
			return Response(status=204)
	
				
		
	else:
		return Response(status=405)

#assignment 2- clear db
@app.route('/api/v1/db/clear',methods=['POST'])
def clearDb():
	x = requests.post('http://localhost:80/api/v1/_count1',json={"type":"api"})
	if request.method=='POST':
		
		for c in db.session.query(User):
			db.session.delete(c)
				
		db.session.flush()
		db.session.commit()
		
		return Response(status=200)
	else:
		return Response(status=405)

#EXTRA APIS TO CHECK WORKING

@app.route('/api/v1/_count1',methods=['POST'])
def httprequests1():
	
		req = request.get_json()
		print(req)
		type1 = req["type"]
		
		
		f=open("count2.txt","r")
		count=f.read()
		f.close()
		print(count)
		count=int(count)+1
		
		f=open("count2.txt","w").close()
		f=open("count2.txt","w")
		f.write(str(count))
		f.close()
		return Response(status=200)

@app.route('/api/v1/_count',methods=['GET'])
def httprequests():
	if request.method=="GET":
		f=open("count2.txt","r")
		count=f.read()
		f.close()
		c=[]
		c.append(int(count))
		return jsonify(c)
	else:
		return Response(status=405)

@app.route('/api/v1/_count',methods=['DELETE'])
def httprequestsdel():
	if request.method=="DELETE":
		
		
		f=open("count2.txt","w").close()
		f=open("count2.txt","w")
		f.write("0")
		f.close()
		return Response(status=200)
	else:
		return Response(status=405)


if __name__=='__main__':
	app.run(debug=True,host="0.0.0.0",port=80)