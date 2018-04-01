#get starred repositories (at commits.txt)
from crawler_lib import *

def write_num_starred(url,fstarred):
	(result,num_pages)=do_req(url)
	if(num_pages==1): 

		num_starred=result['stargazers_count']
		stargazers_url=result['stargazers_url']

		if num_starred>0:
			fstarred.write(url+" "+str(num_starred)+"\n")
			return stargazers_url
		else:
			return None

	else:
		assert num_pages<=0

def write_starred(starredlist,url,fstarred):
	for starred in starredlist:
		date=starred[u'starred_at']
		user=str(starred[u'user'][u'id'])
		fstarred.write(date+"\t"+user+"\n")

def get_starred(url,fstarred):

	stargazers_url=write_num_starred(url,fstarred)	
	if stargazers_url!=None:
		get_api_pages(stargazers_url,write_starred,(fstarred,),extra_headers=[("Accept","application/vnd.github.v3.star+json")])


fcommit=open("commits.txt","r")

'''RECOVER FILE
fstarred=open("starred2.txt","r")
fstarredlines=fstarred.readlines()
for line in fstarredlines:
	if 'https://api.github.com/' in line:
		repository=line.split()[0]
fstarred.close()
fstarred=open("starred2.txt","w")

for line in fstarredlines:
	if repository in line:
		break
	fstarred.write(line)
print repository	
END OF RECOVER'''
fstarred=open("starred.txt","w")

#write=0

count=0
for line in fcommit:
	field=line.strip("\n").split("\t")

	if len(field)>=5 and field[0]=="repo_info:": #header
		url=field[1][:-8] #remove /commits from url
		count+=1
		print count
		get_starred(url,fstarred)
		'''if(repository in url):
			write=1
			print "STARTED"
		if(write):
			get_starred(url,fstarred)'''
fstarred.close()
