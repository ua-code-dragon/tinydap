--
-- to render list of own and inherit permissions of specific subject to object, TODO: permission overlap rule, not-mask
--
create or replace function dap.effective_rights( subect uuid, object uuid) returns setof text as $$
    select permit
    from dap.rights r
    join (
        select distinct (dap.sweep_up(subject)).* from dap.rights
        where subject = $1 and object = $2
    ) e on r.subject = e.owner and r.object = $2
;
$$ language sql;


