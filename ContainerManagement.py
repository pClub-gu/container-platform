#This is all about managing containers with docker-py client

import docker
import os
import redis
import peewee
from sys import argv, exit

cli = docker.Client(base_url="unix://var/run/docker.sock")


get_ip = lambda container: str(cli.inspect_container(container=container["Id"])['NetworkSettings']['IPAddress'])

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


def __SetReverseProxy(CONTAINER_IP, SERVER_NAME, CONTAINER_ID):
    # This function is used to set the reverse proxy server for apache
    # This has to be updateed to nginx
    conf_template = open("Server_Config_templates/apacheConfig.conf", "r")
    conf_file = conf_template.read()
    conf_template.close()
    conf_file = conf_file.format(CONTAINER_IP=CONTAINER_IP, SERVER_NAME=SERVER_NAME)
    #conf_file = conf_file.replace("{SERVER_NAME}", SERVER_NAME)

    print "The config file for apache is : \n\n\n " + conf_file + "\n\n\n\n"
    deploy_conf = open(CONTAINER_ID + ".conf", "w")
    deploy_conf.write(conf_file)
    deploy_conf.close()
    command = "mv " + CONTAINER_ID + ".conf /etc/apache2/sites-available/"
    os.system(command)
    command = "sudo a2ensite " + CONTAINER_ID + ".conf"
    os.system(command)
    os.system("sudo service apache2 reload")
    #command = CONTAINER_ID + ".conf"
    #   os.remove(command)
    print 'Reverse Proxy server set'


def CreatePlatform(image_type, app_path, SERVER_NAME):
    '''
        The sole aim of this function is to create a platfrom specific containers, and run web apps with it.

        Currently this is optimised for python.
        Should add support for more.
    '''
    image_name = platform_containers.get(image_type)
    if not image_name:
        return "Error: Need the type of the app you are deploying"
    # time to create the container
    PORT=8000 # This has to customised for custom port, stored in redis

    # Procfile parsing
    procfile = open(app_path+"/Procfile", "r")
    procfile_data = procfile.read()
    procfile.close()

    procfile_data = procfile_data.split("\n")

    for i in procfile_data:
        if i.index("web"):
            procfile_data = i
            break
    command = procfile_data[procfile_data.index(":")+1:]


    container = cli.create_container(image=image_type,
                                     volumes=["/app"],
                                     ports=[8000],
                                     environment={"PORT": PORT},
                                     host_config=cli.create_host_config(binds={
                                         app_path:{
                                             "bind": "/app",
                                              "mode": "rw"
                                         }
                                     }),
                                     command=command
                                     )
    # SQL command to store the container metadata and the path. Need to write it
    # Installing the dependencies
    # Code goes here
    # Starting the container
    cli.start(container["Id"])

    CONTAINER_IP = get_ip(container)
    __SetReverseProxy(CONTAINER_IP, SERVER_NAME, container["Id"])
    # Time to deploy the container
    # Set the godaddy domain

    # that ends here
    # That pretty much is the function to create the platform specific container
    return


def CreateStaticSite(file_path, SERVER_NAME):
     # This works in with all the files
    # parse and set the nginx config file

    nginx_template = open("Server_Config_templates/nginx-template.conf", "r")
    nginx_conf = nginx_template.read()
    nginx_template.close()

    nginx_conf = nginx_conf.replace("{MY_SERVER_NAME}", SERVER_NAME)

    conf_file = open("default.conf", "w")
    conf_file.write(nginx_conf)
    conf_file.close()

    container = cli.create_container(image="nginx",
                                     volumes=["/var/www/html"],
                                     host_config=cli.create_host_config(binds={
                                         file_path:{
                                             "bind": "/var/www/html",
                                             "mode": "ro"
                                         }
                                     })
                                     )
    # Set domain here
    # SQL here
    command = "docker cp " + os.getcwd() + "Server_Config_templates/default.conf " + container["Id"]  + ":/etc/nginx/conf.d"
    print "The copy command is : " + command
    os.system(command)
    cli.start(container=container["Id"])
    CONTAINER_IP = get_ip(container)
    print "The IP address of the container is : " + CONTAINER_IP
    __SetReverseProxy(CONTAINER_IP=CONTAINER_IP, SERVER_NAME=SERVER_NAME, CONTAINER_ID=container["Id"])

    return

if __name__ == "__main__":
    # Testing the code here
    # This is misc
    print "argv[1]  : "  + argv[1]
    print "argv[2]  : "  + argv[2]
    CreateStaticSite(file_path=argv[1], SERVER_NAME=argv[2])
