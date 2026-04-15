-- This is an export of ddl via alembic from locally testing postgres + pgvector

BEGIN;


-- Running upgrade  -> 8b86002b0bda

CREATE TABLE collection (
    slug VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    id UUID NOT NULL,
    created TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (slug)
);

CREATE TABLE tag (
    name VARCHAR NOT NULL,
    id UUID NOT NULL,
    created TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (name)
);

CREATE TABLE topic (
    title VARCHAR NOT NULL,
    slug VARCHAR NOT NULL,
    collection_id UUID NOT NULL,
    body TEXT NOT NULL,
    visualisation_data JSONB,
    search_vector TSVECTOR,
    id UUID NOT NULL,
    created TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(collection_id) REFERENCES collection (id),
    UNIQUE (collection_id, slug)
);

CREATE INDEX ix_topic_search_vector ON topic USING gin (search_vector);

CREATE TYPE linktype AS ENUM ('website', 'dataset', 'api');

CREATE TABLE link (
    url VARCHAR NOT NULL,
    link_text VARCHAR NOT NULL,
    link_type linktype NOT NULL,
    topic_id UUID NOT NULL,
    id UUID NOT NULL,
    created TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(topic_id) REFERENCES topic (id)
);

CREATE TABLE topic_tag (
    topic_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    PRIMARY KEY (topic_id, tag_id),
    FOREIGN KEY(tag_id) REFERENCES tag (id),
    FOREIGN KEY(topic_id) REFERENCES topic (id)
);

CREATE FUNCTION topic_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.body, '')), 'B');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;;

CREATE TRIGGER topic_search_vector_trigger
        BEFORE INSERT OR UPDATE OF title, body ON topic
        FOR EACH ROW EXECUTE FUNCTION topic_search_vector_update();;

INSERT INTO alembic_version (version_num) VALUES ('8b86002b0bda') RETURNING alembic_version.version_num;

-- Running upgrade 8b86002b0bda -> a1f2c3d4e5f6

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE topic ADD COLUMN embedding VECTOR(384);

ALTER TABLE topic ADD COLUMN content_hash VARCHAR(64);

CREATE INDEX ix_topic_embedding ON topic USING hnsw (embedding vector_cosine_ops);

UPDATE alembic_version SET version_num='a1f2c3d4e5f6' WHERE alembic_version.version_num = '8b86002b0bda';

COMMIT;
