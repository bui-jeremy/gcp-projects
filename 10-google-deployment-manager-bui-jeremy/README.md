[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/ZcG31-o8)
# Assignment 10: Google Deployment Manager

## Directions

In this homework we will try to recreate parts of Homework 5 using Google Deployment
Manager (GDM).

Write a declarative configuration using Google Deployment Manager, that can deploy the
parts of Homework 5 (Service Accounts, GCS buckets, VM web server, Cloud SQL
database, PubSub, VM with PubSub listener).

Since GDM does not support schema creation, you will have to modify your webserver
code to create the schema with the relevant tables if they don’t exist.

1. Run GDM to create all the relevant pieces of your deployment
2. Run the given HTTP client for a few (10-20) requests to demonstrate that
everything works.
3. Use curl to demonstrate the correct behavior for 200, 404, and 501 responses to
requests.
4. Show the contents of your database after the execution of the HTTP client and the
curl commands.
5. When done, make sure to shutdown your deployment and ensure that all relevant
resources have been cleaned up

## Submission

What to include in this repo: 
- The YAML code for your deployment as a github link.
- A PDF or markdown file describing all the necessary steps to deploy your configuration, the
output of your curl commands, the contents of your database, and console views
demonstrating the correct creation of all relevant resources, and correct deletion
of resources once the deployment has been decommissioned.
- In your report include your total spend on cloud resources for the development and execution of this program(s)
