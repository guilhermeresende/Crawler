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
numreqs=0

def handler(signum, frame):
    print 'Signal handler called (reading took too long)'
    raise IOError("Couldn't read page!")

def create_req(url):
	global numreqs
	req=urllib2.Request(url)
	req.add_header("Authorization","token "+token)
	numreqs+=1
	return req

def do_req(url):
	try:
		response=urllib2.urlopen(create_req(url))
	except urllib2.HTTPError as e:
		if e.code == 451:
			print "Page not allowed"
			return json.loads("[]")
		elif e.code == 404:
			print "page not found"
			return json.loads("[]")
		elif e.code == 403:
			print "page forbidden"
			return json.loads("[]")
		else:
			raise
	return json.loads(response.read())

def get_fork_info(url):
	repoinfo=do_req(url)
	if repoinfo==[]:
		return ()
	return (repoinfo[u'parent'][u'full_name'], repoinfo[u'parent'][u'owner'][u'login'])

def get_orgs(url):
	req=create_req(url)
	response=urllib2.urlopen(req)
	
	last = get_num_pages(response.info().getheader('Link'))
	currentpage=1
	orgs=[]
	while(True):
		results=json.loads(response.read())
		for org in results:
			orgs.append(org)
		if(currentpage==last):
			break
		else:
			currentpage+=1
			newurl=url+"?page="+str(currentpage)
			response=urllib2.urlopen(create_req(newurl))
	return orgs

def collect_repos(url, repos,checked_repos):
	req=create_req(url)
	response=urllib2.urlopen(req)
	
	last = get_num_pages(response.info().getheader('Link'))
	currentpage=1
	while(True):
		results=json.loads(response.read())
		for res in results:
			if not(res[u'commits_url'][:-6] in checked_repos):
				if(res[u'fork']==False): #gets repo_link, owner, and if its a fork, fork count
					repos.append((res[u'commits_url'][:-6],res[u'owner'][u'login'],res[u'fork'],res[u'forks_count']))
				else: #gets repo_link, owner, if its a fork, fork count and parentinfo
					repos.append((res[u'commits_url'][:-6],res[u'owner'][u'login'],res[u'fork'],res[u'forks_count'])+get_fork_info(res[u'url']))
				checked_repos.add(res[u'commits_url'][:-6])
			else:
				print "repeated", res[u'commits_url'][:-6]
		if(currentpage==last):
			break
		else:
			currentpage+=1
			newurl=url+"?page="+str(currentpage)
			response=urllib2.urlopen(create_req(newurl))

def get_num_pages(link):
	if(link==None): #find number of pages
		return 1
	else:
		m = re.search('rel="next",(.*)page=(\d+)>; rel="last"',link)
		return int(m.group(2))

def get_commits_from_push(results):
	s=""
	for res in results[u'commits']:
		s+="commits"+"\t"+res[u'url']+"\t"+res[u'author'][u'email']+"\t"+res[u'author'][u'name']+"\n"
	return s

def get_user_info(user):
	url="https://api.github.com/users/"+user+"/events"
	print url
	req=create_req(url)
	response=urllib2.urlopen(req)
	
	last = get_num_pages(response.info().getheader('Link'))

	s=""
	currentpage=1
	while(True):
		results=json.loads(response.read())
		
		for res in results:
			s+=user+"\t"+res[u'id']+"\t"+res[u'type']+"\t"+res[u'created_at']+"\n"
			#fuser.write(s)

			if res[u'type']=='PushEvent':
				s+=get_commits_from_push(res[u'payload'])

		if(currentpage==last):
			break
		else:
			currentpage+=1
			newurl=url+"?page="+str(currentpage)
			response=urllib2.urlopen(create_req(newurl))
	return s

def collect_commits_from_repo(req,repo,users,allusers,fcommit):
	try:
		response=urllib2.urlopen(req)
	except urllib2.HTTPError as e:
		if e.code == 451:
			print "page not allowed"
			return
		elif e.code == 404:
			print "page not found"
			return
		elif e.code == 403:
			print "page forbidden"
			return
		else:
			raise
	last = get_num_pages(response.info().getheader('Link'))	

	commits=json.loads(response.read())	
	currentpage=1
	while(True): #Collect all repository commit pages

		for commit in commits:  #writes commit
			s=repo+"\t"+commit[u'commit'][u'author'][u'name']+"\t"+commit[u'commit'][u'author'][u'email']+"\t"+commit[u'commit'][u'author'][u'date']

			if commit[u'author']!=None and (u'id' in commit[u'author']): #adds authors
				s+="\t"+str(commit[u'author'][u'id'])
				if commit[u'author'][u'login'] not in allusers:
					users.append(commit[u'author'][u'login'])
					allusers.add(commit[u'author'][u'login'])

			s+="\n"
			fcommit.write(s.encode('utf-8'))
		if(currentpage==last):
			break
		else:
			currentpage+=1
			url=repo+"?page="+str(currentpage)
			print url, last
			
			'''Tries to read page untill it works'''
			signal.signal(signal.SIGALRM, handler)
			signal.alarm(10) 
			readdone=1
			while(readdone):
				try:
					readdone=0
					response=urllib2.urlopen(create_req(url))					
					commits=json.loads(response.read())	
				except:
					readdone=1
					signal.alarm(10)
			signal.alarm(0)

def recover_from_fail():
	allusers=set()
	checked_repos=set()
	commits=""
	events=""
	flist=open("userlist.txt","r")
	currentuser=flist.readline().strip("\n").strip("\r")
	users=eval(flist.readline().strip("\n").strip("\r"))
	#allusers=eval(flist.readline().strip("\n").strip("\r"))
	#checked_repos=eval(flist.readline().strip("\n").strip("\r"))

	current_repo='https://api.github.com/repos/mozilla/gecko-dev/commits'
	fcommit = open("commits.txt","r+")
	fuser=open("events.txt","r")

	commitlines = fcommit.readlines()
	fcommit.seek(0)
	
	for line in commitlines:
		fields=line.strip("\n").strip("\r").split("\t")
		if fields[2]!=currentuser:
			fcommit.write(line)
		else:
			break
		if fields[0]=="repo_info:":
			if not(fields[2] in allusers):
				allusers.add(fields[2])
			if not(fields[1] in checked_repos):
				checked_repos.add(fields[1])		
	fcommit.truncate()
	for line in fuser:
		fields=line.strip("\n").strip("\r").split("\t")
		if fields[0]==currentuser:
			break
		events+=line

	#for user in users:
	#	allusers.add(user)
	fcommit.close()
	fuser.close()
	flist.close()
	return (currentuser,users,events,allusers,checked_repos)

def main():
	global numreqs
	if len(sys.argv)>1 and sys.argv[1]=='--restart': 	#start collecting from beginning
		users = ["guilhermeresende"]
		allusers=set()
		checked_repos=set()
		allusers.add("guilhermeresende")
		fcommit=open("commits.txt","w")
		fuser=open("events.txt","w")	
	else: 												#start from last user
		print "Recovering from last restart" 
		(currentuser,users,events,allusers,checked_repos)=recover_from_fail()
		fcommit=open("commits.txt","a+")
		fcommit.seek(0,2)
		fuser=open("events.txt","w")
		#fcommit.write(commits)
		fuser.write(events)
		frst=users.index(currentuser)
		users=users[frst:]

	start = time.time()
	for user in users:
		print "User", user
		flist=open("userlist.txt","w")
		flist.write(user+"\n"+str(users)+"\n"+str(allusers)+"\n"+str(checked_repos))
		flist.close()
		repos=[]
		url="https://api.github.com/users/"+user+"/repos"	

		collect_repos(url,repos,checked_repos)

		url="https://api.github.com/users/"+user+"/orgs"	
		orgs=get_orgs(url)

		for org in orgs:
			url=org[u'repos_url']
			collect_repos(url,repos,checked_repos)	

		for repoinfo in repos:
			repo=repoinfo[0]
			print repo

			written_repoinfo="\t".join([str(partinfo).encode('utf-8') for partinfo in repoinfo])
			fcommit.write("repo_info:\t"+written_repoinfo+"\n")
					
			req=create_req(repo)
			
			try:
				collect_commits_from_repo(req,repo,users,allusers,fcommit)
			except urllib2.URLError as e:
				if(e.reason=="Conflict"):
					print "empty repository"
				else:
					raise

			#controls for request limit
			end = time.time()
			time_dif=(end-start)
			'''if(time_dif>3600 and numreqs<=4999):
				numreqs=0
				start=time.time()
			elif(time_dif>3600 and numreqs>4999): 
				print "WAIT FOR REQ LIMIT",3600-time_dif
				time.sleep(3600-time_dif)
				numreqs=0
				start=time.time()'''

		print "Reqs and time", numreqs, time_dif, numreqs/time_dif

	f.close()
	fuser.close()

if __name__ == "__main__":
    main()