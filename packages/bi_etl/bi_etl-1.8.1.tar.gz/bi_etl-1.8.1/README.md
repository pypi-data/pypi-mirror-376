# bi_etl Python ETL Framework for BI

[![pypi](https://img.shields.io/pypi/v/bi-etl.svg)](https://pypi.org/project/bi-etl/)
[![license](https://img.shields.io/github/license/arcann/config_wrangler.svg)](https://github.com/arcann/config_wrangler/blob/master/LICENSE)
[![Python package](https://github.com/arcann/bi_etl/actions/workflows/unit_test.yml/badge.svg)](https://github.com/arcann/bi_etl/actions/workflows/unit_test.yml)

## Docs

[Please see the documentation site for detailed documentation.](https://bietl.dev/bi_etl/)

Python based ETL (Extract Transform Load) framework geared towards BI databases in particular. 
The goal of the project is to create reusable objects with typical technical transformations used in loading dimension tables.

## Guiding Design Principles
1. Don’t Repeat Yourself (DRY).

1. The source or target of an ETL owns the metadata (list of columns and data types). The ETL generally has no reason to define those again unless the ETL requires a change. If a datatype must be changed, only that one column’s new type should be specified. If a column name must be changed, only the source & target column names that differ should be specified.

1. Data Quality is King

1. Data quality is more important than performance. For example, the process should fail before truncating data contents (i.e. loading 6 characters into a 5 character field) even if that means sacrificing some load performance.

1. Give helpful error messages.

1. Make it as easy as possible to create re-usable modules.

1. SQL is a very powerful transformation language. The Transform Extract Load (TEL) model should be supported.