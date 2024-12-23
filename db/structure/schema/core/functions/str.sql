create or replace function core.str( isect varchar(32), ilang varchar(2), ikey varchar ) returns text as $$
    select value from core.stringtable where section = $1 and lang = $2 and key = $3;
$$ language sql immutable;

create or replace function core.str ( isect varchar(32), ikey varchar ) returns text as $$
    select value from core.stringtable
    where section = $1 and key = $2
    order by lib.idx( public._o('language_priority')::text[], core.stringtable.lang::text )
    limit 1;
$$ language sql immutable;

create or replace function core.astr( isect varchar(32), ilang varchar(2), ikey text[] ) returns text[] as $$
    select array_agg(value) from unnest($3) left join core.stringtable s on s.section = $1 and s.lang = $2 and s.key = unnest;
$$ language sql immutable;

create or replace function core.astr ( isect varchar(32), ikey text[] ) returns text[] as $$
    select array_agg(value) from (
    select first_value(value) over (partition by section, key order by lib.idx( public._o('language_priority')::text[], s.lang::text )) as value
    from unnest($2)
    left join core.stringtable s on s.key = unnest
    and s.section = $1
    ) q;
$$ language sql immutable;
