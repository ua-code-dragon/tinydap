create table if not exists core.version (
     moment   timestamp with time zone not null default now()
    ,module   character varying                 
    ,major    integer                           
    ,minor    integer                           
    ,release  integer                           
    ,rc       integer                           
    ,build    integer                           
    ,revision character varying                 
    ,memo     character varying                 
);

