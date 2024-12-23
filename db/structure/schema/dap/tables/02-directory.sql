create table if not exists dap.directory (
    entity  uuid not null references dap.entities (id) on update cascade on delete cascade deferrable initially deferred,
    parent  uuid not null references dap.entities (id) on update cascade on delete cascade deferrable initially deferred
);

create index if not exists i_dap_dir_entity on dap.directory ( entity );
create index if not exists i_dap_dir_parent on dap.directory ( parent );

