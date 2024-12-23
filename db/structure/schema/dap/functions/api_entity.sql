create or replace function dap.api_entity(iid uuid, ikind varchar(32), iname text, idata jsonb, out nrows integer) as $$ -- ikind is null === delete, else === create/update
begin
    if ikind isnull then
        delete from dap.entities where id = iid;
    else
        insert into dap.entities
        (id, kind,name,data)
        values( iid, ikind, iname, idata )
        on conflict (id) do update set
            kind = ikind, name = iname, data = idata
        ;
    end if;
    get diagnostics nrows = row_count;
end;
$$ language plpgsql;


