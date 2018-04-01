#crawl forks from repositories (at commits.txt)
from crawler_lib import *

def write_forks(forklist,url,fforks):
	for fork in forklist:
		s=fork['created_at']+"\n"
		fforks.write(s)

def get_forks(url,fforks):
	get_api_pages(url,write_forks,(fforks,))


fcommit=open("commits.txt","r")
fforks=open("forks.txt","w")
for line in fcommit:
	field=line.strip("\n").split("\t")

	if len(field)>=5 and field[0]=="repo_info:": #header
		url=field[1][:-8] #remove /commits from url
		if int(field[4])>0:
			fforks.write(url+"\n")
			get_forks(url+'/forks',fforks)
fforks.close()