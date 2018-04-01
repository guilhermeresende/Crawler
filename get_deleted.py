#check for unavailable repositories (collected at commits.txt)
from crawler_lib import *
import time

fcommit=open("commits.txt","r")
fstatus=open("repostatus2.txt","w")

deleted_cnt=0
online_cnt=0
req_cnt=0
start=time.time()
for line in fcommit:
	field=line.strip("\n").split("\t")

	if len(field)>=5 and field[0]=="repo_info:": #header
		try:
			url=field[1]
			result=do_req(url)
			req_cnt+=1
			if result[1]>=0:
				fstatus.write(url+"\t"+"1"+"\n")
				online_cnt+=1
				if online_cnt%100==0:
					print online_cnt				
			else:
				fstatus.write(url+"\t"+str(result[1])+"\n")
				deleted_cnt+=1				
		except:
			print url,"error"

	time_dif=(time.time()-start)
	if(time_dif<3600 and req_cnt>4999): 
				print "WAIT FOR REQ LIMIT",3600-time_dif
				time.sleep(3600-time_dif)
				req_cnt=0
				start=time.time()

print online_cnt,deleted_cnt
fstatus.close()