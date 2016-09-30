import urllib
import urllib2
import re
import json

users = ["guilhermeresende"]
token="8598d7eb9235997676760e8695c3951a2a9c31b7"
for user in users:
	repos=[]
	url="https://api.github.com/users/"+user+"/repos"
	req=urllib2.Request(url)
	req.add_header("Authorization","token "+token)
	response=urllib2.urlopen(req)

	results= json.loads(response.read())
	for i in results:
		repos.append(i[u'commits_url'][:-6])
	for repo in repos:
		print repo
		req=urllib2.Request(repo)
		req.add_header("Authorization","token "+token)
		try:
			response=urllib2.urlopen(req)
			link=response.info().getheader('Link')
			if(link==None):
				last=1
			else:
				m = re.search('rel="next",(.*)page=(\d+)>; rel="last"',link)
				last=int(m.group(2))

			currentpage=1
			author_list=[]
			numcommits=0
			while(True):
				l=response.read()
				#print "read response"
				commits=json.loads(l)
				#print "json loaded"	
				numcommits+=len(commits)	
				for commit in commits:				
					f=open("exit.txt","a")
					f.write(str(commit)+"\n")
					f.close()
					author_list.append(commit[u'commit'][u'author'][u'email'])
				#print "analyzed"
				if(currentpage==last):
					break
				else:
					currentpage+=1
					url=repo+"?page="+str(currentpage)
					req=urllib2.Request(url)
					print url
					req.add_header("Authorization","token "+token)
					response=urllib2.urlopen(req)
					#print "got response"
		except urllib2.URLError as e:
			if(e.reason=="Conflict"):
				print "empty repository"
				numcommits=0
				author_list=[]
			else:
				raise

		print "number of commits:",numcommits,"different authors:",len(set(author_list))