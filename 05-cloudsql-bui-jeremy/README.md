# Assignment 5: CloudSQL

## Directions

*In this homework we will build on top of the work from Homework 4*
1. We will assume that you have successfully built the 2 apps required in HW 4. If not
please reach out to the professor or the TAs for code on which to build.
2. You should add a Cloud SQL database to your project and create a schema that
obeys 2nd normal form and can hold the following information about the requests
that your web server is receiving: country, client ip, gender, age, income, is_banned,
time of day, and requested file.
3. You should modify your web server to extract the information from the incoming
requests, process it appropriately to convert it to 2nd normal and insert it into the
database. You will need to make the appropriate changes to your VM so that it has
the right permissions and installed libraries to be able to talk to your database.
Requests that fail (return codes other than 200) should be logged into a separate
table that also obeys 2nd normal form but only contains the time of request, the
requested file, and the error code.
4. Demonstrate the functionality of your app by using curl to issue one successful and
2 erroneous requests and show the contents of your tables before and after each
request.
5. Provision a VM that can handle the request load from 2 concurrent clients (use the
client that has been provided to you) and run each client to issue 50,000 requests
against your VM. Make sure to start the 2 clients with the same random seed so
the clients are consistent about their request generation. This may take a little
while to finish (multiple minutes)
6. Once the clients have completed, compute the following statistics on your
requests:
  - How many requests were you able to process successfully vs unsuccessfully?
  - How many requests came from banned countries?
  - How many requests were made by Male vs Female users?
  - What were the top 5 countries sending requests to your server?
  - What age group issued the most requests to your server?
  - What income group issued the most requests to your server?

## Submission
What to include in this repo:

- The Python code for your modified first app (and the unmodified second app)
- A PDF or markdown file describing all the necessary steps to configure and run your apps, your database schema, screenshots of your curl work from step #4, and your methodology and answers to part #6.
