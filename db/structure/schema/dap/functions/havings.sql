--
-- to list all objects the specific subject has permissions to
--
create or replace function dap.havings( subject uuid ) returns table (
    id uuid, kind text, permit text
) as $$
    select distinct entity, e.kind, permit
    from (
        select
            (dap.sweep_down(object)).entity,
            permit
        from (
            select distinct r.object, r.permit
            from
                dap.rights r
                join dap.sweep_down($1) s
                on r.subject = s.owner
        ) q
    ) qq
    join dap.entities e
    on e.id = qq.entity
    ;
$$ language sql;

