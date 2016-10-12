import urllib
import urllib2
import re
import json
import time

tokenf=open("token.txt")
token=tokenf.read()
tokenf.close()

def create_req(url):
	req=urllib2.Request(url)
	req.add_header("Authorization","token "+token)
	return req

def do_req(url):
	response=urllib2.urlopen(create_req(url))
	return json.loads(response.read())


def collect_repos(results, repos,checked_repos):
	for res in results:
		if not(res[u'id'] in checked_repos):
			repos.append(res[u'commits_url'][:-6])
			checked_repos.add(res[u'id'])

users = ["guilhermeresende"]
f=open("commits.txt","w")
commitsha = set()
checked_repos=set()
numreqs=0

wth_author=0
wthout_author=0

start = time.time()
for user in users:
	repos=[]
	url="https://api.github.com/users/"+user+"/repos"
	
	results=do_req(url)
	numreqs+=1 

	collect_repos(results,repos,checked_repos)

	url="https://api.github.com/users/"+user+"/orgs"	
	results=do_req(url)
	numreqs+=1

	for org in results:
		url=org[u'repos_url']
		results=do_req(url)
		numreqs+=1
		collect_repos(results,repos,checked_repos)

	for repo in repos:		
		print repo		
		req=create_req(repo)
		numreqs+=1 #TESTE

		try:
			response=urllib2.urlopen(req)
			link=response.info().getheader('Link')

			if(link==None): #find number of pages
				last=1
			else:
				m = re.search('rel="next",(.*)page=(\d+)>; rel="last"',link)
				last=int(m.group(2))

			currentpage=1
			while(True): #Collect all repository commit pages
				commits=json.loads(response.read())	
				for commit in commits:
					if not commit[u'sha'] in commitsha: #writes commit
						s=repo+"\t"+commit[u'commit'][u'author'][u'email']+"\t"+commit[u'commit'][u'author'][u'date']+"\n"
						commitsha.add(commit[u'sha'])
						f.write(s)

						if commit[u'committer']!=None: #adds authors
							if commit[u'committer'][u'login'] not in users:
								users.append(commit[u'committer'][u'login'])
							wth_author+=1
						else:
							wthout_author+=1

				if(currentpage==last):
					break
				else:
					currentpage+=1
					url=repo+"?page="+str(currentpage)
					print url
					response=urllib2.urlopen(create_req(url))
					numreqs+=1 #TESTE
				
		except urllib2.URLError as e:
			if(e.reason=="Conflict"):
				print "empty repository"
			else:
				raise

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
	print float(wth_author)/(wth_author+wthout_author)

f.close()