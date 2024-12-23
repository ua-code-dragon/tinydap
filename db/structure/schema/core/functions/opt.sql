create or replace function core.getopt(varchar, varchar) returns varchar as $$
    select "value" from (select "value" from core.opt where "section" = $1 and "key" = $2 union all select null as "value") as q order by "value" limit 1;
$$ language sql immutable;

create or replace function core.setopt(varchar, varchar, varchar) returns integer as $$
    update core.opt set "value" = $3 where "section" = $1 and "key" = $2 returning 1 as setopt;
$$ language sql immutable;

create or replace function core.putopt(varchar, varchar, varchar, varchar, varchar, varchar, integer) returns void as $$
    insert into core.opt ( "section", "key", "value", "default", "type", "group", "weight" ) values ( $1, $2, $3, $4, $5, $6, $7 )
    on conflict (section,key) do update
        set "default" = $4, "type" = $5, "value" = case when core.opt.value = core.opt.default then $4 else core.opt.value end where core.opt."section" = $1 and core.opt."key" = $2;
$$ language sql;


create or replace function public._o(varchar) returns varchar as $$ select core.getopt('public',$1); $$ language sql immutable;
create or replace function public._do(varchar) returns varchar as $$ select core.getopt('dap',$1); $$ language sql immutable;

