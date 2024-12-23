create or replace function dap.api_revoke(isubject uuid, iobject uuid, ipermit varchar(32), out nrows integer ) as $$
begin
    delete from dap.rights where subject = isubject and object =  iobject and permit =  ipermit;
    get diagnostics nrows = row_count;
end;
$$ language plpgsql;


