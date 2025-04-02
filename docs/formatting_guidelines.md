SQL code formatting guidelines
===============

### The non-idempotent part

Here we define tables, triggers and the like. Idempotent in this context means if you run a file a 2nd time against a database it is supposed to fail. For example, if you create a table and you want to create it again, the 2nd operation fails because the table is already there. Non-idempotency also means that a change transforms a database from one state to another. Hence, to get from a certain state to another state through multiple changes an order is required.

The very first of these changes is represented in `initialize_db.sql`. This file generally creates the database. It also creates users. This is a bit unfortunate because in postgres the scope of a user id is the cluster, not a single database.

Based on the state set up by `initialize_db.sql`, the series of `schema_N_up.sql` files is run against the database in the order given by `N`. `N` is a sequence number without gaps.

The rest of the files in `config/sql/` is to adjust the database to certain conditions aside from production. Notably we have there `unit_test_dml.sql` and `test_helper.sql`. The former contains much outdated test data. Unfortunately, a number of our tests still rely on that data. The latter contains helper functions to ease unit testing. `test_helper.sql` relies on the existence of the schema `t` in the database and should not modify anything outside of that schema.

Schema files have control over their database transactions. That usually means a schema file starts with

``` {#bkmrk-begin%3B}
BEGIN;
```

and ends with

``` {#bkmrk-commit%3B}
COMMIT;
```

However, it is perfectly valid to have several transactions in the same schema if that's semantically necessary. `CREATE INDEX CONCURRENTLY` would be an example.

### The idempotent part

Here we define mainly functions. All functions should be created with `CREATE OR REPLACE FUNCTION` instead of just `CREATE FUNCTION`. In an up-to-date database you should be able to run any of the files in `config/sql/functions/` and the database should not change. Besides the obvious, this means each function should be defined only in one file. You can't have multiple versions of a function in different files.

The files in that directory are named like `NNN_function_name.sql`. In contrast to the non-idempotent part, the number `NNN` does not define an order. Initially it was used to keep semantically related functions together.

The general rule is to have one function per file. Sometimes rapid development is easier if semantically related functions are in the same file. This is temporarily acceptable. However, once things have settled that one file should be split up.

Similarly, sometimes you might want to transition from one version of a function to another. If the parameter lists of these 2 functions differ Postgres recognizes them as 2 different functions. So, you could create the new version in the same file and keep the old one there, too. Once each caller has been updated, the old function is then removed from the file. This is also acceptable. However, beware of [the type conversion trap](./sql-tips#the-type-conversion-trap "the type conversion trap").

The files here should not contain transaction control statements, no `BEGIN` or `COMMIT`. This is left to the caller.

General Code Layout
===================

**As a general rule, try to keep lines shorter than 80-120 characters.**

Spaces should be used to line up the code so that the root keywords all end on the same character boundary. This forms a river down the middle making it easy for the readers eye to scan over the code and separate the keywords from the implementation detail.

> Use:
{.is-success}

``` {#bkmrk-select-...-from-...-}
SELECT ...
  FROM ...
  JOIN ... ON ...
  LEFT JOIN ... ON ...
 RIGHT JOIN ... ON ...
 WHERE ...
   AND ...
 GROUP BY ...
HAVING ...
 ORDER BY ... DESC
 LIMIT ...
OFFSET ...
```

> Don't use something like this:
{.is-danger}

``` {#bkmrk-select-...-from-...--0}
SELECT ...
    FROM ...
    JOIN ... ON ...
    LEFT JOIN ... ON ...
    RIGHT JOIN ... ON ...
    WHERE ...
        AND ...
    GROUP BY ...
    HAVING ...
    ORDER BY ... DESC
    LIMIT ...
    OFFSET ...
```

ORDER BY, GROUP BY, FOR UPDATE and similar
==========================================

Following the general layout the last character of the first word is vertically aligned.

> Like this:
{.is-success}

``` {#bkmrk-select-...-...-order}
SELECT ...
   ...
 ORDER BY ...
```

> Not like this:
{.is-danger}

``` {#bkmrk-select-...-...-order-0}
  SELECT ...
     ...
ORDER BY ...
```

RETURNING
=========

`RETURNING` is an exception to the alignment rule above because it's too long. It's placed on a separate line and the first letter is aligned with the first letter of the corresponding `INSERT`, `UPDATE` or `DELETE`.

> Like this:
{.is-success}

``` {#bkmrk-insert-into-other_ta}
INSERT INTO other_table AS ot (id, txt_col)
SELECT tt.id, coalesce(tt.txt_col, 'n/a')
  FROM this_table AS tt
    ON CONFLICT (id)
    DO UPDATE SET txt_col = 'upd ' || excluded.txt_col
RETURNING ot.id
        , ot.txt_col
```

Output Lists
============

As a general rule always specify all columns you need from a query.

> Do not use:
{.is-danger}

``` {#bkmrk-select-%2A}
SELECT *
```

An exception might be a query in the Perl code calling a function like:

``` {#bkmrk-select-%2A-from-some_f}
SELECT *
  FROM some_function($1, $2)
```

But even then better to qualify the output list.

> Start the output list with the first element on the same line as `SELECT`. Then place each subsequent on its own line with the commas aligned under the `T` of `SELECT` like:
{.is-success}

``` {#bkmrk-select-col1-%2C-coales}
SELECT col1
     , coalesce(col2, 'n/a') AS col2
     , col3
```

Placing the comma at the end of the line is also acceptable. However, better to use the style shown above.

If the entire output list is short enough to be placed on the same line as the `SELECT` keyword without exceeding the line length limit, then it can be done so.

``` {#bkmrk-select-tt.id%2C-coales}
SELECT tt.id, coalesce(tt.txt_col, 'n/a') AS txt_col
  FROM this_table AS tt
```

#### Set returning functions in output lists

Consider this query:

``` {#bkmrk-select-x-%2C-generate_}
SELECT x
     , generate_series(1, 5) AS i
  FROM (VALUES ('a'), ('b'), ('c')) AS txt(x)
```

How many rows are produced? At first glance most people would expect 3. However, when you realize `generate_series()` is a set-returning function, then the answer is *I don't know* or 15.

> Avoid set-returning functions in the output list.
{.is-success}

``` {#bkmrk-select-txt.x-%2C-gen.i}
SELECT txt.x
     , gen.i
  FROM (VALUES ('a'), ('b'), ('c')) AS txt(x)
 CROSS JOIN generate_series(1, 5) AS gen(i)
```

Sometimes performance dictates otherwise, however. Depending on the circumstances either of these variants can be significantly faster than the other. In such a case add a comment and explain why.

``` {#bkmrk-select-x----note%2C-ge}
SELECT x
       -- Note, generate_series() returns multiple rows but using
       -- it that way is twice as fast as the equivalent cross join
     , generate_series(1, 5) AS i
  FROM (VALUES ('a'), ('b'), ('c')) AS txt(x)
```

A real-life example would be this query:

``` {#bkmrk-select-uc.id-%2C-uc.bi}
SELECT uc.id
     , uc.binary_user_id
     , x.js ->> 'value'
  FROM users.binary_user_connects AS uc
 CROSS JOIN jsonb_array_elements(uc.provider_data::JSONB -> 'user' -> 'identity' -> 'emails') AS x(js)
```

instead of

``` {#bkmrk-select-id-%2C-binary_u}
SELECT id
     , binary_user_id
     , jsonb_array_elements(provider_data::JSONB -> 'user' -> 'identity' -> 'emails') ->> 'value'
  FROM users.binary_user_connects
```

WITH clauses (Common Table Expressions)
=======================================

The general layout of a CTE looks like this:

``` {#bkmrk-with-t1-as-%28-select-}
WITH t1 AS (
    SELECT something, ...
      FROM some_table
     WHERE ...
       FOR UPDATE
)
, t2(col1, col2) AS (
    DELETE FROM some_table AS st
     USING t1
     WHERE st.something = t1.something
    RETURNING ...
)
SELECT ...
  FROM t1
 CROSS JOIN t2
```

The declaration of a virtual table starts on a separate line with either the keyword `WITH` or the comma. The comma to declare subsequent virtual tables is aligned with the `W` of the corresponding keyword `WITH`.

The definition of a virtual table is then indented by 4 spaces as show above.

The final statement starts on a separate line on the same column as `WITH`.

Sub-Selects
===========

2 forms of formatting sub-selects are preferred.

If the sub-select is small enough and you don't want to rename output columns, this can be used:

``` {#bkmrk-select-...-from-%28sel}
SELECT ...
  FROM (SELECT ...
          FROM ...) AS t
```

That is the `SELECT` keyword of the sub-select starts right after the opening parenthesis on the same line. The closing parenthesis is placed at the end of the last line of the sub-select followed by the keyword `AS` and the alias.

The 2nd form is preferred when the form above would lead to excessively long lines:

``` {#bkmrk-select-...-from-t1-l}
SELECT ...
  FROM t1
  LEFT JOIN (
        SELECT account_id
             , max(amount)
             , min(amount)
             , avg(amount)
          FROM ...
         GROUP BY 1
       ) AS t2(max_amount,
               min_amount,
               avg_amount) ON t1.account_id = t2.account_id
```

The closing parenthesis is aligned with the right bank of the river in the middle. The initial SELECT of the sub-select starts on the next line one position further indented.

WHERE clauses
=============

`WHERE` clauses are often a list of conditions combined by `AND`. The general style of alignment is as follows:

``` {#bkmrk-select-...-from-...-}
SELECT ...
  FROM ...
 WHERE condition1
   AND condition2
   AND ...
```

Sometimes a condition is semantically a range like `A <= x < B`.

> This is preferred to be written as
{.is-success}

``` {#bkmrk-where-a-%3C%3D-x-and-x-%3C}
WHERE A <= x AND x < B
```

Or as

``` {#bkmrk-where-a-%3C%3D-x-and-x-%3C-0}
WHERE A <= x
  AND x < B
```

> Instead of
{.is-danger}

``` {#bkmrk-where-x-%3E%3D-a-and-x-%3C}
WHERE x >= A
  AND x < B
```

If your `WHERE` clause contains an `OR` combination these 2 styles are preferred:

``` {#bkmrk-where-%28condition1-or}
WHERE (condition1 OR condition2 OR condition3)
```

``` {#bkmrk-where-%28condition1-or-0}
WHERE (condition1 OR
       condition2 OR
       condition3)
```

That is, place the `OR` combination in parentheses even if it is the only condition. Code evolves and somebody might add an `AND` condition later.

> Under no circumstances mix `AND` and `OR` like this even if it behaves correctly:
{.is-danger}

``` {#bkmrk-where-condition1-and}
WHERE condition1
  AND condition2
   OR condition3
  AND condition4
```

UNION, UNION ALL and similar
============================

`UNION`, `EXCEPT` and similar operations combine the results of 2 independent queries.

The recommended style looks like this:

``` {#bkmrk-select-...-from-...-}
SELECT ...
  FROM ...
  
UNION ALL

SELECT ...
```

That is, the UNION clause is surrounded by 2 empty lines. The `UNION` keyword starts at the same position as the 2 corresponding queries.

Sometimes it's necessary to place the queries in parentheses. One such case would be to apply a `LIMIT` clause to each of the queries separately.

This would then look like this:

``` {#bkmrk-%28select-row_number%28%29}
(SELECT row_number() OVER (ORDER BY i) * 100 AS rn
      , i
   FROM generate_series(20, 25) AS i
  ORDER BY 1
 OFFSET 3)

UNION ALL

(SELECT row_number() OVER (ORDER BY i) * 200 AS rn
      , i
   FROM generate_series(10, 15) AS i
  ORDER BY 1
  LIMIT 3)

ORDER BY i
OFFSET 1
LIMIT 4
```

Space or no space
=================

There are way too many situations to cover everything. This page should give you an idea, though.

##### Put a space around operators

``` {#bkmrk-update-some_table-se}
UPDATE some_table
   SET col = 10 * col2 + 19      -- like here around =, * and +
 WHERE col < 19                  -- or here around <
```

##### Put a space on the right side of a comma unless it's the end of the line

``` {#bkmrk-with-map%28c%2C-i%29-as-%28-}
WITH map(c, i) AS (             -- like here
    VALUES ('a', 1), ('b', 2)   -- or here
)
SELECT c, i                     -- or here
  FROM map
```

``` {#bkmrk-create-table-some_ta}
CREATE TABLE some_table (
    -- no space necessary after the comma on the next 2 lines
    col1    BIGINT,
    col2    TEXT,
    PRIMARY KEY (col1, col2)     -- but here a space is appropriate
)
```

##### Put a space before the opening parenthesis in a `CREATE TABLE` statement and similar situations

``` {#bkmrk-create-table-some_ta-0}
CREATE TABLE some_table (   -- a space here
    ...
)
```

``` {#bkmrk-insert-into-some_tab}
INSERT INTO some_table (    -- put a space here
    col1,
    ...
)
VALUES ('a', ...),          -- put a space here after VALUES
       ('b', ...)
    ON CONFLICT (col1)      -- put a space here
```

``` {#bkmrk-create-index-idx_nam}
CREATE INDEX idx_name ON some_table (col1, col2)    -- put a space here before the opening (
```

``` {#bkmrk-select-row_number%28%29-}
SELECT row_number() OVER (ORDER BY col1) AS rn      -- put a space between OVER and (
  FROM ...

SELECT row_number() OVER w AS rn
  FROM ...
WINDOW w AS (ORDER BY col1)                         -- put a space between AS and (
```

##### No space between a `WITH` query name and the column list

``` {#bkmrk-with-map%28c%2C-i%29-as-%28--0}
WITH map(c, i) AS (         -- no space between map and (
    ...
)
```

##### No space between a table alias and the column list

``` {#bkmrk-select-...-from-%28-se}
SELECT ...
  FROM (
        SELECT ...
       ) AS tablealias(col1, ...)    -- no space here
```

##### No space before the opening parenthesis when calling a function or in similar situations

``` {#bkmrk-select-nullif%28gen.i-}
SELECT nullif(gen.i % 3 = 0, true)             -- no space after nullif
     , random()                                -- no space after random
     , lag(gen.i) OVER (ORDER BY gen.i)        -- no space after lag
  FROM generate_series(1, 10) AS gen(i)        -- no space after generate_series
```

##### No space on the same line after an opening or before a closing parenthesis

``` {#bkmrk-select-nullif%28gen.i--0}
SELECT nullif(gen.i % 3 = 0, true)             -- instead of nullif( gen.i % 3 = 0, true )
     , random()                                -- instead of random( )
     , lag(gen.i) OVER (ORDER BY gen.i)        -- instead of lag( gen.i )
  FROM generate_series(1, 10) AS gen(i)        -- instead of generate_series( 1, 10 )
```

Parentheses
===========

As a general rule, use parentheses only where precedence or syntax asks for them. A place where they are required by syntax is if a column is of complex type and you want to access an element of that type.

> Like this:
{.is-success}

``` {#bkmrk-select-%28x.cl%29.logini}
SELECT (x.cl).loginid
  FROM t.create_client('{}'::JSON) AS x
```

or

``` {#bkmrk-select-%28t.create_cli}
SELECT (t.create_client('{}'::JSON)).cl.loginid
```

Here is an example where parentheses are better omitted:

``` {#bkmrk-select-...-from-t1-j}
SELECT ...
  FROM t1
  JOIN t2 ON (t1.col1 = t2.col2)
```

For more information about operator precedence, please refer to the [Postgres documentation](https://www.postgresql.org/docs/current/sql-syntax-lexical.html#SQL-SYNTAX-OPERATORS).

JOINs
=====

Joins are by default `INNER` joins.

> This keyword is omitted.
{.is-success}

``` {#bkmrk-select-...-from-a-jo}
SELECT ...
  FROM a
  JOIN b ON ...
```

> Instead of
{.is-danger}

``` {#bkmrk-select-...-from-a-in}
SELECT ...
  FROM a
 INNER JOIN b ON ...
```

The same applies to the keyword `OUTER`. Use `LEFT JOIN` instead of `LEFT OUTER JOIN`.

Use explicit join conditions `ON t1.col1 = t2.col1` instead of `USING (col1)` or `NATURAL`.

If possible place the join condition on the same line as the joined table like this:

``` {#bkmrk-select-...-from-a-jo-0}
SELECT ...
  FROM a
  JOIN b ON a.x = b.y
```

Where this is not possible because the condition is too complex follow the general layout:

``` {#bkmrk-select-...-from-a-jo-1}
SELECT ...
  FROM a
  JOIN b
    ON a.x = b.y
```

Make joins explicit. Inner joins can always be replaced by a cross join with a corresponding `WHERE` clause.

> Please prefer the explicit join.
{.is-success}

``` {#bkmrk-select-...-from-a-jo-2}
SELECT ...
  FROM a
  JOIN b ON a.x = b.y
```

> Instead of
{.is-danger}

``` {#bkmrk-select-...-from-a%2C-b}
SELECT ...
  FROM a, b
 WHERE a.x = b.y
```

If you really need an unqualified Cartesian product of 2 tables, spell it out as `CROSS JOIN` instead of just using the comma. Note, a `CROSS JOIN` is the same as an `INNER JOIN ON true`. Please use the former.

##### LATERAL

Joining a function is automatically `LATERAL`. In that case we omit the syntactic sugar.

> Use:
{.is-success}

``` {#bkmrk-select-...-from-some}
SELECT ...
  FROM some_table AS tb
  JOIN some_function(tb.col1, tb.col2) AS fn ON ...
```

> Instead of:
{.is-danger}

``` {#bkmrk-select-...-from-some-0}
SELECT ...
  FROM some_table AS tb
  JOIN LATERAL some_function(tb.col1, tb.col2) AS fn ON ...
```

Otherwise, the `LATERAL` keyword is only useful in combination with a sub-select. Often, however, it can be replaced with a normal `JOIN`. Please try to avoid `LATERAL`. `LATERAL` basically forces a nested loop join which is only suitable for low data volume.

> Use:
{.is-success}

``` {#bkmrk-select-...-from-some-1}
SELECT ...
  FROM some_table AS tb
  JOIN (SELECT sum(x.col1) AS sum_col1
             , x.col2
          FROM other_table AS x
         WHERE ...
         GROUP BY x.col2) AS t2 ON t2.col2 = tb.some_column
```

> Instead of:
{.is-danger}

``` {#bkmrk-select-...-from-some-2}
SELECT ...
  FROM some_table AS tb
 CROSS JOIN LATERAL (
        SELECT sum(x.col1) AS sum_col1
          FROM other_table AS x
         WHERE x.col2 = tb.some_column
           AND ...
       ) AS t2
```

Of course, in cases where `LATERAL` is unavoidable, use it.

Identifiers
===========

In SQL names which designate database objects like tables, columns, constraints, triggers etc. are called identifiers. SQL allows to use arbitrary characters in identifiers with proper quoting. For instance `"this is a table"."and this a colunm"` is valid SQL and identifies a column in a table. Unless there is a very specific reason, this should be avoided.

##### Character set

All identifiers in our system should start with a letter and consist or letters, digits and underscore characters. Without explicit quoting identifiers are case-insensitive in SQL. We use lower-case only, `client.loginid` instead of `CLIENT.loginId`.

##### Singular

Objects should be named in singular. We do have a `client` and a `transaction` table, not `clients` or `transactions`.

 

``` {#bkmrk-with-acc-as-%28-select}
WITH acc AS (
    SELECT x.client_loginid AS loginid
         , x.currency_code
      FROM transaction.account AS x
     ORDER BY last_modified DESC
     LIMIT 10
)
SELECT c.loginid
     , c.date_joined
     , acc.currency_code
  FROM acc
  JOIN betonmarkets.client AS c ON c.loginid = acc.loginid
```

Upper/Lower case
================

SQL keywords like `SELECT` or `JOIN` are written in UPPER CASE. Everything else including standard SQL functions like `max()` or operators like `coalesce()` or `nullif()` are written in lower case.

``` {#bkmrk-select-count%28%2A%29-as-t}
SELECT count(*) AS total_row_count
     , avg(t.amount) AS amount_average
  FROM transaction.transaction AS t
```

Standard types are usually spelled in upper case and without the namespace. Our own custom types are spelled lower case including the namespace.

> Like this:
{.is-success}

``` {#bkmrk-create-table-bet.lim}
CREATE TABLE bet.limits_market_mapper (
    symbol      TEXT PRIMARY KEY,       -- built-in type
    market      TEXT NOT NULL,
    submarket   TEXT NOT NULL,
    market_type bet.market_type         -- our own custom type
)
```

Types and Typecasting
=====================

Types
-----

Postgres supports for several types multiple names. In general we prefer the shorter one. So, use `VARCHAR` instead of `CHARACTER VARYING`. Use `TIMESTAMP` instead of `TIMESTAMP WITHOUT TIMEZONE`.

There are a few exceptions, however.

-   prefer `DOUBLE PRECISION` over `FLOAT8`
-   prefer `INTEGER` over `INT4`
-   prefer `BIGINT` over `INT8`

> Types to avoid:
{.is-danger}

-   `CHAR`, use `TEXT` or `VARCHAR`
-   `MONEY`, use `NUMERIC`
-   `DECIMAL`, use `NUMERIC`
-   `TIMETZ`, think again
-   `TIMESTAMP(0)` or `TIMESTAMPTZ(0)`, never store data like this. Why would you want to reduce precision? If you need second boundaries, use `date_trunc()`.

> Types to think twice:
{.is-warning}

-   `REAL` - pretty low precision, maybe better `DOUBLE PRECISION`
-   `DOUBLE PRECISION` - make sure you understand the rounding differences between `NUMERIC` and `DOUBLE PRECISION`. Money quantities have to be `NUMERIC`. Exchange rates (ticks) are usually `DOUBLE PRECISION`.
-   `DATE` - maybe better `TIMESTAMP` or `TIMESTAMPTZ`
-   `SERIAL` and `BIGSERIAL` - in a post-9.6 world use `IDENTITY` columns.

Typecasting
-----------

Postgres has multiple ways to express typecasting. In our code the postfix `::TYPE` syntax is preferred.

> Use:
{.is-success}

``` {#bkmrk-select-date_trunc%28%27d}
SELECT date_trunc('day', now())::TEXT AS start_of_today
```

> Instead of
{.is-danger}

``` {#bkmrk-select-text%28date_tru}
SELECT TEXT(date_trunc('day', now())) AS start_of_today
```

``` {#bkmrk-select-cast%28date_tru}
SELECT CAST(date_trunc('day', now()) AS TEXT) AS start_of_today
```

## Avoid `%TYPE` and `%ROWTYPE` or similar

In Postgres a table definition also defines a type with the same name. In our clientdb the following would, hence, be a valid table definition:

```
CREATE TABLE type_test (
    txn transaction.transaction,
    fmb bet.financial_market_bet,
    pm  payment.payment
);
```

Likewise, `plpgsql` allowes to use table names as types and to copy types:

```
CREATE OR REPLACE FUNCTION type_test ()
RETURNS SETOF TEXT LANGUAGE plpgsql AS $$
DECLARE
    v1 betonmarkets.broker_code;
    v2 betonmarkets.broker_code.broker_code%TYPE;
    v3 betonmarkets.broker_code%ROWTYPE;
BEGIN
    RETURN NEXT format('v1 is of type %s', pg_typeof(v1));
    RETURN NEXT format('v2 is of type %s', pg_typeof(v2));
    RETURN NEXT format('v3 is of type %s', pg_typeof(v3));
END
$$;
```

> If possible avoid any of the above.
{.is-danger}

Here is why.

```
# ALTER TABLE transaction.transaction ALTER COLUMN remark TYPE TEXT;
ERROR:  cannot alter table "transaction" because column "type_test.txn" uses its row type
```

As can be seen, using a table type as part of the definition of another table prevents certain changes of the table type. This certainly comes as a surprise. You want to change the type of a column in one table but you can't because of some other seemingly unrelated table.

So what about the usage in functions? That seems fair enough. Let's call the `type_test` function.

```
# select * from type_test();
               type_test                
----------------------------------------
 v1 is of type betonmarkets.broker_code
 v2 is of type character varying
 v3 is of type betonmarkets.broker_code
```

Interestingly, it does not make a difference whether or not we use `%ROWTYPE`. Also, the `%TYPE` specification actually means to look up the type when the function is compiled and use it from then on.

Now, keep that session running and in another session change the type of the `broker_code` column.

```
# ALTER TABLE betonmarkets.broker_code ALTER COLUMN broker_code TYPE TEXT;
ALTER TABLE
```

Then go back to the original session and call the function again. You will see that the type of `v2` has not changed. It's still `VARCHAR`. The only way to inform the original session about the type change is to `CREATE OR REPLACE` the function. But to do that you have to know the function exists.

> The take-away from this little experiment should be to avoid `%TYPE`, `%ROWTYPE` and using table definitions as types. This can create explicit or silent *action-at-a-distance* problems.
{.is-success}

Aliases
=======

SQL allows to use alias names in queries. You are encouraged to use aliases even in the simplest query. That way, when the query evolves, less mistakes can be made. Aliases are usually introduced by the optional keyword `AS`. Please spell this out in capital letters.

``` {#bkmrk-update-transaction.a}
UPDATE transaction.account AS a
   SET binary_user_id = c.binary_user_id
  FROM betonmarkets.client AS c
 WHERE a.client_loginid = c.loginid
```

Alias names are valid only within the scope of a query. Hence, they can be short. Don't invent `overly_complicated_and_long_alias_names`. Traditionally we use certain common aliases.

-   `b` or `fmb` is a common alias for the `bet.financial_market_bet` table
-   `fmbo` stand for `bet.financial_market_bet_open`.
-   `a` or `acc` is the `transaction.account` table
-   `c` or `cl` is an alias for `betonmarkets.client`
-   `p` usually designates `payment.payment`

Aliases can be omitted if they refer to common table expressions. There is no need to introduce another alias for the `acc` table in the main part of this query.

``` {#bkmrk-with-acc-as-%28-select}
WITH acc AS (
    SELECT x.client_loginid
         , x.currency_code
      FROM transaction.account AS x
     ORDER BY last_modified DESC
     LIMIT 10
)
SELECT c.loginid
     , c.date_joined
     , acc.currency_code
  FROM acc
  JOIN betonmarkets.client AS c ON c.loginid = acc.client_loginid
```

Column aliases are better also avoided. In this example a column alias is used to rename `client_loginid` in the common table expression to simply `loginid`. This should be avoided. However, this is a judgement call. We do have some awfully long column names like `binary_user_id` or `financial_market_bet_id`. It is acceptable to  shorten them to `buid` and `fmbid` respectively.  The important point is to avoid unnecessary aliases in the final output list of a query. Our code often uses `$dbh->fetchrow_hashref()`. So names matter and better to name things uniformly.

> Renaming `client_loginid` to `loginid` in the `WITH` clause is not a good idea.
{.is-danger}

``` {#bkmrk-with-acc-as-%28-select-0}
WITH acc AS (
    SELECT x.client_loginid AS loginid
         , x.currency_code
      FROM transaction.account AS x
     ORDER BY last_modified DESC
     LIMIT 10
)
SELECT c.loginid
     , c.date_joined
     , acc.currency_code
  FROM acc
  JOIN betonmarkets.client AS c ON c.loginid = acc.loginid
```

CREATE TABLE
============

How to best format `CREATE TABLE`?

``` {#bkmrk-create-table-betonma}
CREATE TABLE betonmarkets.payment_agent_country (
    client_loginid VARCHAR
                   REFERENCES betonmarkets.payment_agent(client_loginid)
                   ON UPDATE restrict
                   ON DELETE cascade,
    country        TEXT,
    insert_time    TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (client_loginid, country)
)
```

-   Fully qualify the table name. Don't rely on the current `search_path`. Even if you have to create 20 tables in the `betonmarkets` schema, please repeat `betonmarkets....` 20 times. 
-   Declare each column starting with a new line. Choose at least 4 spaces indentation. More is acceptable but be reasonable.
-   Vertically align column names. (use the same amount of spaces in front of each column name)
-   Vertically align the type declarations of all columns. You can put more than one space between the longest column name and the type declaration.
-   A complete column definition can be very long. Break it up into multiple lines. Make sure those continuation lines are vertically aligned with the type declaration.
-   table constraints like the `PRIMARY KEY` definition in the example above are vertically aligned with column declarations and follow after all column definitions
-   [mind our upper/lower case convention](https://bookstack.deriv.cloud/books/sql-style-guide-and-faq/page/upperlower-case "SQL Style Guide and FAQ")
-   [mind our type name convention](https://bookstack.deriv.cloud/books/sql-style-guide-and-faq/page/types-and-typecasting "mind our type name convention")

#### Pitfall warning

``` {#bkmrk-create-table-foo-%28-b}
CREATE TABLE foo (
    bar TIMESTAMP DEFAULT 'today'::TIMESTAMP
)
```

This is a valid table definition. However, the result of the following INSERT statement on any day after the one when the table was created will probably surprise you.

``` {#bkmrk-insert-into-foo-%28bar}
INSERT INTO foo (bar) VALUES (DEFAULT)
```

It will always insert the same `TIMESTAMP`, namely the day when the table was created. Postgres converts `'today'` to a `TIMESTAMP` when it creates the table not when the row is inserted.

The correct definition is probably:

``` {#bkmrk-create-table-foo-%28-b-0}
CREATE TABLE foo (
    bar TIMESTAMP DEFAULT date_trunc('day', now())::TIMESTAMP
)
```

INSERT
======

Some recommendations on how to write `INSERT` statements

``` {#bkmrk-insert-into-namespac}
INSERT INTO namespace.table (
    col1,
    col2,
    col3
)
VALUES (
    'some constant value',
    DEFAULT                  -- the default value as per table declaration
    $3                       -- a parameter
)
```

-   fully qualify the table, don't rely on the `search_path`.
-   list the columns you want to insert. [Even if you want to insert a full row, do it.](https://bookstack.deriv.cloud/books/sql-style-guide-and-faq/page/dropping-a-column)
-   vertically align the column names with at least 4 spaces indentation
-   if you use `VALUES`, vertically align the data at the same column
-   if you use `INSERT ... SELECT`, follow the recommendations for `SELECT` queries.

UPDATE and DELETE
=================

In addition to everything else in this chapter, there is only one recommendation specific to `UPDATE` and `DELETE`. 

> Avoid joining other tables using the `IN` operator.
{.is-danger}

Given 2 tables, `src` and `del`. Now, you want to delete rows from `del` where corresponding rows in `src` match a certain criteria.

``` {#bkmrk-delete-from-del-wher}
DELETE FROM del
 WHERE del.i IN (SELECT src.i
                   FROM src
                  WHERE src.rnd < 0.5)
RETURNING *
```

> Instead, think in terms of an inner join
{.is-success}

This gives more flexibility in more complex situations. These are the rows the developer wants to remove:

``` {#bkmrk-select-%2A-from-del%2C-s}
SELECT *
  FROM del, src
 WHERE del.i = src.i
   AND src.rnd < 0.5
```

This can then simply be transformed into this `DELETE` statement.

``` {#bkmrk-delete-from-del-usin}
DELETE FROM del
 USING src
 WHERE del.i = src.i
   AND src.rnd < 0.5 
RETURNING *
```

The same applies to updates. If you think in terms of joins you gain flexibility.

``` {#bkmrk-update-del-as-target}
UPDATE del AS target
   SET rnd = source.rnd * 10 + target.rnd
  FROM src AS source
 WHERE target.i = source.i
   AND source.rnd < 0.5
RETURNING *
```

Operators
=========

##### Avoid custom operators

Postgres allows to [define custom operators](https://www.postgresql.org/docs/current/sql-createoperator.html "CREATE OPERATOR"). Except for testing and debugging purposes we avoid this.

##### Use operators the usual way

> Like
{.is-success}

``` {#bkmrk-select-3-%2B-4}
SELECT 3 + 4
```

> Instead of
{.is-danger}

``` {#bkmrk-select-3-operator%28pg}
SELECT 3 OPERATOR(pg_catalog.+) 4
```

Calling functions
=================

##### Style

If the parameter list is short enough to fit all on the same line, then call it

> like this:
{.is-success}

``` {#bkmrk-select-format%28%27quote}
SELECT format('quoted identifier: %I.%I', n.nspname, c.relname)
  FROM pg_class AS c
  JOIN pg_namespace AS n ON n.oid = c.relnamespace
```

If this would exceed the line length limit, then

> like this:
{.is-success}

``` {#bkmrk-select-format%28-%27quot}
SELECT format(
           'quoted identifier: %I.%I',
           n.nspname,
           c.relname
       ) AS table_name
  FROM pg_class AS c
  JOIN pg_namespace AS n ON n.oid = c.relnamespace
```

The opening parenthesis is attached to the function name without a space. Parameters are placed one per line and indented by 4 spaces. The closing parenthesis is vertically aligned with the beginning of the function name.

> Avoid placing multiple parameters on a line with a parameter list spanning multiple lines.
{.is-danger}

``` {#bkmrk-select-format%28-%27rela}
SELECT format(
           'relation %I.%I is of %s kind and is stored in %s',
           n.nspname, c.relname,              -- multiple parameters on the same line
           c.relkind, c.relfilenode           -- in a multi-line parameter list
       ) AS description
  FROM pg_class AS c
  JOIN pg_namespace AS n ON n.oid = c.relnamespace
```

##### Named parameters

Postgres also allows you to call a function with named parameters. A good example is the built-in function `make_interval`. It accepts 7 parameters each of which has a `DEFAULT` of 0. To build an interval of 1 hour, 43 minutes and 12.25 seconds you can call it like this:

``` {#bkmrk-select-make_interval}
SELECT make_interval(0, 0, 0, 0, 1, 43, 12.25)
```

or with named parameters like this

``` {#bkmrk-select-make_interval-0}
SELECT make_interval(
           hours => 1,
           mins  => 43,
           secs  => 12.25
       )
```

For functions with a confusing parameter list with lots of defaults this version is preferred because it improves readability. The drawback is, the developer has to know the parameter names. `make_interval` is also good to illustrate that. The parameters are called `years`, `months`, `weeks`, `days` and `hours` but then `mins` and `secs`.

##### Do not rely on the `search_path`

All functions except those defined in the `pg_catalog` namespace should be called fully qualified.

> Like:
{.is-success}

``` {#bkmrk-select-financial_mar}
SELECT financial_market_bet_id
  FROM public.expired_unsold_bets()
```

> Instead of
{.is-danger}

``` {#bkmrk-select-financial_mar-0}
SELECT financial_market_bet_id
  FROM expired_unsold_bets()
```

However, this is okay:

``` {#bkmrk-select-now%28%29%2C-random}
SELECT now(), random()
```

Because they are defined in `pg_catalog`.

Creating functions
==================

Postgres supports many programming languages to write stored procedures (functions). In our system we only allow SQL and PLPGSQL. Despite their similarity in the name these are different programming languages with different interpreters running them.

If possible prefer SQL over PLPGSQL.

#### General layout

Postgres'  function declaration syntax can be confusing. There are many ways to express the same thing. Information can be put before and after the function body. Parameter names are optional. And more.

Example:

``` {#bkmrk-create-or-replace-fu}
CREATE OR REPLACE FUNCTION namespace.function_name (
    p_param1 BIGINT,
    p_param2 TIMESTAMP,
    OUT out_column_name1 JSONB,
    OUT out_column_name2 TEXT
) RETURNS SETOF RECORD AS $def$
...
$def$ LANGUAGE plpgsql VOLATILE SECURITY invoker
      SET session_replication_role='replica'
```

-   In our source code, function declarations should always start with `CREATE OR REPLACE FUNCTION` instead of simply `CREATE FUNCTION`. See [here](https://bookstack.deriv.cloud/books/sql-style-guide-and-faq/page/files-and-directrories#bkmrk-the-idempotent-part "The idempotent part") for a justification.
-   The function name should be fully qualified. Even if you intend to create a function in the `public` namespace, specify it. Otherwise the reader has to do extra work to find out what the `search_path` is at the time when this is executed.
-   The function name is followed by the parameter list. If that list is short enough to fit on the same line without exceeding the length limits, then that's acceptable. In most cases, however, it's better to declare the parameter list as shown. Each parameter declaration starts on a new line indented by 4 spaces.
-   Always specify parameter names
-   After the parameter list follows an optional return type declaration
-   which is followed by the function body. The function body is a SQL string literal. Please use `$$`-style quoting here. Even better if you use something like `$def$` or `$func$` instead of the plain `$$`.
-   All the supplemental information which completes the function declaration is added after the function body. This information is not just a random sequence of words. It's a sequence of phrases where each phrase consists of one or several words. To separate these phrases visually, the first word of a phrase is written in upper case and the rest in lower case. In the example above, `LANGUAGE plpgsql` is such a phrase, `VOLATILE` is another as is `SECURITY invoker`. If you need to break the line, indent appropriately.
-   Specify only if something differs from the default. The phrase `SECURITY invoker` above is superfluous because that's the default.
-   If there are several ways to specify the same thing, use the shortest. `RETURNS null on null input` is the same as `STRICT`. So use the latter.

##### Parameter names

Parameter names can lead to visual confusion and ambiguity. Consider for instance this function:

``` {#bkmrk-create-or-replace-fu-0}
CREATE OR REPLACE FUNCTION ambig (i INT, t TEXT) RETURNS RECORD AS $$
    SELECT i, some_table.i
      FROM some_table
     WHERE some_table.t=t
$$ LANGUAGE sql
```

The qualified `some_table.t` and `some_table.i` specifications are easily understood. But what does the unqualified `t` and `i` refer to? Since this is a `SQL` function, the way Postgres resolves this ambiguity is well-defined. Yet, it is confusing the reader. If it was PLPGSQL, Postgres would in the standard configuration throw an error.

There are several ways to resolve this ambiguity. In our code base, we prefer to prefix function parameters with `p_`.

So, the function above should be defined as

``` {#bkmrk-create-or-replace-fu-1}
CREATE OR REPLACE FUNCTION ambig (p_i INT, p_t TEXT) RETURNS RECORD AS $$
    SELECT p_i, some_table.i
      FROM some_table
     WHERE some_table.t=p_t
$$ LANGUAGE sql
```

##### Return type specification

Postgres allows you to specify the return type in several ways. Even no explicit return type specification is valid:

``` {#bkmrk-create-or-replace-fu-2}
CREATE OR REPLACE FUNCTION namespace.function_name (
    p_param1 BIGINT,
    p_param2 TIMESTAMP,
    OUT c1 JSONB,
    OUT c2 TEXT
) AS $def$
...
$def$ ...
```

This function returns a single row with 2 columns named `c1` and `c2`.

All of the ways have their use cases. So recommendations here are few:

-   don't use a table name as a return type as in `RETURNS transaction.account` or `RETURNS SETOF transaction.account`. This creates action-at-a-distance vulnerabilities when the table structure changes.
-   prefer `RETURNS TABLE(...)` over the equivalent `(..., OUT c1 ..., OUT c2 ..., OUT ...) RETURNS SETOF RECORD`. The code layout rules for `RETURN TABLE` are the same as for the parameter list.

``` {#bkmrk-create-or-replace-fu-3}
CREATE OR REPLACE FUNCTION namespace.function_name (
    p_param1 BIGINT,
    p_param2 TIMESTAMP
) RETURNS TABLE (
    c1 JSONB,
    c2 TEXT
) AS $def$
...
$def$ ...
```

#### SQL functions

SQL functions can combine several statements but SQL has no flow control tools like if-else or loops. Only the last statement in a SQL function defines the output.

``` {#bkmrk-create-or-replace-fu-4}
CREATE OR REPLACE FUNCTION sleepy_beauty (
    p_how_long INTERVAL
) RETURNS TABLE (
    t TEXT
) AS $$
    SELECT pg_sleep(extract('epoch' FROM p_how_long));

    VALUES ('slept for ' || p_how_long);
$$ LANGUAGE sql
```

In terms of formatting, the function body should be indented by 4 spaces. Vertical separation of different statements is advised.

##### Inlining

One of the main advantages of SQL functions over any other programming language is that they can be inlined by the Postgres planner in certain conditions. This means the SQL engine does not see the actual function call. The call is replaced by the function body in the calling statement.

To be inlined, a function needs to be `STABLE`. But make sure [you know what that means](https://www.postgresql.org/docs/current/xfunc-volatility.html "volatility categories"). However, even if a function is stable it may not be able to be inlined. Just to name a few obstacles, if it is marked as `STRICT`, then for each call a check has to be done if a parameter is `NULL`. Similarly, if it is marked as `SECURITY definer` it cannot be inlined because the user context is different.

Inlining is important for query optimization. Let's have a look at 2 functions and corresponding execution plans.

``` {#bkmrk-create-or-replace-fu-5}
CREATE OR REPLACE FUNCTION get_account_by_id (p_id BIGINT)
RETURNS TABLE (
    client_loginid VARCHAR,
    balance NUMERIC,
    currency_code TEXT
) AS $def$
    SELECT a.client_loginid, a.balance, a.currency_code
      FROM transaction.account AS a
     WHERE a.id > p_id;
$def$ LANGUAGE sql STABLE
```

The non-inlineable version differs only in the missing word `STABLE` at the end.

For the non-inlineable version the query plan looks like this:

``` {#bkmrk-function-scan-on-get}
 Function Scan on get_account_by_id  (cost=0.25..10.25 rows=1000 width=96)
                                     (actual time=12.448..15.206 rows=45140 loops=1)
 Planning time: 0.029 ms
 Execution time: 17.299 ms
```

The inlineable one reads:

``` {#bkmrk-seq-scan-on-account-}
 Seq Scan on account a  (cost=0.00..951.25 rows=45140 width=16)
                        (actual time=0.011..9.826 rows=45140 loops=1)
   Filter: (id > '12'::bigint)
 Planning time: 0.163 ms
 Execution time: 11.909 ms
```

As you can see, the rows estimate for the function call is 1000. This is a constant which can be set when the function is created. It has nothing to do with the actual data. Similarly, the cost estimate is set when the function is created.

In contrast, the inlined plan shows a scan of the table. That also means the table's statistics are used to calculate rows and cost estimates.

If this is the outer-most query like here:

``` {#bkmrk-select-%2A-from-get_ac}
SELECT * FROM get_account_by_id(12)
```

then these cost and rows estimates are not so important. Even the runtime, 12msec versus 17msec, is not so much of a difference. However, if it is part of a more complex query, then having realistic cost estimates is crucial in choosing good plans.

Postgres' query planner produces a tree of nodes which describes how a query will be executed. A `seq scan` node for instance scans the entire table and produces rows matching a certain condition. Now, if the next node above that `seq scan` is a `limit` node, the scan can be stopped as soon as the required number of rows has been produced. *Pushing down* now means to tell the `seq scan` node when to stop.

A function call is a barrier for doing so. This can be seen here.

``` {#bkmrk-select-%2A-from-get_ac-0}
SELECT * FROM get_account_by_id(12) LIMIT 2
```

The non-inlineable function call looks very similar to the query without the limit.

``` {#bkmrk-limit-%28cost%3D0.25..0.}
 Limit  (cost=0.25..0.27 rows=2 width=96)
        (actual time=13.031..13.032 rows=2 loops=1)
   ->  Function Scan on get_account_by_id  (cost=0.25..10.25 rows=1000 width=96)
                                           (actual time=13.029..13.029 rows=2 loops=1)
 Planning time: 0.032 ms
 Execution time: 13.446 ms
```

However, the inlineable one \>500 times faster.

``` {#bkmrk-limit-%28cost%3D0.00..0.}
 Limit  (cost=0.00..0.04 rows=2 width=16)
        (actual time=0.011..0.012 rows=2 loops=1)
   ->  Seq Scan on account a  (cost=0.00..951.25 rows=45140 width=16)
                              (actual time=0.010..0.011 rows=2 loops=1)
         Filter: (id > '12'::bigint)
 Planning time: 0.144 ms
 Execution time: 0.022 ms
```

This is a contrived example. The effect in real life depends on the circumstances.

#### PLPGSQL functions
