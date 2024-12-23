create table if not exists dap.entities (
    id uuid not null default gen_random_uuid() primary key,
    kind varchar(32), -- for example [user, group, document, folder]
    name varchar(128),
    data jsonb
);

create index if not exists i_dap_entities_kind on dap.entities (kind);


