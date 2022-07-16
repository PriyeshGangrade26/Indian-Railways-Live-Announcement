import json
import requests
from json2html import *
import traceback
api_key='KUIOTCFW***********'
def get_response_from_IndianRailways(messaging_text):
	try:
		IndianRailwaysurl='https://api.railwayapi.com/v2/platform-status/platform/%s/apikey/%s' %(messaging_text,api_key)
		resp_str=requests.get(IndianRailwaysurl)
		resp_dict = json.loads(resp_str.text)
		print(resp_dict)
		passenger=[]
		total_passengers=resp_dict.get('total_passengers')
		from_station=resp_dict.get('from_station').get('name')
		train_number=resp_dict.get('train').get('number')
		train_name=resp_dict.get('train').get('name')
		platform=resp_dict.get('platform')
		doj=resp_dict.get('doj')
		response_code=resp_dict.get('response_code')
		chart_prepared=resp_dict.get('chart_prepared')
		if chart_prepared=='True':
			chart_prepared='Yes'
		else:
			chart_prepared='No'	
		to_station=resp_dict.get('to_station').get('name')
		journey_class=resp_dict.get('journey_class').get('code')
		passengers=resp_dict.get('passengers')
		print(resp_dict.get('chart_prepared'))
		if response_code==200:
			for i in range(len(passengers)):
				booking_status=resp_dict.get('passengers')[i].get('booking_status')
				passenger.append(booking_status)
				print(passenger)
			final_str="platform : "+str(platform)+"\nTrain Name : "+train_name+"\nTrain Number : "+str(train_number)+"\nDate of Journey : "+str(doj)+\
					"\nBoarding_Point : "+from_station+"\nReservation Upto : "+to_station+"\nTotal Passengers : "+str(total_passengers)+\
					"\nReservation Class : "+journey_class + "\nChart Prepared : "+str(chart_prepared)
			print(final_str)
			return final_str,passenger
		else:
			return 'none','none'
	except Exception as ex:
			print ("get_response_from_IndianRailways exception "+str(ex))
			print("There is an exception from function " + str(traceback.extract_stack(None, 2)[0][2]))