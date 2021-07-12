--
-- PostgreSQL database dump
--

-- Dumped from database version 13.3 (Ubuntu 13.3-1.pgdg20.04+1)
-- Dumped by pg_dump version 13.3 (Ubuntu 13.3-1.pgdg20.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

CREATE TYPE public.actiontype AS ENUM (
    'REMINDER',
    'INFRACTION',
    'NOTIFICATION'
);

CREATE TYPE public.infractiontype AS ENUM (
    'WARN',
    'MUTE',
    'KICK',
    'UNBAN',
    'TEMPBAN',
    'PERMABAN'
);

CREATE TYPE public.loggingtype AS ENUM (
    'MOD_ACTIONS'
);

SET default_tablespace = '';
SET default_table_access_method = heap;

CREATE TABLE public.infractions (
    id bigint NOT NULL,
    action_id bigint,
    inf_type public.infractiontype,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    guild_id bigint,
    mod_id bigint,
    target_id bigint,
    reason text
);

CREATE FUNCTION public.get_infractions(_guild_id bigint, _inf_id bigint, _target_id bigint, _mod_id bigint) RETURNS SETOF public.infractions
    LANGUAGE plpgsql
    AS $$
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
    _sql := _sql || ' limit 500;';

    return query execute _sql;
end;
$$;

CREATE TABLE public.actions (
    id bigint NOT NULL,
    action_type public.actiontype DEFAULT 'REMINDER'::public.actiontype,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    trigger_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    author_id bigint,
    guild_id bigint,
    channel_id bigint,
    message_id bigint,
    extra jsonb
);

ALTER TABLE public.actions ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.actions_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

CREATE TABLE public.blacklisted (
    user_id bigint NOT NULL,
    reason text DEFAULT 'because'::text
);

CREATE TABLE public.guilds (
    guild_id bigint NOT NULL,
    prefix character varying(16),
    lang character varying(16) DEFAULT 'en_US'::character varying,
    tz character varying(32) DEFAULT 'UTC'::character varying
);

ALTER TABLE public.infractions ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.infractions_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

CREATE TABLE public.logging (
    guild_id bigint,
    log_type public.loggingtype,
    channel_id bigint
);

CREATE TABLE public.mod_settings (
    guild_id bigint,
    mute_role bigint,
    mod_roles bigint[] DEFAULT '{}'::bigint[],
    audit_infractions boolean DEFAULT true,
    dm_targets boolean DEFAULT false
);

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.blacklisted
    ADD CONSTRAINT blacklisted_pkey PRIMARY KEY (user_id);

ALTER TABLE ONLY public.guilds
    ADD CONSTRAINT guilds_pkey PRIMARY KEY (guild_id);

ALTER TABLE ONLY public.infractions
    ADD CONSTRAINT infractions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.mod_settings
    ADD CONSTRAINT mod_settings_guild_id_key UNIQUE (guild_id);

CREATE INDEX actions_author_id_guild_id_idx ON public.actions USING btree (author_id, guild_id);
CREATE INDEX actions_trigger_at_created_at_idx ON public.actions USING btree (trigger_at, created_at);
CREATE INDEX infractions_action_id_idx ON public.infractions USING btree (action_id);
CREATE INDEX infractions_guild_id_mod_id_target_id_idx ON public.infractions USING btree (guild_id, mod_id, target_id);
CREATE INDEX logging_guild_id_idx ON public.logging USING btree (guild_id);

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_fk_guild_id FOREIGN KEY (guild_id) REFERENCES public.guilds(guild_id) ON DELETE CASCADE;

ALTER TABLE ONLY public.infractions
    ADD CONSTRAINT infractions_actions_id_fk FOREIGN KEY (action_id) REFERENCES public.actions(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.logging
    ADD CONSTRAINT logging_fk_guild_id FOREIGN KEY (guild_id) REFERENCES public.guilds(guild_id) ON DELETE CASCADE;

ALTER TABLE ONLY public.mod_settings
    ADD CONSTRAINT mod_settings_fk_guild_id FOREIGN KEY (guild_id) REFERENCES public.guilds(guild_id) ON DELETE CASCADE;

--
-- PostgreSQL database dump complete
--
