-- actions table
create table actions
(
    id bigserial,
    sort text default 'REMINDER' not null,
    created_at timestamp with time zone default CURRENT_TIMESTAMP not null,
    trigger_at timestamp with time zone default CURRENT_TIMESTAMP not null,
    author_id bigint not null,
    guild_id bigint default NULL,
    channel_id bigint not null,
    message_id bigint not null,
    extra jsonb default NULL
);

create unique index actions_id_uindex
    on actions (id);

create index actions_created_at_index
    on actions (created_at);

create index actions_trigger_at_index
    on actions (trigger_at);

alter table actions
    add constraint actions_pk
        primary key (id);

-- reminders table
create table reminders
(
    id bigserial,
    created_at timestamp with time zone default CURRENT_TIMESTAMP not null,
    trigger_at timestamp with time zone default CURRENT_TIMESTAMP not null,
    author_id bigint not null,
    guild_id bigint,
    channel_id bigint not null,
    message_id bigint not null,
    contents text
);

create unique index reminders_id_uindex
    on reminders (id);

alter table reminders
    add constraint reminders_pk
        primary key (id);

-- guilds table
-- auto-generated definition
create table guilds
(
    guild_id bigint                                         not null
        constraint guilds_pkey
            primary key,
    prefix   varchar(16),
    lang     varchar(16) default 'en_US'::character varying not null,
    tz       varchar(32) default 'UTC'::character varying   not null
);

create index ix_guilds_guild_id
    on guilds (guild_id);

-- blacklisted table
-- auto-generated definition
create table blacklisted
(
    user_id bigint not null
        constraint blacklisted_pkey
            primary key,
    reason  text default 'because'::text
);

create index ix_blacklisted_user_id
    on blacklisted (user_id);

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

