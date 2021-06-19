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



