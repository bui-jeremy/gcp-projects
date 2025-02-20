# Assignment 6: Data Classification with VMs and CloudSQL

## Directions

*In this homework we will build on top of the work from Homework 5*
1. We will assume that you have successfully populated the database with the
information coming from the client as described in HW 5. If not please reach out to
the professor or the TAs for sample code.
2. Write a simple program that can retrieve the data from the database, and build 2
models that use some of the fields to predict some of the other fields. Run this
program on a VM that you will create as part of the exercise.
  - One model should use client IP to predict the country from which the request originated. You can use any model you want but you should be able to achieve at least 99% accuracy for this exercise.
  - The second model should use any of the available fields to predict income. Once again you get to choose what kind of model you want to use. You should aim for 80+% accuracy for this second model but report any problems you run into, as fitting a model for this data is subject to the vagaries of the random seed you may have picked.

## Submission

What to include in this repo: 
- The python code for retrieving the data and building your two models
- A PDF or markdown file describing all the necessary steps to configure and run your app, the
output of your models and an explanation of how your models work.
