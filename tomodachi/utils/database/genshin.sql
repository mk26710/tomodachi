-- teapot table
create table teapot
(
	id bigint not null,
	energy int not null
);

create unique index teapot_id_uindex
	on teapot (id);

alter table teapot
	add constraint teapot_pk
		primary key (id);

create function tea(
    _id bigint,
    out id bigint,
    out energy integer,
    out currency integer,
    out bounty integer
)
    returns setof record
    language plpgsql
as
$$
begin
    return query select t.id,
                        t.energy,
                        case
                            when t.energy >= 20000 then 30
                            when t.energy >= 15000 then 28
                            when t.energy >= 12000 then 26
                            when t.energy >= 10000 then 24
                            when t.energy >= 8000 then 22
                            when t.energy >= 6000 then 20
                            when t.energy >= 4500 then 16
                            when t.energy >= 3000 then 12
                            when t.energy >= 2000 then 8
                            when t.energy >= 0 then 4
                            end currency,
                        case
                            when t.energy >= 12000 then 5
                            when t.energy >= 6000 then 4
                            when t.energy >= 3000 then 3
                            when t.energy >= 0 then 2
                            end bounty
                 from teapot t
                 where t.id = _id;
end
$$;