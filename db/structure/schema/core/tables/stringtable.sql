create table if not exists core.stringtable
(
    section character varying(32) not null,
    lang character varying(2) not null,
    key character varying not null,
    value text
);

create unique index if not exists stringtable_key on core.stringtable using btree
    (section collate pg_catalog."default", lang collate pg_catalog."default", key collate pg_catalog."default");


