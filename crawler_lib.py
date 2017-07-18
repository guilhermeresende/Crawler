import urllib
import urllib2
import re
import json
import time
import sys
import signal

tokenf=open("token.txt")
token=tokenf.read()
tokenf.close()

def handler(signum, frame):
    print 'Signal handler called (reading took too long)'
    raise IOError("Couldn't read page!")

def create_req(url):
	req=urllib2.Request(url)
	req.add_header("Authorization","token "+token)
	return req

def get_num_pages(link): #get the total number of pages containing the information requested
	if(link==None):
		return 1
	else:
		m = re.search('rel="next",(.*)page=(\d+)>; rel="last"',link)
		return int(m.group(2))

def do_req(url): #makes req, return response and number of pages
	try:
		response=urllib2.urlopen(create_req(url))
	except urllib2.HTTPError as e:
		if e.code == 451:
			print "Page not allowed"
			return (json.loads("[]"),-2)
		elif e.code == 404:
			print "Page not found"
			return (json.loads("[]"),-1)
		elif e.code == 403:
			print "Page forbidden"
			return (json.loads("[]"),-2)
		elif e.code == 409:
			print "Empty Repository"
			return (json.loads("[]"),0)
	last = get_num_pages(response.info().getheader('Link'))	
	return (json.loads(response.read()),last)


def get_api_pages(url, write_result_func, params):
	(results,last)=do_req(url)	
	currentpage=1
	while(True): #Collect all repository commit pages
		if(write_result_func(results,url,*params))==-1:
			return

		if(currentpage>=last):
			break
		else:
			currentpage+=1
			url=url.split('?page')[0]+"?page="+str(currentpage)
			print url, last
			
			'''Tries to read page untill it works'''
			signal.signal(signal.SIGALRM, handler)
			signal.alarm(15) 
			readdone=1
			while(readdone):
				try:
					readdone=0				
					response=urllib2.urlopen(create_req(url))					
					results=json.loads(response.read())
				except:
					readdone=1
					signal.alarm(15)
			signal.alarm(0)
#cd /cygdrive/c/Users/Guilherme/Documents/GitHub/Crawler/
