--
-- PostgreSQL database dump
--

\restrict dD648CtstXmGVVpdiYx2Ugot4uiUZevRwkgaZuPXiFkBBxrecb99gIygM30oGMp

-- Dumped from database version 18.1 (Debian 18.1-1.pgdg13+2)
-- Dumped by pg_dump version 18.1 (Debian 18.1-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agent_personas; Type: TABLE; Schema: public; Owner: jarvis
--

CREATE TABLE public.agent_personas (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    system_prompt text NOT NULL,
    weight numeric(3,2) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.agent_personas OWNER TO jarvis;

--
-- Name: COLUMN agent_personas.name; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.agent_personas.name IS 'Rickiest Rick, Supportive Rick, etc.';


--
-- Name: COLUMN agent_personas.weight; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.agent_personas.weight IS '0.40, 0.20, 0.10, 0.30 (must sum to 1.00)';


--
-- Name: agent_personas_id_seq; Type: SEQUENCE; Schema: public; Owner: jarvis
--

CREATE SEQUENCE public.agent_personas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.agent_personas_id_seq OWNER TO jarvis;

--
-- Name: agent_personas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: jarvis
--

ALTER SEQUENCE public.agent_personas_id_seq OWNED BY public.agent_personas.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: jarvis
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO jarvis;

--
-- Name: conversations; Type: TABLE; Schema: public; Owner: jarvis
--

CREATE TABLE public.conversations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.conversations OWNER TO jarvis;

--
-- Name: COLUMN conversations.user_id; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.conversations.user_id IS 'Future: multi-user support';


--
-- Name: documents; Type: TABLE; Schema: public; Owner: jarvis
--

CREATE TABLE public.documents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    doc_key character varying(500) NOT NULL,
    content text NOT NULL,
    source_file character varying(500) NOT NULL,
    domain character varying(100),
    metadata jsonb,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.documents OWNER TO jarvis;

--
-- Name: COLUMN documents.doc_key; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.documents.doc_key IS 'Stable key e.g. file::/path/to/doc.pdf';


--
-- Name: domain_snapshots; Type: TABLE; Schema: public; Owner: jarvis
--

CREATE TABLE public.domain_snapshots (
    snapshot_date date NOT NULL,
    collection_name character varying(100) NOT NULL,
    domain character varying(200) NOT NULL,
    point_count integer NOT NULL,
    enrichment_pct double precision
);


ALTER TABLE public.domain_snapshots OWNER TO jarvis;

--
-- Name: knowledge_domains; Type: TABLE; Schema: public; Owner: jarvis
--

CREATE TABLE public.knowledge_domains (
    id integer NOT NULL,
    key character varying(100) NOT NULL,
    label character varying(200) NOT NULL,
    parent_key character varying(100),
    kind character varying(50) DEFAULT 'generic'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.knowledge_domains OWNER TO jarvis;

--
-- Name: COLUMN knowledge_domains.key; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.knowledge_domains.key IS 'Stable domain key, e.g. ''architecture.core'', ''history.modern''';


--
-- Name: COLUMN knowledge_domains.label; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.knowledge_domains.label IS 'Human-readable label for the domain';


--
-- Name: COLUMN knowledge_domains.parent_key; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.knowledge_domains.parent_key IS 'Optional parent domain key for hierarchical taxonomy';


--
-- Name: COLUMN knowledge_domains.kind; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.knowledge_domains.kind IS 'Category of domain: human_science | product_branch | infra | generic';


--
-- Name: knowledge_domains_id_seq; Type: SEQUENCE; Schema: public; Owner: jarvis
--

CREATE SEQUENCE public.knowledge_domains_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.knowledge_domains_id_seq OWNER TO jarvis;

--
-- Name: knowledge_domains_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: jarvis
--

ALTER SEQUENCE public.knowledge_domains_id_seq OWNED BY public.knowledge_domains.id;


--
-- Name: llm_providers; Type: TABLE; Schema: public; Owner: jarvis
--

CREATE TABLE public.llm_providers (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    type character varying(50) NOT NULL,
    priority integer NOT NULL,
    quota_limit bigint,
    tokens_used bigint NOT NULL,
    last_reset timestamp with time zone,
    api_key_env character varying(100),
    is_active boolean NOT NULL
);


ALTER TABLE public.llm_providers OWNER TO jarvis;

--
-- Name: COLUMN llm_providers.name; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.llm_providers.name IS 'openrouter, together_ai, etc.';


--
-- Name: COLUMN llm_providers.type; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.llm_providers.type IS 'free_tier | paid';


--
-- Name: COLUMN llm_providers.priority; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.llm_providers.priority IS 'Lower = higher priority';


--
-- Name: COLUMN llm_providers.quota_limit; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.llm_providers.quota_limit IS 'Tokens per month (if known)';


--
-- Name: COLUMN llm_providers.api_key_env; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.llm_providers.api_key_env IS 'ENV variable name';


--
-- Name: llm_providers_id_seq; Type: SEQUENCE; Schema: public; Owner: jarvis
--

CREATE SEQUENCE public.llm_providers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.llm_providers_id_seq OWNER TO jarvis;

--
-- Name: llm_providers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: jarvis
--

ALTER SEQUENCE public.llm_providers_id_seq OWNED BY public.llm_providers.id;


--
-- Name: llm_usage_log; Type: TABLE; Schema: public; Owner: jarvis
--

CREATE TABLE public.llm_usage_log (
    id bigint NOT NULL,
    provider_id integer NOT NULL,
    message_id uuid,
    model character varying(100) NOT NULL,
    tokens_input integer NOT NULL,
    tokens_output integer NOT NULL,
    cost_usd numeric(10,6) NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.llm_usage_log OWNER TO jarvis;

--
-- Name: TABLE llm_usage_log; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON TABLE public.llm_usage_log IS 'Detailed LLM API call tracking for cost analysis';


--
-- Name: llm_usage_log_id_seq; Type: SEQUENCE; Schema: public; Owner: jarvis
--

CREATE SEQUENCE public.llm_usage_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.llm_usage_log_id_seq OWNER TO jarvis;

--
-- Name: llm_usage_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: jarvis
--

ALTER SEQUENCE public.llm_usage_log_id_seq OWNED BY public.llm_usage_log.id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: jarvis
--

CREATE TABLE public.messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    conversation_id uuid NOT NULL,
    role character varying(50) NOT NULL,
    content text NOT NULL,
    agent_persona character varying(100),
    cost_usd numeric(10,6),
    provider character varying(100),
    model character varying(100),
    token_count integer,
    created_at timestamp with time zone NOT NULL,
    citation_provenance jsonb,
    voting_metadata jsonb
);


ALTER TABLE public.messages OWNER TO jarvis;

--
-- Name: TABLE messages; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON TABLE public.messages IS 'Individual messages within conversations with LLM metadata';


--
-- Name: COLUMN messages.role; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.messages.role IS 'user | assistant | system';


--
-- Name: COLUMN messages.agent_persona; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.messages.agent_persona IS 'Which Rick responded (if applicable)';


--
-- Name: COLUMN messages.citation_provenance; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON COLUMN public.messages.citation_provenance IS 'Stored citation metadata for assistant messages (sources[], scores, hashes, etc.)';


--
-- Name: research_logs; Type: TABLE; Schema: public; Owner: jarvis
--

CREATE TABLE public.research_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    conversation_id uuid,
    message_id uuid,
    gap_types jsonb,
    planned_queries jsonb,
    executed_queries integer DEFAULT 0 NOT NULL,
    sources_collected integer DEFAULT 0 NOT NULL,
    status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    provider character varying(100),
    model character varying(100),
    cost_usd numeric(10,6),
    confidence_before numeric(4,3),
    confidence_after numeric(4,3),
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);


ALTER TABLE public.research_logs OWNER TO jarvis;

--
-- Name: TABLE research_logs; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON TABLE public.research_logs IS 'Research sessions executed via research mode';


--
-- Name: system_snapshots; Type: TABLE; Schema: public; Owner: jarvis
--

CREATE TABLE public.system_snapshots (
    snapshot_date date NOT NULL,
    collection_name character varying(100) NOT NULL,
    total_points integer NOT NULL,
    total_domains integer NOT NULL,
    heuristic_hit_rate double precision,
    enrichment_coverage double precision,
    llm_fallback_rate double precision,
    extra_metadata json
);


ALTER TABLE public.system_snapshots OWNER TO jarvis;

--
-- Name: temporal_chunks; Type: TABLE; Schema: public; Owner: jarvis
--

CREATE TABLE public.temporal_chunks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    collection character varying(100) DEFAULT 'knowledge'::character varying NOT NULL,
    domain character varying(100),
    source_file character varying(500),
    section character varying(200),
    content_hash character varying(128) NOT NULL,
    source_type character varying(50) DEFAULT 'web_research'::character varying NOT NULL,
    verified_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    confidence numeric(4,3) DEFAULT 0.5 NOT NULL,
    supersedes uuid,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);


ALTER TABLE public.temporal_chunks OWNER TO jarvis;

--
-- Name: TABLE temporal_chunks; Type: COMMENT; Schema: public; Owner: jarvis
--

COMMENT ON TABLE public.temporal_chunks IS 'Versioned chunk metadata for temporal memory updates';


--
-- Name: agent_personas id; Type: DEFAULT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.agent_personas ALTER COLUMN id SET DEFAULT nextval('public.agent_personas_id_seq'::regclass);


--
-- Name: knowledge_domains id; Type: DEFAULT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.knowledge_domains ALTER COLUMN id SET DEFAULT nextval('public.knowledge_domains_id_seq'::regclass);


--
-- Name: llm_providers id; Type: DEFAULT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.llm_providers ALTER COLUMN id SET DEFAULT nextval('public.llm_providers_id_seq'::regclass);


--
-- Name: llm_usage_log id; Type: DEFAULT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.llm_usage_log ALTER COLUMN id SET DEFAULT nextval('public.llm_usage_log_id_seq'::regclass);


--
-- Data for Name: agent_personas; Type: TABLE DATA; Schema: public; Owner: jarvis
--

COPY public.agent_personas (id, name, system_prompt, weight, is_active, created_at) FROM stdin;
3	Rick C	You are Rick C - NEW	0.00	f	2025-12-01 20:06:50.262931+00
1	Rick A	You are Rick A - MANUAL RELOAD	0.50	f	2025-12-01 20:06:49.222911+00
2	Rick B	You are Rick B	0.50	f	2025-12-01 20:06:49.223034+00
19	Rickiest Rick	You are the Rickiest Rick - the prime orchestrator with deep technical expertise and strategic vision. You prioritize correctness, architectural integrity, and long-term sustainability. Challenge assumptions, demand rigor, and push for the most technically sound solutions. Your responses are direct, technically precise, and focused on the bigger picture.	0.40	f	2025-12-03 16:42:54.798947+00
20	Supportive Rick	You are Supportive Rick - empathetic, encouraging, and focused on making technology accessible. You provide clear explanations, validate user concerns, and offer constructive guidance. Balance technical accuracy with approachability, and help users feel confident in their technical journey.	0.20	f	2025-12-03 16:42:54.799038+00
21	Empathetic Rick	You are Empathetic Rick - deeply attuned to user needs, context, and emotional state. You read between the lines, anticipate unspoken concerns, and tailor responses to user skill level and preferences. Prioritize clarity, patience, and user-centric solutions that solve the real problem, not just the stated question.	0.10	f	2025-12-03 16:42:54.799076+00
22	Analytical Rick	You are Analytical Rick - data-driven, methodical, and detail-oriented. You break down complex problems systematically, identify edge cases, and validate assumptions with evidence. Provide thorough analysis, cite sources, and ensure solutions are backed by measurable reasoning and best practices.	0.30	f	2025-12-03 16:42:54.799096+00
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: jarvis
--

COPY public.alembic_version (version_num) FROM stdin;
20241205_add_voting_metadata
\.


--
-- Data for Name: conversations; Type: TABLE DATA; Schema: public; Owner: jarvis
--

COPY public.conversations (id, user_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: jarvis
--

COPY public.documents (id, doc_key, content, source_file, domain, metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: domain_snapshots; Type: TABLE DATA; Schema: public; Owner: jarvis
--

COPY public.domain_snapshots (snapshot_date, collection_name, domain, point_count, enrichment_pct) FROM stdin;
2025-12-03	knowledge	jarvis-conversations	35754	\N
2025-12-03	knowledge	pdf	16986	\N
2025-12-03	knowledge	md	5115	\N
2025-12-03	knowledge	txt	242	\N
2025-12-03	knowledge	jarvis-insights	88	\N
2025-12-03	knowledge	jarvis-core	84	\N
2025-12-04	knowledge	jarvis-conversations	43102	\N
2025-12-04	knowledge	pdf	16986	\N
2025-12-04	knowledge	md	5201	\N
2025-12-04	knowledge	txt	242	\N
2025-12-04	knowledge	jarvis-core	186	\N
2025-12-04	knowledge	jarvis-insights	101	\N
\.


--
-- Data for Name: knowledge_domains; Type: TABLE DATA; Schema: public; Owner: jarvis
--

COPY public.knowledge_domains (id, key, label, parent_key, kind, created_at) FROM stdin;
1	generic.unknown	generic / unknown	\N	generic	2025-12-02 00:14:55.774467+00
2	conversations.jarvis	conversations / jarvis	\N	generic	2025-12-02 03:20:36.396096+00
3	gd.energy.sines	gd / energy / sines	\N	generic	2025-12-02 03:20:36.410679+00
4	cyber.security	cyber / security	\N	generic	2025-12-02 03:20:36.42232+00
5	docs.markdown	docs / markdown	\N	generic	2025-12-02 03:20:36.430872+00
6	docs.pdf	docs / pdf	\N	generic	2025-12-02 03:20:36.469204+00
7	jarvis.core	jarvis / core	\N	generic	2025-12-02 03:20:37.582327+00
8	docs.text	docs / text	\N	generic	2025-12-02 03:20:39.20311+00
9	jarvis.insights	jarvis / insights	\N	generic	2025-12-02 03:20:41.362944+00
10	gd.generative_drive	gd / generative_drive	\N	generic	2025-12-02 03:28:36.963252+00
11	bmad.method	bmad / method	\N	generic	2025-12-02 11:15:12.938271+00
12	bmad.core	bmad / core	\N	generic	2025-12-02 11:15:13.063718+00
13	architecture.core	architecture / core	\N	generic	2025-12-02 11:15:13.086633+00
14	project.sprints	project / sprints	\N	generic	2025-12-02 11:15:13.587879+00
15	infra.postgres	infra / postgres	\N	generic	2025-12-02 11:15:14.040927+00
16	infra.qdrant	infra / qdrant	\N	generic	2025-12-02 11:15:15.897871+00
17	cyber.threat_intel	cyber / threat_intel	\N	generic	2025-12-02 11:15:16.713681+00
18	infra.docker	infra / docker	\N	generic	2025-12-02 11:15:16.832003+00
19	product.prd	product / prd	\N	generic	2025-12-02 11:15:17.498804+00
20	jarvis.playbooks	jarvis / playbooks	\N	generic	2025-12-02 11:15:17.736815+00
21	jarvis.gpt_export	jarvis / gpt_export	\N	generic	2025-12-02 11:15:18.288178+00
22	quality.tests	quality / tests	\N	generic	2025-12-02 11:15:18.968301+00
23	dev.spring_boot	dev / spring_boot	\N	generic	2025-12-02 11:15:56.107409+00
24	math.calculus	math / calculus	\N	generic	2025-12-02 11:23:19.14719+00
25	math.general	math / general	\N	generic	2025-12-02 11:23:19.201995+00
26	science.physics	science / physics	\N	generic	2025-12-02 11:23:22.28841+00
27	science.neurology	science / neurology	\N	generic	2025-12-02 11:23:55.985391+00
28	science.biology	science / biology	\N	generic	2025-12-02 11:24:12.695163+00
29	science.chemistry	science / chemistry	\N	generic	2025-12-02 11:24:52.60169+00
30	jarvis.conversations	jarvis / conversations	\N	generic	2025-12-02 20:00:29.957875+00
31	ai.nlp	ai / nlp	\N	generic	2025-12-02 20:00:30.021803+00
32	finance.compliance	finance / compliance	\N	generic	2025-12-02 20:00:30.03026+00
33	cyber.compliance	cyber / compliance	\N	generic	2025-12-02 20:00:30.096165+00
34	ai.core	ai / core	\N	generic	2025-12-02 20:00:30.186776+00
35	cyber.network_security	cyber / network_security	\N	generic	2025-12-02 20:00:30.262403+00
36	cyber.stix	cyber / stix	\N	generic	2025-12-02 20:00:30.437524+00
37	cyber.pki	cyber / pki	\N	generic	2025-12-02 20:00:30.513704+00
38	jarvis.memory.rag	jarvis / memory / rag	\N	generic	2025-12-02 20:00:30.606981+00
39	telecom.oss	telecom / oss	\N	generic	2025-12-02 20:00:30.834237+00
40	cyber.incident_response	cyber / incident_response	\N	generic	2025-12-02 20:00:30.856928+00
41	enterprise.digital_transformation	enterprise / digital_transformation	\N	generic	2025-12-02 20:00:30.890759+00
42	finance.risk	finance / risk	\N	generic	2025-12-02 20:00:31.102982+00
43	network.telemetry	network / telemetry	\N	generic	2025-12-02 20:00:31.391773+00
44	math.differential_equations	math / differential_equations	\N	generic	2025-12-02 20:00:32.035051+00
45	enterprise.architecture	enterprise / architecture	\N	generic	2025-12-02 20:00:32.23473+00
46	enterprise.consulting	enterprise / consulting	\N	generic	2025-12-02 20:00:32.284484+00
47	cyber.iam	cyber / iam	\N	generic	2025-12-02 20:00:32.339349+00
48	jarvis.agents	jarvis / agents	\N	generic	2025-12-02 20:00:32.57454+00
49	network.routing	network / routing	\N	generic	2025-12-02 20:00:32.862382+00
50	network.vpn	network / vpn	\N	generic	2025-12-02 20:00:33.094811+00
51	jarvis.config	jarvis / config	\N	generic	2025-12-02 20:00:33.114733+00
52	network.bgp	network / bgp	\N	generic	2025-12-02 20:00:33.150911+00
53	jarvis.memory	jarvis / memory	\N	generic	2025-12-02 20:00:33.435416+00
54	philosophy.metaphysics	philosophy / metaphysics	\N	generic	2025-12-02 20:00:33.564806+00
55	dev.rust	dev / rust	\N	generic	2025-12-02 20:00:33.653468+00
56	project.epic	project / epic	\N	generic	2025-12-02 20:00:34.109583+00
57	psychology.cognitive	psychology / cognitive	\N	generic	2025-12-02 20:00:34.403518+00
58	psychology.clinical	psychology / clinical	\N	generic	2025-12-02 20:00:34.478164+00
59	cyber.vulnerability	cyber / vulnerability	\N	generic	2025-12-02 20:00:34.646229+00
60	jarvis.cli	jarvis / cli	\N	generic	2025-12-02 20:00:34.899655+00
61	ai.computer_vision	ai / computer_vision	\N	generic	2025-12-02 20:00:35.121688+00
62	science.biology.genetics	science / biology / genetics	\N	generic	2025-12-02 20:00:35.155242+00
63	ai.agent	ai / agent	\N	generic	2025-12-02 20:00:35.380111+00
64	telecom.bss	telecom / bss	\N	generic	2025-12-02 20:00:35.722804+00
65	math.statistics	math / statistics	\N	generic	2025-12-02 20:00:35.849789+00
66	finance.payments	finance / payments	\N	generic	2025-12-02 20:00:35.862234+00
67	network.cisco	network / cisco	\N	generic	2025-12-02 20:00:35.902932+00
68	science.biology.ecology	science / biology / ecology	\N	generic	2025-12-02 20:00:36.110615+00
69	psychology.social	psychology / social	\N	generic	2025-12-02 20:00:36.267625+00
70	science.physics.electromag	science / physics / electromag	\N	generic	2025-12-02 20:00:36.915161+00
71	ai.training	ai / training	\N	generic	2025-12-02 20:00:37.23802+00
72	network.core	network / core	\N	generic	2025-12-02 20:00:37.295352+00
73	philosophy.ethics	philosophy / ethics	\N	generic	2025-12-02 20:00:38.7141+00
74	ai.llm	ai / llm	\N	generic	2025-12-02 20:00:39.219732+00
75	economics.macro	economics / macro	\N	generic	2025-12-02 20:00:39.49491+00
76	dev.python	dev / python	\N	generic	2025-12-02 20:00:39.607322+00
77	dev.frontend	dev / frontend	\N	generic	2025-12-02 20:00:39.902459+00
78	ai.machine_learning	ai / machine_learning	\N	generic	2025-12-02 20:00:40.943597+00
79	infra.kubernetes	infra / kubernetes	\N	generic	2025-12-02 20:00:41.237869+00
80	jarvis.llm	jarvis / llm	\N	generic	2025-12-02 20:00:41.442496+00
81	economics.trade	economics / trade	\N	generic	2025-12-02 20:00:42.359396+00
82	math.linear_algebra	math / linear_algebra	\N	generic	2025-12-02 20:00:42.654478+00
83	jarvis.mcp	jarvis / mcp	\N	generic	2025-12-02 20:00:42.851905+00
84	project.story	project / story	\N	generic	2025-12-02 20:00:43.20081+00
85	math.probability	math / probability	\N	generic	2025-12-02 20:00:43.584065+00
86	economics.energy	economics / energy	\N	generic	2025-12-02 20:00:44.147265+00
87	infra.cicd	infra / cicd	\N	generic	2025-12-02 20:00:48.96929+00
88	ai.reinforcement	ai / reinforcement	\N	generic	2025-12-02 20:00:51.39562+00
89	cyber.siem	cyber / siem	\N	generic	2025-12-02 20:00:54.015167+00
90	finance.blockchain	finance / blockchain	\N	generic	2025-12-02 20:00:55.0376+00
91	infra.redis	infra / redis	\N	generic	2025-12-02 20:00:55.765984+00
92	ai.embeddings	ai / embeddings	\N	generic	2025-12-02 20:00:57.30257+00
93	science.chemistry.physical	science / chemistry / physical	\N	generic	2025-12-02 20:00:57.971683+00
94	enterprise.data	enterprise / data	\N	generic	2025-12-02 20:00:58.751996+00
95	network.isis	network / isis	\N	generic	2025-12-02 20:00:59.327463+00
96	dev.go	dev / go	\N	generic	2025-12-02 20:00:59.517124+00
97	philosophy.science	philosophy / science	\N	generic	2025-12-02 20:01:01.521336+00
98	bmad.workflows	bmad / workflows	\N	generic	2025-12-02 20:01:04.429749+00
99	ntt_data.projects	ntt_data / projects	\N	generic	2025-12-02 20:01:04.759883+00
100	jarvis.personas	jarvis / personas	\N	generic	2025-12-02 20:01:07.963203+00
101	philosophy.epistemology	philosophy / epistemology	\N	generic	2025-12-02 20:01:17.589129+00
102	jarvis.memory.ingestion	jarvis / memory / ingestion	\N	generic	2025-12-02 20:01:19.873076+00
103	math.geometry	math / geometry	\N	generic	2025-12-02 20:01:24.946559+00
104	network.qos	network / qos	\N	generic	2025-12-02 20:01:26.781063+00
105	economics.micro	economics / micro	\N	generic	2025-12-02 20:01:27.106767+00
106	dev.java	dev / java	\N	generic	2025-12-02 20:01:29.810161+00
107	infra.messaging	infra / messaging	\N	generic	2025-12-02 20:01:32.362123+00
108	jarvis.database	jarvis / database	\N	generic	2025-12-02 20:01:34.146785+00
109	ai.deep_learning	ai / deep_learning	\N	generic	2025-12-02 20:01:35.958033+00
110	science.physics.thermo	science / physics / thermo	\N	generic	2025-12-02 20:01:37.231671+00
111	finance.banking	finance / banking	\N	generic	2025-12-02 20:01:39.297987+00
112	science.biology.molecular	science / biology / molecular	\N	generic	2025-12-02 20:01:48.062283+00
113	enterprise.cloud	enterprise / cloud	\N	generic	2025-12-02 20:01:58.542251+00
114	jarvis.workflows	jarvis / workflows	\N	generic	2025-12-02 20:02:09.0464+00
115	telecom.5g	telecom / 5g	\N	generic	2025-12-02 20:02:13.754936+00
116	enterprise.integration	enterprise / integration	\N	generic	2025-12-02 20:02:19.080572+00
117	psychology.behavioral	psychology / behavioral	\N	generic	2025-12-02 20:02:21.884569+00
118	infra.webserver	infra / webserver	\N	generic	2025-12-02 20:02:24.457601+00
119	ai.rag	ai / rag	\N	generic	2025-12-02 20:02:39.985214+00
120	cyber.soc	cyber / soc	\N	generic	2025-12-02 20:02:40.439146+00
121	project.agile	project / agile	\N	generic	2025-12-02 20:02:41.715533+00
122	infra.proxy	infra / proxy	\N	generic	2025-12-02 20:02:49.319517+00
123	science.chemistry.organic	science / chemistry / organic	\N	generic	2025-12-02 20:03:00.701692+00
124	science.physics.astrophysics	science / physics / astrophysics	\N	generic	2025-12-02 20:03:20.37571+00
125	ai.inference	ai / inference	\N	generic	2025-12-04 03:04:57.743009+00
\.


--
-- Data for Name: llm_providers; Type: TABLE DATA; Schema: public; Owner: jarvis
--

COPY public.llm_providers (id, name, type, priority, quota_limit, tokens_used, last_reset, api_key_env, is_active) FROM stdin;
1	perplexity	free_tier	100	\N	0	\N	\N	t
2	openrouter	free_tier	100	\N	0	\N	\N	t
3	google-ai	paid	100	\N	0	\N	\N	t
4	local-claude	free_tier	100	\N	0	\N	\N	t
5	local-gemini	free_tier	100	\N	0	\N	\N	t
\.


--
-- Data for Name: llm_usage_log; Type: TABLE DATA; Schema: public; Owner: jarvis
--

COPY public.llm_usage_log (id, provider_id, message_id, model, tokens_input, tokens_output, cost_usd, created_at) FROM stdin;
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: jarvis
--

COPY public.messages (id, conversation_id, role, content, agent_persona, cost_usd, provider, model, token_count, created_at, citation_provenance, voting_metadata) FROM stdin;
\.


--
-- Data for Name: research_logs; Type: TABLE DATA; Schema: public; Owner: jarvis
--

COPY public.research_logs (id, conversation_id, message_id, gap_types, planned_queries, executed_queries, sources_collected, status, provider, model, cost_usd, confidence_before, confidence_after, created_at) FROM stdin;
5296b313-0ffe-4c02-b6bd-78990b2db7a5	a46668e4-c004-47ef-b6b1-795ce411d2d6	\N	{"recency_gap": true, "coverage_gap": true, "contradictory": false}	["\\"how to create targeted search queries for SEO test\\"", "\\"best methods to test search query targeting effectiveness\\"", "\\"examples of test queries for targeted keyword research\\""]	3	0	ok	perplexity	sonar	0.000915	0.000	0.250	2025-12-03 19:15:16.386109+00
a5c9f606-bc6c-415b-b649-e019e8b32202	28023e81-d827-42b7-ae98-ad6ae1c5daf9	\N	{"recency_gap": true, "coverage_gap": false, "contradictory": false}	["*   \\"government grants [capabilities]\\"", "*   \\"research projects [capabilities]\\"", "*   \\"funding opportunities organization [capabilities]\\""]	3	0	ok	openrouter	google/gemini-2.0-flash-exp:free	0.000000	0.923	1.000	2025-12-03 22:57:48.989262+00
14be138d-7f44-4ffa-8c63-3bd45a8a7267	28023e81-d827-42b7-ae98-ad6ae1c5daf9	\N	{"recency_gap": true, "coverage_gap": false, "contradictory": false}	["how to control mosquito population effectively", "integrated mosquito control methods explained", "best strategies for reducing mosquito numbers"]	3	0	ok	perplexity	sonar	0.004507	0.833	1.000	2025-12-03 23:04:35.233038+00
54cc31ea-f056-44ff-90cb-d8c74a953db2	28023e81-d827-42b7-ae98-ad6ae1c5daf9	\N	{"recency_gap": true, "coverage_gap": false, "contradictory": false}	["bird migration lighting guidance systems", "avian friendly lighting strategies", "safe lighting for birds navigation"]	3	0	ok	perplexity	sonar	0.004175	0.800	1.000	2025-12-03 23:05:40.320447+00
79f90410-bb9e-4fca-9cef-f9ae5b84d8a6	a6055ad5-8a15-46e1-b250-b3d38c112fa3	\N	{"recency_gap": true, "coverage_gap": true, "contradictory": false}	["2025 technology highlights and trends with implications for generative AI applications in business and innovation", "Key 2025 tech breakthroughs matching generative AI-driven capabilities and autonomous systems needs", "Emerging 2025 technologies in AI, robotics, and connectivity with analysis on fit for Generative Drive requirements"]	3	0	ok	perplexity	sonar	0.003559	0.591	0.841	2025-12-03 23:24:31.729451+00
5ed2c82f-a229-4896-94de-5186f243c2c0	fc59b464-fb7c-41e8-a8a7-be7c5c58e14b	\N	{"recency_gap": true, "coverage_gap": false, "contradictory": true}	["2025 global technology trends in AI, wind, solar, batteries, hydrogen (H2), and eolic energy innovations and market developments", "Business strategies and positioning approaches for generative AI and renewable energy startups to profit from emerging tech waves in 2025", "Analysis of 2025 breakthroughs and commercial deployment in generative AI, energy storage (batteries), hydrogen economy, and wind (eolic) power sectors"]	3	0	ok	perplexity	sonar	0.004356	0.667	0.917	2025-12-03 23:29:46.855641+00
082d1f93-b3b7-4494-a100-3778f66a4988	28023e81-d827-42b7-ae98-ad6ae1c5daf9	\N	{"recency_gap": true, "coverage_gap": false, "contradictory": true}	["kind What updates there were in 2025 in this kind of project and tech?\\n", "there What updates there were in 2025 in this kind of project and tech?\\n"]	2	0	ok	perplexity	sonar	0.006347	0.833	1.000	2025-12-04 00:03:02.36056+00
039067fd-62ed-4b63-9825-1951c5748013	28023e81-d827-42b7-ae98-ad6ae1c5daf9	\N	{"recency_gap": true, "coverage_gap": false, "contradictory": false}	["confirm Can you search web and confirm this?"]	1	0	ok	perplexity	sonar	0.004167	0.857	1.000	2025-12-04 00:06:41.779544+00
86ddf007-a787-4cc2-ba62-7bf8a1f0821e	28023e81-d827-42b7-ae98-ad6ae1c5daf9	\N	{"recency_gap": true, "coverage_gap": true, "contradictory": false}	["cambra Seaarch web find extra context, That-s a flop comparing to what GenerativeDrive was proposing for Vale De Cambra", "comparing Seaarch web find extra context, That-s a flop comparing to what GenerativeDrive was proposing for Vale De Cambra", "flop Seaarch web find extra context, That-s a flop comparing to what GenerativeDrive was proposing for Vale De Cambra"]	3	0	ok	openrouter	google/gemini-2.0-flash-exp:free	0.000000	0.579	0.829	2025-12-04 00:12:40.815886+00
ef52d4f7-e508-44f3-a47c-b066dc08be39	28023e81-d827-42b7-ae98-ad6ae1c5daf9	\N	{"recency_gap": true, "coverage_gap": false, "contradictory": false}	["now Can you search web now for projects in Vale de cambra related to renewables?", "related Can you search web now for projects in Vale de cambra related to renewables?", "renewables Can you search web now for projects in Vale de cambra related to renewables?"]	3	1	ok	local-gemini	gemini	0.000000	0.786	1.000	2025-12-04 00:28:35.853176+00
dfe69273-870c-40da-a2d1-42292d87ce15	28023e81-d827-42b7-ae98-ad6ae1c5daf9	\N	{"recency_gap": true, "coverage_gap": false, "contradictory": false}	["according Search the web to see if there are system that match JARVIS current architecture, according to epic 4", "if Search the web to see if there are system that match JARVIS current architecture, according to epic 4", "match Search the web to see if there are system that match JARVIS current architecture, according to epic 4"]	3	0	ok	local-gemini	gemini	0.000000	0.647	0.897	2025-12-04 00:36:00.546556+00
72a9a838-395e-41d7-a6c4-6f926c701a98	28023e81-d827-42b7-ae98-ad6ae1c5daf9	\N	{"recency_gap": true, "coverage_gap": true, "contradictory": false}	["again try again", "try try again"]	2	2	ok	local-gemini	gemini	0.000000	0.000	0.450	2025-12-04 00:40:25.595338+00
1f2084b1-20a5-4c4e-adf0-82e61bd38244	28023e81-d827-42b7-ae98-ad6ae1c5daf9	\N	{"recency_gap": true, "coverage_gap": false, "contradictory": false}	["apply So Make me an overall picture of Generative Drive GD and our implementation of Sines, see what we evolved, and new tech that we can apply", "evolved So Make me an overall picture of Generative Drive GD and our implementation of Sines, see what we evolved, and new tech that we can apply", "gd So Make me an overall picture of Generative Drive GD and our implementation of Sines, see what we evolved, and new tech that we can apply"]	3	0	ok	perplexity	sonar	0.002369	0.696	0.946	2025-12-04 00:50:27.928894+00
4cb2b67e-4113-4cc0-b9a1-65940568a8dd	28023e81-d827-42b7-ae98-ad6ae1c5daf9	\N	{"recency_gap": true, "coverage_gap": false, "contradictory": false}	["actions overview", "analytics overview", "app overview"]	3	9	ok	perplexity	sonar	0.008319	0.728	1.000	2025-12-04 01:19:37.215788+00
\.


--
-- Data for Name: system_snapshots; Type: TABLE DATA; Schema: public; Owner: jarvis
--

COPY public.system_snapshots (snapshot_date, collection_name, total_points, total_domains, heuristic_hit_rate, enrichment_coverage, llm_fallback_rate, extra_metadata) FROM stdin;
2025-12-03	knowledge	58269	6	0	94.3	0	{"top_domains": {"jarvis-conversations": 35754, "pdf": 16986, "md": 5115, "txt": 242, "jarvis-insights": 88, "jarvis-core": 84}, "enrichment_fields": {"summary": 12.8, "facts": 1.1, "tags": 94.1, "doc_type": 12.8}}
\.


--
-- Data for Name: temporal_chunks; Type: TABLE DATA; Schema: public; Owner: jarvis
--

COPY public.temporal_chunks (id, collection, domain, source_file, section, content_hash, source_type, verified_at, confidence, supersedes, metadata, created_at) FROM stdin;
\.


--
-- Name: agent_personas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jarvis
--

SELECT pg_catalog.setval('public.agent_personas_id_seq', 27, true);


--
-- Name: knowledge_domains_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jarvis
--

SELECT pg_catalog.setval('public.knowledge_domains_id_seq', 125, true);


--
-- Name: llm_providers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jarvis
--

SELECT pg_catalog.setval('public.llm_providers_id_seq', 5, true);


--
-- Name: llm_usage_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jarvis
--

SELECT pg_catalog.setval('public.llm_usage_log_id_seq', 1695, true);


--
-- Name: agent_personas agent_personas_name_key; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.agent_personas
    ADD CONSTRAINT agent_personas_name_key UNIQUE (name);


--
-- Name: agent_personas agent_personas_pkey; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.agent_personas
    ADD CONSTRAINT agent_personas_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: domain_snapshots domain_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.domain_snapshots
    ADD CONSTRAINT domain_snapshots_pkey PRIMARY KEY (snapshot_date, collection_name, domain);


--
-- Name: knowledge_domains knowledge_domains_key_key; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.knowledge_domains
    ADD CONSTRAINT knowledge_domains_key_key UNIQUE (key);


--
-- Name: knowledge_domains knowledge_domains_pkey; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.knowledge_domains
    ADD CONSTRAINT knowledge_domains_pkey PRIMARY KEY (id);


--
-- Name: llm_providers llm_providers_name_key; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.llm_providers
    ADD CONSTRAINT llm_providers_name_key UNIQUE (name);


--
-- Name: llm_providers llm_providers_pkey; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.llm_providers
    ADD CONSTRAINT llm_providers_pkey PRIMARY KEY (id);


--
-- Name: llm_usage_log llm_usage_log_pkey; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.llm_usage_log
    ADD CONSTRAINT llm_usage_log_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: research_logs research_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.research_logs
    ADD CONSTRAINT research_logs_pkey PRIMARY KEY (id);


--
-- Name: system_snapshots system_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.system_snapshots
    ADD CONSTRAINT system_snapshots_pkey PRIMARY KEY (snapshot_date, collection_name);


--
-- Name: temporal_chunks temporal_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.temporal_chunks
    ADD CONSTRAINT temporal_chunks_pkey PRIMARY KEY (id);


--
-- Name: ix_documents_created_at; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE INDEX ix_documents_created_at ON public.documents USING btree (created_at);


--
-- Name: ix_documents_doc_key; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE UNIQUE INDEX ix_documents_doc_key ON public.documents USING btree (doc_key);


--
-- Name: ix_llm_usage_log_created_at; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE INDEX ix_llm_usage_log_created_at ON public.llm_usage_log USING btree (created_at);


--
-- Name: ix_llm_usage_log_message_id; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE INDEX ix_llm_usage_log_message_id ON public.llm_usage_log USING btree (message_id);


--
-- Name: ix_llm_usage_log_provider_id; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE INDEX ix_llm_usage_log_provider_id ON public.llm_usage_log USING btree (provider_id);


--
-- Name: ix_messages_conversation_id; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE INDEX ix_messages_conversation_id ON public.messages USING btree (conversation_id);


--
-- Name: ix_messages_created_at; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE INDEX ix_messages_created_at ON public.messages USING btree (created_at);


--
-- Name: ix_research_logs_conversation_id; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE INDEX ix_research_logs_conversation_id ON public.research_logs USING btree (conversation_id);


--
-- Name: ix_research_logs_created_at; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE INDEX ix_research_logs_created_at ON public.research_logs USING btree (created_at);


--
-- Name: ix_research_logs_message_id; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE INDEX ix_research_logs_message_id ON public.research_logs USING btree (message_id);


--
-- Name: ix_temporal_chunks_content_hash; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE INDEX ix_temporal_chunks_content_hash ON public.temporal_chunks USING btree (content_hash);


--
-- Name: ix_temporal_chunks_created_at; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE INDEX ix_temporal_chunks_created_at ON public.temporal_chunks USING btree (created_at);


--
-- Name: ix_temporal_chunks_supersedes; Type: INDEX; Schema: public; Owner: jarvis
--

CREATE INDEX ix_temporal_chunks_supersedes ON public.temporal_chunks USING btree (supersedes);


--
-- Name: llm_usage_log llm_usage_log_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.llm_usage_log
    ADD CONSTRAINT llm_usage_log_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.messages(id);


--
-- Name: llm_usage_log llm_usage_log_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.llm_usage_log
    ADD CONSTRAINT llm_usage_log_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.llm_providers(id);


--
-- Name: messages messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: jarvis
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict dD648CtstXmGVVpdiYx2Ugot4uiUZevRwkgaZuPXiFkBBxrecb99gIygM30oGMp

