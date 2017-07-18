from crawler_lib import *
import urllib
import urllib2
import re
import json
import time
import sys
import signal

def get_fork_info(url): #returns parent's name and owner of forked repository
	repoinfo=do_req(url)[0]
	if repoinfo==[]:
		return ()
	return (repoinfo[u'parent'][u'full_name'], repoinfo[u'parent'][u'owner'][u'login'])

def get_orgs(results,url,orgs):
	for org in results:
			orgs.append(org)

def update_orgs(url,orgs): #get all organizations that the user is a public member of
	get_api_pages(url,get_orgs(,orgs))
	return orgs

def update_collected_repos(results, url, checked_repos):
	for res in results:
		if not(res[u'commits_url'][:-6] in checked_repos):
			if(res[u'fork']==False): #gets repo_link, owner, and if its a fork, fork count
				repos.append((res[u'commits_url'][:-6],res[u'owner'][u'login'],res[u'fork'],res[u'forks_count']))
			else: #gets repo_link, owner, if its a fork, fork count and parentinfo
				repos.append((res[u'commits_url'][:-6],res[u'owner'][u'login'],res[u'fork'],res[u'forks_count'])+get_fork_info(res[u'url']))
			checked_repos.add(res[u'commits_url'][:-6])
		else:
			print "repeated", res[u'commits_url'][:-6]

def collect_repos(url, repos,checked_repos): #collect the repositories of a member or organization (stored in repos)
	get_api_pages(url,update_collected_repos,(checked_repos,))


def write_repo_commits(commits,url, fcommit,users,allusers):
	for commit in commits:  #writes commit
		s=repo+"\t"+commit[u'commit'][u'author'][u'name']+"\t"+commit[u'commit'][u'author'][u'email']+"\t"+commit[u'commit'][u'author'][u'date']

		if commit[u'author']!=None and (u'id' in commit[u'author']): #adds authors
			s+="\t"+str(commit[u'author'][u'id'])
			if commit[u'author'][u'login'] not in allusers:
				users.append(commit[u'author'][u'login'])
				allusers.add(commit[u'author'][u'login'])

		s+="\n"
		fcommit.write(s.encode('utf-8'))

def collect_commits_from_repo(req,repo,users,allusers,fcommit): #writes commits from repo 'repo' into file 'fcommit'
	get_api_pages(repo,write_repo_commits,(fcommit,users,allusers))

def recover_from_fail():
	allusers=set()
	checked_repos=set()
	commits=""
	events=""
	flist=open("userlist.txt","r")
	currentuser=flist.readline().strip("\n").strip("\r")
	users=eval(flist.readline().strip("\n").strip("\r"))

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
		orgs=[]	
		update_orgs(url,orgs)

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