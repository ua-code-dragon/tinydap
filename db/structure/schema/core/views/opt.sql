create or replace view core.v_listopt as
    select o.section, o.key, o.value, o."default", o.type, o."group", o.weight, s.lang, s.value AS name
    from core.opt o
        join core.stringtable s ON s.section::text = 'opt'::text AND s.key::text = ((o.section::text || '.'::text) || o.key::text);

