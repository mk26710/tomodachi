create type InfractionType as enum ('WARN', 'MUTE', 'KICK', 'UNBAN', 'TEMPBAN', 'PERMABAN');
create type ActionType as enum ('REMINDER', 'INFRACTION', 'NOTIFICATION');
create type LoggingType as enum ('MOD_ACTIONS');

-- guilds table
create table if not exists public.guilds
(
    guild_id bigint primary key,
    prefix   varchar(16),
    lang     varchar(16) default 'en_US'::varchar,
    tz       varchar(32) default 'UTC'::varchar
);

-- blacklisted table
create table if not exists public.blacklisted
(
    user_id bigint primary key,
    reason  text default 'because'::text
);

-- actions
create table public.actions
(
    id          bigint generated always as identity (start with 1000) primary key,
    action_type ActionType  default 'REMINDER'::ActionType,
    created_at  timestamptz default CURRENT_TIMESTAMP,
    trigger_at  timestamptz default CURRENT_TIMESTAMP,
    author_id   bigint,
    guild_id    bigint,
    channel_id  bigint,
    message_id  bigint,
    extra       jsonb,

    constraint actions_fk_guild_id
        foreign key (guild_id) references public.guilds
            on delete cascade
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
    inf_type   infractiontype,
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

drop function if exists get_infractions;

create or replace function get_infractions(_guild_id bigint, _inf_id bigint, _target_id bigint, _mod_id bigint)
    returns setof infractions
    language plpgsql
as
$$
declare
    _sql text;
begin
    _sql := format('select * from infractions i where i.guild_id = %L', _guild_id);
    if _inf_id is not null then
        _sql := _sql || format(' and i.id = %L ', _inf_id);
    end if;
    if _target_id is not null then
        _sql := _sql || format(' and i.target_id = %L ', _target_id);
    end if;
    if _mod_id is not null then
        _sql := _sql || format(' and i.mod_id = %L ', _mod_id);
    end if;
    _sql := _sql || ';';

    return query execute _sql;
end;
$$;

-- mod_settings
create table if not exists public.mod_settings
(
    guild_id          bigint,
    mute_role         bigint,
    mod_roles         bigint[] default '{}'::bigint[],
    audit_infractions boolean  default true,

    unique (guild_id),

    constraint mod_settings_fk_guild_id
        foreign key (guild_id)
            references public.guilds (guild_id)
            on delete cascade
);

-- logging
create table if not exists public.logging
(
    guild_id   bigint,
    log_type   loggingtype,
    channel_id bigint,

    constraint logging_fk_guild_id
        foreign key (guild_id)
            references public.guilds (guild_id)
            on delete cascade
);

create index logging_guild_id_idx
    on public.logging (guild_id);
