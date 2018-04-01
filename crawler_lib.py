#Functions to help crawl pages of github api's response
from time import sleep
import urllib2
import re
import json
import time
import sys
import signal
import socket

tokenf=open("token.txt")
token=tokenf.read()
tokenf.close()

def handler(signum, frame):
    print 'Signal handler called (reading took too long)'
    raise IOError("Couldn't read page!")

def create_req(url,extra_headers=[]):
	req=urllib2.Request(url)
	req.add_header("Authorization","token "+token)
	for header in extra_headers:
		req.add_header(header[0],header[1])
	return req

def get_num_pages(link): #get the total number of pages containing the information requested
	if(link==None):
		return 1
	else:
		m = re.search('rel="next",(.*)\?page=(\d+)(.*)>; rel="last"',link)
		return int(m.group(2))

def do_req(url,extra_headers=[]): #makes req, return response and number of pages, negative number of pages means error
	print url
	try:
		response=urllib2.urlopen(create_req(url,extra_headers))
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
		elif e.code== 500:
			print "Server error"
			return do_req(url)
		else:
			raise
	except socket.error:
		print "Connection reset"
		return do_req(url)
	except urllib2.URLError:
		print "Connection reset"
		return do_req(url)	

	last = get_num_pages(response.info().getheader('Link'))	

	return (json.loads(response.read()),last)

#collect all pages resulted in the url request and sends them to write_result_func
#if you want the get_api_pages to stop crawling after calling write_result_func, pass a function that returns -1 when the crawling should stop
def get_api_pages(url, write_result_func, params,extra_headers=[]): 

	'''Repeats request if server hangs'''
	signal.signal(signal.SIGALRM, handler)
	signal.alarm(15) 
	readdone=1
	while(readdone):
		try:
			readdone=0		
			(results,last)=do_req(url+'?page=1&per_page=100',extra_headers)
		except:
			readdone=1
			signal.alarm(15)
	signal.alarm(0)		
	#	(results,last)=do_req(url)

	currentpage=1
	while(True): #Collect all repository commit pages

		if(write_result_func(results,url,*params))==-1:
			return

		if(currentpage>=last):
			break
		else:
			currentpage+=1
			url=url.split('?page')[0]+"?page="+str(currentpage)+'&per_page=100'
			print url, last
			
			'''Repeats request if server hangs'''
			signal.signal(signal.SIGALRM, handler)
			signal.alarm(15) 
			readdone=1
			while(readdone):
				try:
					readdone=0		
					response=urllib2.urlopen(create_req(url,extra_headers))					
					results=json.loads(response.read())
				except:
					readdone=1
					signal.alarm(15)
			signal.alarm(0)
	falert=open("alerts.txt","a")
	falert.write(url+"\n")
	falert.close()