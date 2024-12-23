create or replace function lib.idx(anyarray, anyelement) returns int as $$
    select i from ( select generate_series(array_lower($1,1),array_upper($1,1))) g(i) where $1[i] = $2 limit 1;
$$ language sql immutable;
 
