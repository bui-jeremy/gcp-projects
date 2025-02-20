[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/UGQAEdtH)
# Assignment 8: Load Balancers and VMs

## Directions

*In this homework we will build on top of the work from Homework 4*
1. We will assume that you have successfully built the 2 apps required in HW 4. If not
please reach out to the professor or the TAs for code on which to build.
2. You should now create two VMs running your web server, and ensure they are in
different zones (in the same region) and place them behind a load balancer. I
recommend using a network load balancer as it is easier to use. Make sure you
configure health checks and other properties appropriately.
3. Modify your web server code to return the name of the zone the server is running
in as a response header.
4. Modify the given client to extract and print the new response header your are
returning in step #3.
5. Kill the web server in one of your VMs and report how quickly the load balancer
notices its demise and routes the requests to the remaining healthy instance by
monitoring any errors seen by your client (it should be in the order of seconds and
definitely less than a minute). If not, stop your client to save on resource usage and
use curl to debug your setup.
6. Once the load balancer has rerouted traffic to your one healthy VM, restart the
web server on the other one and report how quickly the load balancer notices its
presence and starts routing requests to it by monitoring the responses your client
is getting (it should be in the order of seconds and definitely less than a minute). If
not, stop your client to save on resource usage and use curl to debug your setup.

## Submission

What to include in this repo: 
- The python code for your modified server and client
- A PDF or markdown file describing all the necessary steps to configure and run your apps, your
failover timing measurements, and the ratio of requests served by each backend
VM.
