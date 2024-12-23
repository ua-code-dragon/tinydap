create or replace function public._s(isect varchar(32), ilang varchar(2), ikey varchar) returns text as $$ select core.str ($1, $2, $3); $$ language sql immutable;
create or replace function public._s(isect varchar(32), ikey varchar) returns text as $$ select core.str ($1, $2); $$ language sql immutable;


create or replace function public._sa(isect varchar(32), ilang varchar(2), ikey text[]) returns text[] as $$ select core.astr ($1, $2, $3); $$ language sql immutable;
create or replace function public._sa(isect varchar(32), ikey text[]) returns text[] as $$ select core.astr ($1, $2); $$ language sql immutable;

