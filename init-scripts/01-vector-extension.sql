CREATE EXTENSION IF NOT EXISTS vector;
CREATE INDEX ON movie USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
