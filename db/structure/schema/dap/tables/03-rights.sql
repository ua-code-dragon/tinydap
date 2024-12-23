create table if not exists dap.rights (
    subject uuid not null references dap.entities (id) on update cascade on delete cascade deferrable initially deferred,
    object uuid not null references dap.entities (id) on update cascade on delete cascade deferrable initially deferred,
    permit varchar(32) not null
);

create index if not exists i_dap_rights_s on dap.rights ( subject );
create index if not exists i_dap_rights_o on dap.rights ( object );
create index if not exists i_dap_rights_p on dap.rights ( permit );



