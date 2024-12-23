--
-- to list all subjects having permissions to specific object
--
create or replace function dap.shareholders( object uuid ) returns table (
    id uuid, kind text, permit text
) as $$
    select distinct s.entity, e.kind, r.permit from
    dap.rights r
    join (
        select distinct
            (dap.sweep_down(subject)).*
        from dap.rights
        where object = $1
    ) s
    on r.subject = s.owner
    join dap.entities e
    on e.id = s.entity
    where r.object = $1
    ;
$$ language sql;

