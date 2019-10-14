# Sysco Labs Technical Assessment

This code repository contains the answers to the technical assessment for the Data Platform Engineer role at Sysco Labs.

## SQL Assessment

In the sql subdirectory, the answers.sql file contains the SQL that is used to answers to the following questions:

### Given a table with monthly transactions (customer id, month, payment) and a table with customer info(type 2 dimension) (id, cust_id, plan type, num users, start_date, end_date):

1. How much do customers pay per month, per plan ($, month, plan type)?
2. What is the top grossing plan is each month (month, $, plan)?
3. Given the above tables, how many customers are brought on every month (month, plan, # new customers)?
4. Given the above tables, how many people switch plans per month (month, from plan, to plan, # customers)?

### Assumptions

In order to carry out this analysis, a couple assumptions were necessary:

1. Active records will have an end date of '2999-12-31', could alternatively used NULL.
2. Customers can only have one active plan at a time (this is necessary as if there is no way to map individual transactions to one of many plans, we would require altering the data model).
3. As a corollary to 2, each transaction with be associated with a single plan and customers are billed once monthly (as transactions only map to customer, and there's only one plan per customer).

## Python Assessment

Requirements for the python assessment are defined in the requirements.txt file under the python subdirectory. They can be installed from within the python directory using pip:

```
pip install -r requirements.txt
```

The script used for the analysis can be run using the following command:
```
python3 mealdb_analysis.py