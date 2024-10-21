--
-- PostgreSQL database dump
--

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: orthoepy_problems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.orthoepy_problems (
    word text NOT NULL,
    counter integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.orthoepy_problems OWNER TO postgres;

--
-- Name: uchus_online; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.uchus_online (
    user_id bigint NOT NULL,
    min_complexity integer DEFAULT 0,
    max_complexity integer DEFAULT 100,
    complexity_asc boolean DEFAULT true,
    done integer[] DEFAULT '{}'::integer[]
);


ALTER TABLE public.uchus_online OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id bigint NOT NULL,
    upscaled boolean DEFAULT false,
    username text,
    user_name text,
    user_surname text,
    admin boolean DEFAULT false,
    aliases jsonb DEFAULT '{}'::jsonb,
    ai_access boolean DEFAULT false,
    openai_tokens integer DEFAULT 0
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: wordcloud_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wordcloud_settings (
    user_id bigint NOT NULL,
    background_color text DEFAULT 'white'::text,
    colormap text DEFAULT 'viridis'::text,
    scale double precision DEFAULT 1,
    width integer DEFAULT 1600,
    height integer DEFAULT 800,
    min_font_size integer DEFAULT 4,
    max_font_size integer,
    max_words integer DEFAULT 200
);


ALTER TABLE public.wordcloud_settings OWNER TO postgres;