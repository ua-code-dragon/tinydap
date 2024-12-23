
create table if not exists public.users ( 
    id uuid not null primary key,
    username varchar(128), -- illustrates multikey link see unique index
    fullname varchar(128),
    email varchar(128),
    phone varchar(128),
    ctime timestamptz not null default current_timestamp,
    utime timestamptz not null default current_timestamp,
    enable boolean not null default true,
    password varchar(256),
    roles text[],
    requiz jsonb, -- illustrates quiz pwd repair
    meta jsonb
);

create index if not exists i_users_ctime on public.users (ctime);
create index if not exists i_users_utime on public.users (utime);
create index if not exists i_users_enable on public.users (enable);
create index if not exists i_users_roles on public.users using gin (roles);

create unique index if not exists i_users_key_username on public.users ( id, username );
create unique index if not exists i_users_key_email on public.users ( id, email );
create unique index if not exists i_users_key_phone on public.users ( id, phone );

