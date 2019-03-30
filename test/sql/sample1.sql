SELECT *
FROM (%(test/sql/sample2.sql)s) s2
JOIN (%(test/sql/sample3.sql)s) s3 ON (s3.sample2_id=s2.id)
WHERE s2.id=%(s2_id)s
