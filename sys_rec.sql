--
-- PostgreSQL database dump
--

\restrict WphEJExB4rCUdaaypAzmRU46ehHFoy7OpDwBfvvyPYWk9Dp6FCUYtWZSBTvmaIj

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg13+1)
-- Dumped by pg_dump version 16.10 (Debian 16.10-1.pgdg13+1)

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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: competition; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.competition (
    competition_id integer NOT NULL,
    title character varying(300) NOT NULL,
    date timestamp with time zone NOT NULL,
    status character varying(3) NOT NULL,
    description character varying(4000) NOT NULL,
    date_created timestamp with time zone NOT NULL,
    date_updated timestamp with time zone NOT NULL,
    category character varying(100) NOT NULL,
    min_member integer NOT NULL,
    max_member integer NOT NULL,
    poster character varying(255),
    original_url text
);


ALTER TABLE public.competition OWNER TO postgres;

--
-- Name: competition_competition_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.competition_competition_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.competition_competition_id_seq OWNER TO postgres;

--
-- Name: competition_competition_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.competition_competition_id_seq OWNED BY public.competition.competition_id;


--
-- Name: skills; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.skills (
    skill_id integer NOT NULL,
    skill_code character varying(50) NOT NULL,
    skill_name character varying(100) NOT NULL,
    date_created timestamp with time zone NOT NULL,
    date_updated timestamp with time zone NOT NULL
);


ALTER TABLE public.skills OWNER TO postgres;

--
-- Name: skills_skill_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.skills_skill_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.skills_skill_id_seq OWNER TO postgres;

--
-- Name: skills_skill_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.skills_skill_id_seq OWNED BY public.skills.skill_id;


--
-- Name: team_invitation; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team_invitation (
    team_invitation_id integer NOT NULL,
    inviter_id integer,
    invitee_id integer,
    status character varying(30) NOT NULL,
    date_created timestamp with time zone NOT NULL,
    date_updated timestamp with time zone
);


ALTER TABLE public.team_invitation OWNER TO postgres;

--
-- Name: team_invitation_team_invitation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.team_invitation_team_invitation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.team_invitation_team_invitation_id_seq OWNER TO postgres;

--
-- Name: team_invitation_team_invitation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.team_invitation_team_invitation_id_seq OWNED BY public.team_invitation.team_invitation_id;


--
-- Name: team_join; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team_join (
    team_join_id integer NOT NULL,
    user_id integer,
    team_id integer,
    status character varying(30) NOT NULL,
    date_created timestamp with time zone NOT NULL,
    date_updated timestamp with time zone
);


ALTER TABLE public.team_join OWNER TO postgres;

--
-- Name: team_join_team_join_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.team_join_team_join_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.team_join_team_join_id_seq OWNER TO postgres;

--
-- Name: team_join_team_join_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.team_join_team_join_id_seq OWNED BY public.team_join.team_join_id;


--
-- Name: teams; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.teams (
    team_id integer NOT NULL,
    member_id character varying(200) NOT NULL,
    team_name character varying(100) NOT NULL,
    competition_id integer,
    leader_id integer,
    date_created timestamp with time zone NOT NULL,
    date_updated timestamp with time zone NOT NULL,
    is_finalized boolean NOT NULL,
    description character varying(500),
    notes character varying(500)
);


ALTER TABLE public.teams OWNER TO postgres;

--
-- Name: teams_team_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.teams_team_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.teams_team_id_seq OWNER TO postgres;

--
-- Name: teams_team_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.teams_team_id_seq OWNED BY public.teams.team_id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    username character varying(100) NOT NULL,
    password character varying(200) NOT NULL,
    email character varying(100) NOT NULL,
    fullname character varying(100) NOT NULL,
    role character varying(30),
    gender character varying(1) NOT NULL,
    semester integer NOT NULL,
    major character varying(30) NOT NULL,
    field_of_preference character varying(500) NOT NULL,
    date_created timestamp with time zone NOT NULL,
    date_updated timestamp with time zone NOT NULL,
    token character varying(255),
    token_expiration timestamp with time zone,
    is_verified boolean NOT NULL,
    profile_picture character varying(255),
    portfolio character varying(255)
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_user_id_seq OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: competition competition_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.competition ALTER COLUMN competition_id SET DEFAULT nextval('public.competition_competition_id_seq'::regclass);


--
-- Name: skills skill_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.skills ALTER COLUMN skill_id SET DEFAULT nextval('public.skills_skill_id_seq'::regclass);


--
-- Name: team_invitation team_invitation_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_invitation ALTER COLUMN team_invitation_id SET DEFAULT nextval('public.team_invitation_team_invitation_id_seq'::regclass);


--
-- Name: team_join team_join_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_join ALTER COLUMN team_join_id SET DEFAULT nextval('public.team_join_team_join_id_seq'::regclass);


--
-- Name: teams team_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teams ALTER COLUMN team_id SET DEFAULT nextval('public.teams_team_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
cf38f067d8fc
\.


--
-- Data for Name: competition; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.competition (competition_id, title, date, status, description, date_created, date_updated, category, min_member, max_member, poster, original_url) FROM stdin;
1	GKE Turns 10 Hackathon	2025-10-05 07:00:00+07	ACT	Google Kubernetes Engine (GKE) is turning 10, and we're celebrating a decade of container orchestration with a global hackathon! We're calling on you—the builders, the creators, the coders of all levels—to join the party. This is your chance to build something amazing, win awesome prizes, and have your work showcased by Google.\r\n\r\nWe're diving deep into the world of AI agents on GKE. As generative AI transforms the tech landscape, we want to see how you can leverage the power and scalability of GKE to bring intelligent, agentic capabilities to life. This is your chance to show how GKE is the ultimate platform for running cutting-edge AI workloads.	2025-08-25 07:38:12.058841+07	2025-10-04 11:00:25.684356+07	ML	2	4	d1b169e309d2410685a2235679bfdd3d_gke-hackathon.png	https://ctf.hackthebox.com/event/details/holmes-ctf-2025-2536
7	Indonesia Healthcare AI Hackathon 2025	2025-10-13 07:00:00+07	ACT	The Ministry of Health of Indonesia is proud to host the first-ever Healthcare AI Hackathon, a global call to action for bright minds to co-create solutions that will strengthen and transform Indonesia’s healthcare system.\r\n\r\nIndonesia is facing some of the most pressing health challenges of our time, tuberculosis, stroke, stunting, diabetes, and cardiovascular disease. Through the power of AI and digital innovation, we believe these challenges can be turned into opportunities for sustainable impact	2025-09-27 11:04:06.455002+07	2025-09-27 11:04:06.455006+07	ML	1	3	8e47a0c5925c4d8c9769db0d5394f6fa_1758072621835.png	\N
6	Holmes CTF 2025	2025-09-22 07:00:00+07	ACT	Welcome to HTB’s first-ever Blue CTF! This gauntlet of Sherlock-style challenges leads you through a case that has yet to be solved! \r\n\r\nJoining this event will allow you to investigate a range of scenarios: \r\n\r\n-Threat Intelligence\r\n-SOC\r\n-DFIR\r\n-Malware Reversing \r\n\r\nWith a team of 5, use your collective wit to dive into this forensic mystery and resolve an issue plaguing the city of Cogwork-1. \r\nUse your ace intellect to solve the crimes in Cogwork-1\r\n\r\nConsider this our official debrief. \r\n\r\nHolmes left some vague context (as he does) before heading out into the field. Here’s what we know: \r\n\r\nWe are getting strange readings from around the city; there were some targeted attacks on local businesses that seemed off. Who was chosen and the type of attack piqued Holmes’ interest, so he set out ahead of us. \r\n\r\nOdd though… he was muttering about something that had happened a while back, and he expressed distress about a personal AI he developed named WATSON. \r\n\r\nSee, WATSON was his collaborative ally in his attempts to curb the crime happening around the city. However, some time ago, a catastrophic false-alert event caused by WATSON triggered a year-long manhunt for a breach that never existed. We were chasing ghosts.  \r\n\r\nReputations ruined. Careers ended. The entire city was paralyzed over a phantom that was in our own backyard. The event known as NULLINC caused Holmes to shut down his creation, his friend. \r\n\r\nSo, we are just as confused about why he’d mention WATSON now, but you never can get a read on that man. \r\n\r\nHead out into the field and assist him in finding out what’s going on. We are counting on your detectives. 	2025-09-15 00:29:19.737614+07	2025-09-27 12:22:18.133026+07	SEC	3	5	9fd4db08a25d44908244ad2f9bda56ed_lol.jpg	
8	SRIFOTON 2025 COMPETITION	2025-08-17 07:00:00+07	INA	[SRIFOTON 2025 COMPETITION]\r\n\r\nHi IFMates!𑁍･｡༄.\r\n\r\n🖥 𝘽𝙤𝙤𝙩𝙞𝙣𝙜... 𝙎𝙔𝙎𝙏𝙀𝙈32𝙎𝙍𝙄𝙁𝙊𝙏𝙊𝙉𝟚𝟘𝟚𝟝.EXE\r\n📂 Status: 𝙊𝙋𝙀𝙉 𝙍𝙀𝙂𝙄𝙎𝙏𝙍𝘼𝙏𝙄𝙊𝙉 ✅\r\n\r\nThe system is online and ready to welcome the best talents! 🚀\r\nThis is your chance to be part of Sriwijaya Informatics Exhibition 2025 —\r\nwhere creativity meets technology, and the future starts now. 🪟💾\r\n\r\n⚡ Competitions available:\r\n🛡 Capture The Flag (CTF)\r\n🤖 Machine Learning (ML)\r\n⌨ Competitive Programming (CP)	2025-09-27 20:34:23.900698+07	2025-09-27 20:34:23.900703+07	ML	3	4	854766612d5c41b1b31a9d7446d97a16_deezzzz.png	https://www.instagram.com/srifoton.official/
\.


--
-- Data for Name: skills; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.skills (skill_id, skill_code, skill_name, date_created, date_updated) FROM stdin;
1	DS	Data Science	2025-09-28 11:29:49.503701+07	2025-09-28 11:29:49.503701+07
2	WD	Web Development	2025-09-28 11:29:49.503701+07	2025-09-28 11:29:49.503701+07
3	MD	Mobile Development	2025-09-28 11:29:49.503701+07	2025-09-28 11:29:49.503701+07
4	GD	Game Development	2025-09-28 11:29:49.503701+07	2025-09-28 11:29:49.503701+07
5	CS	Cyber Security	2025-09-28 11:29:49.503701+07	2025-09-28 11:29:49.503701+07
6	AI	Artificial Intelligence	2025-09-28 11:29:49.503701+07	2025-09-28 11:29:49.503701+07
7	ML	Machine Learning	2025-09-28 11:29:49.503701+07	2025-09-28 11:29:49.503701+07
8	DSN	Desain	2025-09-28 11:54:54.554219+07	2025-09-28 11:54:54.554219+07
9	JS	JavaScript	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
10	PY	Python	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
11	CSharp	C#	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
12	CPP	C++	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
13	C	C	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
14	JAVA	Java	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
15	TS	TypeScript	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
16	RB	Ruby	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
17	PHP	PHP	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
18	GO	Go	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
19	RS	Rust	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
20	KT	Kotlin	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
21	SW	Swift	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
22	SQL	SQL	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
23	R	R	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
24	DART	Dart	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
25	TF	TensorFlow	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
26	PT	PyTorch	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
27	NP	NumPy	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
28	PD	Pandas	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
29	SKL	Scikit-Learn	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
30	MAT	MATLAB	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
31	JL	Julia	2025-10-05 18:19:07.758127+07	2025-10-05 18:19:07.758127+07
\.


--
-- Data for Name: team_invitation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.team_invitation (team_invitation_id, inviter_id, invitee_id, status, date_created, date_updated) FROM stdin;
31	7	6	R	2025-09-28 11:16:31.655358+07	2025-09-28 11:17:44.849236+07
32	7	6	C	2025-09-28 11:18:08.837708+07	2025-09-28 11:18:23.47877+07
33	7	1	A	2025-10-05 18:26:34.721213+07	2025-10-05 18:28:50.316313+07
34	7	3	A	2025-10-05 20:15:27.420676+07	2025-10-05 20:15:42.799594+07
35	7	6	A	2025-10-05 20:27:51.795549+07	2025-10-05 20:28:16.830403+07
\.


--
-- Data for Name: team_join; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.team_join (team_join_id, user_id, team_id, status, date_created, date_updated) FROM stdin;
1	12	6	P	2025-10-05 14:44:22.840508+07	2025-10-05 14:44:22.840525+07
2	12	5	A	2025-10-05 14:58:35.100889+07	2025-10-05 15:35:15.442656+07
4	6	5	R	2025-10-05 20:23:29.862011+07	2025-10-05 20:24:52.41813+07
\.


--
-- Data for Name: teams; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.teams (team_id, member_id, team_name, competition_id, leader_id, date_created, date_updated, is_finalized, description, notes) FROM stdin;
6	11,2	Mantap	1	11	2025-09-27 20:10:03.533875+07	2025-09-27 20:10:03.533878+07	f	Test	\N
5	7,4,12,1,6	Joko Mulia	6	7	2025-09-27 01:25:51.496316+07	2025-10-05 20:02:24.702648+07	f	We are a cross-functional team focused on building data-driven solutions that empower smarter decision-making across the organization.\nOur team consists of product strategists, software engineers, data scientists, and UI/UX designers working collaboratively to deliver scalable tools and insights	Must be comfortable working with messy real-world data, not just clean academic datasets.\n\nStrong foundation in statistics, probability, and machine learning fundamentals (not just applying prebuilt models).\n\nHands-on experience with Python (Pandas, NumPy, Scikit-Learn / PyTorch / TensorFlow).\n\nAbility to explain complex findings in a simple and actionable way to non-technical teammates.\n\nFamiliar with MLOps / deployment workflows is a big plus (e.g. FastAPI, Docker, model monitoring).
7	13	Saba Simper	7	13	2025-10-05 20:40:08.384452+07	2025-10-05 20:40:08.384473+07	f	\N	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (user_id, username, password, email, fullname, role, gender, semester, major, field_of_preference, date_created, date_updated, token, token_expiration, is_verified, profile_picture, portfolio) FROM stdin;
13	saba	pbkdf2:sha256:1000000$WsMjprcNt2G303Hn$63a6a7283ff2f96d83cc78345e8ed2d025a89d73f3e751ee1d694188af49c5fa	saba@gmail.com	Sameko Saba	normal	P	2	Computer Science	DS,C,DART,TF	2025-10-05 20:33:40.662649+07	2025-10-05 20:43:21.560949+07	\N	\N	t	\N	\N
11	valeska	pbkdf2:sha256:1000000$pJmDdTxq5CkYlW02$9e3f48e8b7dd45b2ab05f109ff775a1a323e6836dab40cebe0ff9eacd2ca6334	valeska.ekklesia@binus.ac.id	Valeska Lim	normal	L	7	Computer Science	WD,DS,MD	2025-09-27 20:03:39.987881+07	2025-09-27 20:07:47.932568+07	\N	\N	t	\N	\N
2	Joko	joko	valeskalim77@gmail.com	Joko Papat	normal	P	5	Computer Science	WD,GD	2025-08-25 07:37:29.777365+07	2025-08-25 07:37:29.777365+07	\N	\N	t	\N	\N
12	johan	pbkdf2:sha256:1000000$jmsI9P6UTgJiQQG0$3b34982c7ab3407de200c640e29f005584a532556404838c2779b8c467b10b2e	valeskavalentinekklesia@gmail.com	Johan	normal	L	2	Computer Science	DS,WD,MD	2025-09-28 11:43:14.063055+07	2025-09-28 11:44:56.976897+07	\N	\N	t	\N	https://github.com/reynaldomarchell
4	William	william	william@gmail.com	William	normal	L	3	Computer Science	WD,DS	2025-08-25 07:37:29.777365+07	2025-08-25 07:37:29.777365+07	\N	\N	t	\N	\N
5	Handoko	handoko	handoko@gmail.com	Handoko Handoko	normal	L	1	Computer Science	WD,AI	2025-08-25 07:37:29.777365+07	2025-08-25 07:37:29.777365+07	\N	\N	t	\N	\N
6	Yunus	yunus	yunus@gmail.com	Yunus Kepler	normal	L	6	Computer Science	AI,ML,GD	2025-08-25 07:37:29.777365+07	2025-08-25 07:37:29.777365+07	\N	\N	t	\N	\N
3	Stanley	stanley	noersalimstanley@gmail.com	Stanley Noer	normal	L	7	Computer Science	CS,AI,ML	2025-08-25 07:37:29.777365+07	2025-08-25 07:37:29.777365+07	\N	\N	t	\N	\N
7	Admin	pbkdf2:sha256:1000000$GiyrXp8E5LQAmvK7$9e82e228855626982ab526da66b949a400702d6dd3960ade7a0be007022eb974	contactbobomad@gmail.com	Admin Admin	admin	L	1	Computer Science	WD,CSharp,TS	2025-08-25 07:37:29.777365+07	2025-10-05 18:25:26.257637+07	\N	\N	t	\N	https://github.com/ValeskaLim
1	Alibaba	alibaba	alibaba@gmail.com	Alibaba Alibaba	normal	L	4	Computer Science	DS,PY,MAT,TF	2025-08-25 07:37:29.777365+07	2025-10-05 18:28:17.314405+07	\N	\N	t	\N	\N
\.


--
-- Name: competition_competition_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.competition_competition_id_seq', 8, true);


--
-- Name: skills_skill_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.skills_skill_id_seq', 31, true);


--
-- Name: team_invitation_team_invitation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.team_invitation_team_invitation_id_seq', 35, true);


--
-- Name: team_join_team_join_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.team_join_team_join_id_seq', 4, true);


--
-- Name: teams_team_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.teams_team_id_seq', 7, true);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_user_id_seq', 13, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: competition competition_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.competition
    ADD CONSTRAINT competition_pkey PRIMARY KEY (competition_id);


--
-- Name: competition competition_title_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.competition
    ADD CONSTRAINT competition_title_key UNIQUE (title);


--
-- Name: skills skills_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_pkey PRIMARY KEY (skill_id);


--
-- Name: team_invitation team_invitation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_invitation
    ADD CONSTRAINT team_invitation_pkey PRIMARY KEY (team_invitation_id);


--
-- Name: team_join team_join_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_join
    ADD CONSTRAINT team_join_pkey PRIMARY KEY (team_join_id);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (team_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: team_invitation team_invitation_invitee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_invitation
    ADD CONSTRAINT team_invitation_invitee_id_fkey FOREIGN KEY (invitee_id) REFERENCES public.users(user_id);


--
-- Name: team_invitation team_invitation_inviter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_invitation
    ADD CONSTRAINT team_invitation_inviter_id_fkey FOREIGN KEY (inviter_id) REFERENCES public.users(user_id);


--
-- Name: team_join team_join_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_join
    ADD CONSTRAINT team_join_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(team_id);


--
-- Name: team_join team_join_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_join
    ADD CONSTRAINT team_join_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: teams teams_competition_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_competition_id_fkey FOREIGN KEY (competition_id) REFERENCES public.competition(competition_id);


--
-- PostgreSQL database dump complete
--

\unrestrict WphEJExB4rCUdaaypAzmRU46ehHFoy7OpDwBfvvyPYWk9Dp6FCUYtWZSBTvmaIj

