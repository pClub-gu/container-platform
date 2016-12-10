
from sys import argv

file_path = argv[1]

procfile = open(file_path+"/Procfile", "r")
procfile_data = procfile.read()
procfile.close()

procfile_data = procfile_data.split("\n")

print "the data in the procfile is :  "

integer = 0

for i in procfile_data:
    if "web" in i:
        print i
        break
#except ValueError:
#    print "ERROR:  This is the error thrown due to unavailablity of the web directive in the procfile\n\n"
        # Got to handle this in a more pythonic way

#print "the data has been parsed sucessfully"
#print procfile_data
