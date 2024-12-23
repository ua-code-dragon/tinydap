create or replace function dap.directory_unique_t() returns trigger as $$
begin
    if exists ( select 1 from dap.directory where entity = new.entity and parent = new.parent or entity = new.parent and parent = new.entity or new.entity = new.parent )
    then
        raise exception 'Directory unique violation!';
    end if;
    return new;
end;
$$ language plpgsql;

drop trigger if exists t_dap_directory_unique on dap.directory;
create trigger t_dap_directory_unique before insert or update on dap.directory for each row execute function dap.directory_unique_t();

