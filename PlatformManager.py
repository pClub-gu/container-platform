import docker
import os
from sys import argv
import subprocess


bare_containers = {
    "ubuntu 16.04" : "ubuntu:16.04",
    "ubuntu 14.04": "ubuntu:14.04",
    "wordpress": "wordpress:latest",
    "alpine": "alpine:latest"
}

platform_containers = {
    "python2": "python:2.7.12", # also check for python:2-onbuild
    "python3": "python:latest" # Also check for python:3-onbuild
}


cli = docker.Client(base_url="unix://var/run/docker.sock")


get_ip = lambda container: str(cli.inspect_container(container=container["Id"])['NetworkSettings']['IPAddress'])


def HandleDependencies(container_id, image):
    # This is for python both 2 and 3
    if image == "python:2.7.12" or image == "python:latest":
        #print "DEBUG:  Entered the python dependency handler"

        # This is the pythonic way but it is not working
        ret_data  = cli.exec_create(container=container_id,
                        cmd="pip install -r requirements.txt",
                        tty=True)

        stream_data = " "
        for i in cli.exec_start(ret_data["Id"]):
            stream_data += str(i)

        print stream_data

        '''
        # Not so pythonic way of doing this
        command = "docker exec -it " + container_id + " pip install -r requirements.txt"
        os.system(command)
        '''

def CreatePlatform(image_type, file_path, SERVER_NAME=None):
    '''
        The sole aim of this function is to create a platfrom specific containers, and run web apps with it.

        Currently this is optimised for python.
        Should add support for more.
    '''
    image_name = platform_containers.get(image_type)
    if not image_name:
        print "Error: Need the type of the app you are deploying"
    # time to create the container
    PORT=8000 # This has to customised for custom port, stored in redis

    # Procfile parsing
    procfile = open(file_path+"/Procfile", "r")
    procfile_data = procfile.read()
    procfile.close()

    procfile_data = procfile_data.split("\n")
    try:
        for i in procfile_data:
            if "web" in i:
                procfile_data = i
                break
    except ValueError:
        print "This is the error thrown due to unavailablity of the web directive in the procfile"
            # Got to handle this in a more pythonic way
    # Parsing ends

    procfile_command = procfile_data[procfile_data.index(":")+1:]
    container = cli.create_container(image=image_name,
                                     volumes=["/app"],
                                     ports=[8000],
                                     environment={"PORT": PORT},
                                     host_config=cli.create_host_config(binds={
                                         file_path:{
                                             "bind": "/app",
                                              "mode": "rw"
                                         }
                                     }),
                                     tty=True,
                                     working_dir="/app"
                                     )
    # SQL command to store the container metadata and the path. Need to write it
    # Starting the container
    cli.start(container["Id"])
    # Installing the dependencies
    print "The procfile command is : " + procfile_command
    HandleDependencies(container_id=container["Id"], image=image_name)

    command = "docker exec -itd " + container["Id"] + " " + procfile_command
    subprocess.Popen(command, shell=True)# This is not really advised. This is more prone to injection attacks, something like "rm -rfv *"
    #os.system(command) # Neither is this. The best way out of the problem is to either sanitise the command, or using the docker API.
    # Need to update the code based on that.


    CONTAINER_IP = get_ip(container)
    #__SetReverseProxy(CONTAINER_IP, SERVER_NAME, container["Id"])
    # Time to deploy the container
    # Set the godaddy domain
    # That pretty much is the function to create the platform specific container
    cli.close()
    return


if __name__ == "__main__":
    print "the file path is:  " + argv[1]
    CreatePlatform(image_type="python2", file_path=argv[1])
