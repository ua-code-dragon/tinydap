--
-- to list nodes in deep down from specific node with effective owner of each level
--
create or replace function dap.sweep_down ( id uuid) returns table (
    entity uuid,
    owner uuid
) as $$
with recursive tree_down as (
    select t1.entity, t1.parent
    from dap.directory t1
    where t1.parent = $1
    union all
    select t2.entity, t2.parent
    from dap.directory t2
    join tree_down on t2.parent = tree_down.entity
)
select distinct *
from (
    select $1,$1
    union all
    select entity,parent from tree_down
    union all
    select parent,parent from tree_down
) q
;
$$ language sql;

