--truncate article and thread
TRUNCATE thread, article;

--seq reset
SELECT setval ('article_id_seq', 1, false);

--TEST thread insert
INSERT INTO  thread (id, threadname, board_id) VALUES (1, 'FUCK', 7);

INSERT 
INTO "article"( 
  "id"
  ,"article_count"
  ,"pub_date"
  ,"userid"
  ,"name"
  ,"article"
  ,"thread_id"
) 
SELECT
  --(SELECT id FROM article ORDER BY id DESC LIMIT 1) + i
   nextval('article_id_seq')
  ,i
  ,NOW()
  ,format('test_%s', i)
  ,format('test_%s', i)
  ,format('test_ariticle %s', i)
  ,1
FROM
  generate_series(1, 999) as i; 
