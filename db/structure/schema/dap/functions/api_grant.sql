
create or replace function dap.api_grant(isubject uuid, iobject uuid, ipermit varchar(32), out nrows integer ) as $$
begin
    insert into dap.rights (subject, object, permit) values(isubject, iobject, ipermit);
    get diagnostics nrows = row_count;
end;
$$ language plpgsql;

