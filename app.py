import numpy as np
from sklearn.linear_model import LogisticRegression
import dill as dl
from flask import Flask, request, jsonify, render_template
import pickle
import pandas as pd
import lime
import lime.lime_tabular
import pyrebase
from datetime import datetime
from pytz import timezone

app = Flask(__name__)

config = {
    "apiKey": "AIzaSyC3BCU_3v_kFnQp-lt60vvrU5fYlJnIm4Q",
    "authDomain": "feedback-beb57.firebaseapp.com",
    "databaseURL": "https://feedback-beb57.firebaseio.com",
    "projectId": "feedback-beb57",
    "storageBucket": "feedback-beb57.appspot.com",
    "messagingSenderId": "211570371404",
    "appId": "1:211570371404:web:f781b483e59e428bc4fde9"
  	}

firebase = pyrebase.initialize_app(config)

db = firebase.database()

def noquote(s):
    return s
pyrebase.pyrebase.quote = noquote

# timeStamp = datetime.now().astimezone(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")						#converting timestamp into string

@app.route('/tdata/', methods=['GET'])
def predict():
	timeStamp = datetime.now().astimezone(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")						#converting timestamp into string
	air = int(request.args['air'])
	wlev = int(request.args['wlev'])
	hum = int(request.args['hum'])
	wet1 = int(request.args['wet1'])
	wet2 = int(request.args['wet2'])
	temp = int(request.args['temp'])
	
	#data preprocessing	
	air = int(abs(air )/30)
	wlev = abs(50 - wlev)/5
	hum = abs(hum - 60)/4
	temp = int(abs(temp -20)/2)

	# prediction for features
	# pm = pickle.load(open('fmodel', 'rb'))
	# predict_fn = lambda x: pm.predict_proba(x).astype(float) 						#predict function for features. lime
	# t = dl.load(open('explainer','rb'))
	# y = pd.DataFrame([[air,wlev,hum,wet,ldr]])
	# yd = y.values																	#loading the pre-trained explorer
	# exp = t.explain_instance(yd[0], predict_fn, num_features=5)						#predicting the features
	
	data = { 'date': timeStamp, 'air': air, 'wlev': wlev, 'hum': hum, 'wet1': wet1, 'wet2': wet2, 'temp': temp }		#data to be pushed
	db.child("ctdata").update(data)													# updating real time data
	db.child("tdata").child(timeStamp).set(data)									#querrrying database to push the data with timestamp as key

	return '''<h1>The feature value is: {}</h1>'''.format(data)

@app.route('/freq/', methods=['GET'])
def freq():
	timeStamp = datetime.now().astimezone(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")						#converting timestamp into string
	cfreq = int(request.args['cfreq'])				#to receive frequency
	db.child("cfreq").update({"cfreq": cfreq})
	db.child("freq").child(timeStamp).set({"date": timeStamp, "freq": cfreq})
	return '''<h1>The feature value is: {}</h1>'''.format(cfreq)

@app.route('/feed/', methods=['GET'])
def feed():
	timeStamp = datetime.now().astimezone(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")						#converting timestamp into string
	feed = int(request.args['feed'])				#to receive feed back
	db.child("freed").child(timeStamp).set({"date": timeStamp, "feed": feed})
	return '''<h1>The feature value is: {}</h1>'''.format(feed)

@app.route('/att/', methods=['GET'])
def att():
	timeStamp = datetime.now().astimezone(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")						#converting timestamp into string
	att = int(request.args['att'])																						#to receive attendance
	if (att == 1):																										# 1 if cleaner is about to clean
		db.child("att").child(timeStamp).set({"date": timeStamp})														# mark the attendance of the cleaner
	elif(att == 0):
		date_res = db.child("att").order_by_key().limit_to_last(1).get()
		for date in date_res.each():
			before_date = date.val()
		bdata = db.child("tdata").order_by_key().end_at(before_date['date']).limit_to_last(1).get()
		
		for data in bdata.each():
			bair = data.val()['air']
			bwlev = data.val()['wlev']

		cdata = db.child("tdata").order_by_key().limit_to_last(1).get()
		for data in cdata.each():
			cair = data.val()['air']
			cwlev = data.val()['wlev']

		if ((int(bair) - int(cair)) < 0 or (int(bwlev) - int(cwlev)) < 0):
			db.child("cqual").child(timeStamp).set({"quality": 0})
		else:
			db.child("cqual").child(timeStamp).set({"quality": 1})

	return '''<h1>The feature value is: {}</h1>'''.format(str(bair) + ", "+ str(cair))


if __name__ == "__main__":
    app.run(debug=True)