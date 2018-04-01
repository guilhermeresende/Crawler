#check the users whose repositories were collected (at commits.txt)
from crawler_lib import *

users_finished=[]
orgs_finished=[]
other_finished=[]

fcommit=open("commits.txt","r")
cont=0
for line in fcommit:
	field=line.strip("\n").split("\t")

	if len(field)>=5 and field[0]=="repo_info:": #header
		cont+=1

		url=field[1]
		user=url[url.find("repos/"):].split("/")[1] #get user from commits url

		if not((user in users_finished) or (user in orgs_finished) or (user in other_finished)) :

			new_url='https://api.github.com/users/'+user
			(result,num_pages)=do_req(new_url)

			if(num_pages>0):

				if result["type"]=="User":
					users_finished.append(user)
					print cont, result["type"], user	
				else:
					orgs_finished.append(user)
					print cont, result["type"], user	
			else:
					other_finished.append(user)			
					print "ALERT",user

fcommit.close()



with open("check_users_result.txt","w") as f:
	f.write(str(users_finished))
	f.write("\n")
	f.write(str(orgs_finished))