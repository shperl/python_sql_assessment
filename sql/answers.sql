--Given a table with monthly transactions (customer id, month, payment) and a table with customer info(type 2 dimension) (id, cust_id, plan type, num users, start_date, end_date):
--1) tell me how much customers pay per month, per plan ($, month, plan type)
--1b) tell me what the top grossing plan is each month (month, $, plan)
--2) Given the above tables tell me how many customers we bring on every month (month, plan, # new customers)
--3) Given the above tables, tell me how many people switch plans per month (month, from plan, to plan, # customers)


-- Fact Table: transactions
-- customer_id (integer)
-- month (date)
-- payment (numeric)

-- Dimension Table: dim_customer (SCD type 2)
-- id (integer)
-- cust_id (integer)
-- plan_type (varchar)
-- num_users (integer)
-- start_date (date)
-- end_date (date)

-- Assumption 1: Active records will have an end date of '2999-12-31', could alternatively used NULL.
-- Assumption 2: Customers can only have one active plan at a time (as no mapping from transaction -> plan exists, or if one transaction, no way to split)


-- Question 1:  How much do customers pay per month, per plan ($, month, plan type)?
SELECT
    tx.month as month,
    dc.plan_type as plan_type,
    SUM(tx.payment) AS payment_sum
FROM transactions AS tx
    JOIN dim_customer AS dc
    ON (tx.customer_id = dc.cust_id)
    AND (tx.month >= dc.start_date)
    AND (tx.month < dc.end_date)
GROUP BY tx.month, dc.plan_type;

-- Question 1b: What is the top grossing plan is each month (month, $, plan)?
SELECT
    payment_month,
    plan_type,
    gross_payments
FROM (SELECT
        tx.month AS payment_month,
        dc.plan_type AS plan_type,
        SUM(tx.payment) AS gross_payments,
        rank() over (PARTITION BY tx.month order by SUM(tx.payment) desc) as rnk
    FROM transactions AS tx
        JOIN dim_customer AS dc
        ON tx.customer_id = dc.cust_id
        AND (tx.month >= dc.start_date)
        AND (tx.month < dc.end_date)
    GROUP BY tx.month, dc.plan_type) as payments
WHERE rnk = 1;


-- Question 2: Given the above tables, how many customers are brought on every month (month, plan, # new customers)?
SELECT
    cur_month,
    cur_plan_type,
    count(distinct tx1.customer_id)
FROM (SELECT
        transactions.customer_id as customer_id,
        month as cur_month,
        dim_customer.plan_type as cur_plan_type
      FROM transactions
      LEFT JOIN dim_customer
            ON (transactions.customer_id = dim_customer.cust_id)
            AND (transactions.month >= dim_customer.start_date)
            AND (transactions.month < dim_customer.end_date)
      WHERE transactions.month < DATE_TRUNC('month', CURRENT_DATE)
    ) as tx1
LEFT JOIN (SELECT
                transactions.customer_id as customer_id,
                month as prev_month,
                dc.plan_type as prev_plan_type
           FROM transactions
           LEFT JOIN dim_customer as dc
                ON (transactions.customer_id = dc.cust_id)
                AND (transactions.month >= dc.start_date)
                AND (transactions.month < dc.end_date)
           ) as tx2
        ON (tx1.customer_id = tx2.customer_id)
        AND ((tx1.cur_month - INTERVAL '1 month') = tx2.prev_month)
WHERE prev_month is null
GROUP BY cur_month, cur_plan_type;


-- Question 3: Given the above tables, how many people switch plans per month (month, from plan, to plan, # customers)?
SELECT
    cur_month,
    cur_plan_type,
    count(distinct tx1.customer_id)
FROM (SELECT
        transactions.customer_id as customer_id,
        month as cur_month,
        dim_customer.plan_type as cur_plan_type
      FROM transactions
      LEFT JOIN dim_customer
            ON (transactions.customer_id = dim_customer.cust_id)
            AND (transactions.month >= dim_customer.start_date)
            AND (transactions.month < dim_customer.end_date)
      WHERE transactions.month < DATE_TRUNC('month', CURRENT_DATE)
    ) as tx1
LEFT JOIN (SELECT
                transactions.customer_id as customer_id,
                month as prev_month,
                dc.plan_type as prev_plan_type
           FROM transactions
           LEFT JOIN dim_customer as dc
                ON (transactions.customer_id = dc.cust_id)
                AND (transactions.month >= dc.start_date)
                AND (transactions.month < dc.end_date)
           ) as tx2
        ON (tx1.customer_id = tx2.customer_id)
        AND ((tx1.cur_month - INTERVAL '1 month') = tx2.prev_month)
WHERE cur_plan_type != prev_plan_type
    and cur_plan_type is not null
    and prev_plan_type is not null
GROUP BY cur_month, cur_plan_type;


