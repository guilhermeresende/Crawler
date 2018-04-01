#Crawl commits made after original crawling (available at commits.txt)
from crawler_lib import *
from datetime import datetime

def get_last_commit():
    last_commit={}

    fcommit = open("commits.txt","r")
    #commitlines = fcommit.readlines()
    #fcommit.seek(0)
    for line in fcommit:
        field=line.strip("\n").split("\t")
        if len(field)>=5 and field[0]=="repo_info:": #header
            url=field[1]
            count=0
        elif (count==0):
            count+=1
            if len(field)>=4: #with email
                last_commit[url]=field[3]
            else: #with only name
                last_commit[url]=field[2]

    print "finnished reading"
    fcommit.close()

    return last_commit

def write_new_commits(commits,url,fcommit,last_commit):
    if '?page=' in url:
        url=url[:url.find('?page=')]
    for commit in commits:
        commitdate=commit[u'commit'][u'author'][u'date']
        if(commitdate==last_commit[url]):
            return -1
        '''try:
            if(datetime.strptime(commitdate,"%Y-%m-%dT%H:%M:%SZ")<datetime.strptime(last_commit[url],"%Y-%m-%dT%H:%M:%SZ")):
                print "ALERT", url
                print commitdate, last_commit[url]
                #print 3/0
        except:
            print commitdate, last_commit[url]
            print 3/0'''

        s=url+"\t"+commit[u'commit'][u'author'][u'name']+"\t"+commit[u'commit'][u'author'][u'email']+"\t"+commit[u'commit'][u'author'][u'date']

        if commit[u'author']!=None and (u'id' in commit[u'author']): #adds authors
            s+="\t"+str(commit[u'author'][u'id'])

        s+="\n"
        fcommit.write(s.encode('utf-8'))


def collect_new_commits(url,fcommit,last_commit):
    get_api_pages(url,write_new_commits,(fcommit,last_commit))


last_commit=get_last_commit()
f=open("alerts.txt","w")
f.close()
f=open("newcommits.txt","w")
for url in last_commit:   
    collect_new_commits(url,f,last_commit)
f.close()