--
-- to list nodes in the tree path from specific leave up to root with effective owner of each level
--
create or replace function dap.sweep_up ( id uuid) returns table (
    entity uuid,
    owner uuid
) as $$
with recursive tree_up as (
    select t1.entity, t1.parent
    from dap.directory t1
    where t1.entity = $1
    union all
    select t2.entity, t2.parent
    from dap.directory t2
    join tree_up on t2.entity = tree_up.parent
)
select distinct *
from (
    select $1,$1
    union all
    select entity,parent from tree_up
    union all
    select parent,parent from tree_up
) q
;
$$ language sql;

