import urllib
import urllib2
import re
import json
import time
import sys

tokenf=open("token.txt")
token=tokenf.read()
tokenf.close()
numreqs=0

def create_req(url):
	global numreqs
	req=urllib2.Request(url)
	req.add_header("Authorization","token "+token)	
	numreqs+=1
	return req

def do_req(url):
	response=urllib2.urlopen(create_req(url))
	return json.loads(response.read())


def collect_repos(results, repos,checked_repos):
	for res in results:
		if not(res[u'id'] in checked_repos):
			repos.append(res[u'commits_url'][:-6])
			checked_repos.add(res[u'id'])

def get_num_pages(link):
	if(link==None): #find number of pages
		return 1
	else:
		m = re.search('rel="next",(.*)page=(\d+)>; rel="last"',link)
		return int(m.group(2))

def collect_commits_from_push(results,fuser):
	for res in results[u'commits']:
		s="commits"+"\t"+res[u'url']+"\t"+res[u'author'][u'email']+"\t"+res[u'author'][u'name']+"\n"
		fuser.write(s.encode('utf-8'))

def recover_from_fail():
	flist=open("userlist.txt","r")
	currentuser=flist.readline().strip("\n")
	users=eval(flist.readline().strip("\n"))
	f=open("commits.txt","r")
	f2=open("events.txt","r")
	commits=""
	events=""
	for line in f:
		fields=line.strip("\n").split("\t")
		if fields[0]==currentuser:
			break
		commits+=line
	for line in f2:
		fields=line.strip("\n").split("\t")
		if fields[0]==currentuser:
			break
		events+=line
	return (currentuser,users,commits,events)

if(len(sys.argv)>1):
	(currentuser,users,commits,events)=recover_from_fail()
	f=open("commits.txt","w")
	fuser=open("events.txt","w")
	f.write(commits)
	fuser.write(events)
	frst=users.index(currentuser)
	users=users[frst:]
else:
	users = ["guilhermeresende"]
	f=open("commits.txt","w")
	fuser=open("events.txt","w")

checked_repos=set()

wth_author=0
wthout_author=0

start = time.time()
for user in users:
	flist=open("userlist.txt","w")
	flist.write(user+"\n"+str(users))
	flist.close()
	repos=[]
	url="https://api.github.com/users/"+user+"/repos"
	
	results=do_req(url)
	 
	collect_repos(results,repos,checked_repos)

	'''TESTING EVENTS'''
	print "User", user
	url="https://api.github.com/users/"+user+"/events"
	req=create_req(url)
	response=urllib2.urlopen(req)
	
	last = get_num_pages(response.info().getheader('Link'))

	currentpage=1
	while(True):
		results=json.loads(response.read())
		
		for res in results:
			s=user+"\t"+res[u'id']+"\t"+res[u'type']+"\t"+res[u'created_at']+"\n"
			fuser.write(s)

			if res[u'type']=='PushEvent':
				collect_commits_from_push(res[u'payload'],fuser)

		if(currentpage==last):
			break
		else:
			currentpage+=1
			newurl=url+"?page="+str(currentpage)
			response=urllib2.urlopen(create_req(newurl))
	
	'''END TESTING EVENTS'''

	url="https://api.github.com/users/"+user+"/orgs"	
	results=do_req(url)

	
	for org in results:
		url=org[u'repos_url']
		results=do_req(url)
		
		collect_repos(results,repos,checked_repos)

	for repo in repos:		
		print repo		
		req=create_req(repo)
		
		try:
			response=urllib2.urlopen(req)
			
			last = get_num_pages(response.info().getheader('Link'))

			currentpage=1
			while(True): #Collect all repository commit pages
				commits=json.loads(response.read())	
				for commit in commits:  #writes commit
					s=repo+"\t"+commit[u'commit'][u'author'][u'email']+"\t"+commit[u'commit'][u'author'][u'date']

					if commit[u'author']!=None: #adds authors
						s=s+"\t"+str(commit[u'author'][u'id'])
						if commit[u'author'][u'login'] not in users:
							users.append(commit[u'author'][u'login'])
						wth_author+=1
					else:
						wthout_author+=1

					s=s+"\n"
					f.write(s.encode('utf-8'))

				if(currentpage==last):
					break
				else:
					currentpage+=1
					url=repo+"?page="+str(currentpage)
					print url
					response=urllib2.urlopen(create_req(url))
					
				
		except urllib2.URLError as e:
			if(e.reason=="Conflict"):
				print "empty repository"
			else:
				raise

		#controls for request limit
		end = time.time()
		time_dif=(end-start)
		if(time_dif>360):
			numreqs=0
			start=time.time()
		elif(numreqs>=4999): #reached request limit
			print "WAIT FOR REQ LIMIT"
			time.sleep(360-time_dif)
			numreqs=0
			start=time.time()

	print "Proportion with user",float(wth_author)/(wth_author+wthout_author) #number of commits with author
	print "Reqs and time", numreqs, time_dif

f.close()
fuser.close()