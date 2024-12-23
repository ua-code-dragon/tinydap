create or replace function dap.api_directory( ientity uuid, iparent uuid, out nrows integer ) as $$ -- if null -> delete
begin
    if iparent isnull then
        delete from dap.directory where entity = ientity;
    else
        insert into dap.directory (entity, parent) values (ientity, iparent);
    end if;
    get diagnostics nrows = row_count;
end;
$$ language plpgsql;


