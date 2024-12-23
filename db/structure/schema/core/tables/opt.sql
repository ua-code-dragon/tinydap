create table if not exists core.opt
(
    section character varying not null,
    key character varying not null,
    value character varying,
    "default" character varying,
    "type" character varying,
    "group" character varying default 'common'::character varying,
    weight integer default 0,
    constraint opt_pkey primary key (section, key)
);


