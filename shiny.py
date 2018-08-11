import sqlparse


def parse(sql):
	parsed = sqlparse.parse(sql)
	create_statements = [statement for statement in parsed if statement.get_type()=='CREATE']
