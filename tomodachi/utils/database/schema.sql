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

-- actions
create table public.actions
(
    id          bigint generated always as identity (start with 1000) primary key,
    action_type text        default 'REMINDER'::text,
    created_at  timestamptz default CURRENT_TIMESTAMP,
    trigger_at  timestamptz default CURRENT_TIMESTAMP,
    author_id   bigint,
    guild_id    bigint,
    channel_id  bigint,
    message_id  bigint,
    extra       jsonb
);

create index actions_trigger_at_created_at_idx
    on public.actions (trigger_at, created_at);

create index actions_author_id_guild_id_idx
    on public.actions (author_id, guild_id);




-- infractions
create table if not exists public.infractions
(
    id         bigint generated always as identity (start with 1000) primary key,
    action_id  bigint,
    inf_type   text,
    created_at timestamptz default CURRENT_TIMESTAMP,
    expires_at timestamptz default CURRENT_TIMESTAMP,
    guild_id   bigint,
    mod_id     bigint,
    target_id  bigint,
    reason     text,
    constraint infractions_actions_id_fk
        foreign key (action_id) references public.actions
            on delete set null
);

create index infractions_action_id_idx
    on public.infractions (action_id);

create index infractions_guild_id_mod_id_target_id_idx
    on public.infractions (guild_id, mod_id, target_id);