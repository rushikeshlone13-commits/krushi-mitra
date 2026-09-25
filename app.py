import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io

# -------------------------------------------------------------
# पेज कॉन्फिगरेशन
# -------------------------------------------------------------
st.set_page_config(
    page_title="कृषी मित्र",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------------------
# Google Gemini API Key
# -------------------------------------------------------------

# -------------------------------------------------------------
# शेतकरी बॅकग्राउंड आणि आकर्षक २x४ बॉक्सेस CSS
# -------------------------------------------------------------
st.markdown("""
<style>
    /* संपूर्ण पेजला शेतात काम करणाऱ्या शेतकऱ्याचा मूळ हिरवा बॅकग्राउंड */
    .stApp {
        background: linear-gradient(rgba(240, 246, 241, 0.88), rgba(235, 245, 237, 0.92)), 
                    url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=1600&auto=format&fit=crop') no-repeat center center fixed;
        background-size: cover;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* मुख्य स्वागत पट्टी */
    .welcome-banner {
        background: linear-gradient(135deg, #1b5e20, #2e7d32);
        color: white;
        padding: 16px 20px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 22px;
        box-shadow: 0 4px 15px rgba(27, 94, 32, 0.3);
    }
    .welcome-banner h2 {
        margin: 0;
        color: #ffffff !important;
        font-size: 1.6rem;
        font-weight: 700;
    }

    /* चौकोनी पिकांचा बॉक्स */
    .crop-grid-box {
        background: #ffffff;
        border: 2.5px solid #2e7d32;
        border-radius: 16px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 16px;
        transition: transform 0.2s;
    }
    .crop-grid-box:hover {
        transform: scale(1.02);
    }

    /* वेळापत्रक माहिती बॉक्स */
    .schedule-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 16px;
        border: 2px solid #a5d6a7;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        margin-top: 15px;
        margin-bottom: 25px;
    }

    /* खालील मोठा स्कॅनर बॉक्स */
    .scanner-banner {
        background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
        border: 3px dashed #1b5e20;
        border-radius: 18px;
        padding: 20px;
        text-align: center;
        margin-top: 30px;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(46, 125, 50, 0.15);
    }
    .scanner-banner h2 {
        color: #1b5e20;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 800;
    }

    /* सर्व बटन्स */
    .stButton>button {
        background: linear-gradient(135deg, #2e7d32, #1b5e20);
        color: white;
        font-weight: 700;
        font-size: 1.05rem;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        padding: 8px 16px;
        width: 100%;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #1b5e20, #0a3d0d);
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# सेशन स्टेट (लॉगिन कायम राहण्यासाठी)
# -------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "active_crop" not in st.session_state:
    st.session_state.active_crop = None

# -------------------------------------------------------------
# ८ पिके आणि हुबेहूब फोटो लिंक्स
# -------------------------------------------------------------
CROPS = {
    "कपाशी": {
        "title": "कपाशी (Cotton)",
        "img":"https://t4.ftcdn.net/jpg/06/84/31/79/360_F_684317966_Pn9qU1DEfW5zpwoj25znJ1i0VdaOM2Px.jpg",
        "schedule": [
            ("0 ते १५ दिवस", "पेरणीनंतर बेसल डोस (DAP + पोटाश) देणे. उगवण तपासा."),
            ("३० ते ४५ दिवस", "युरियाचा पहिला हप्ता + निंबोळी अर्क फवारणी (रसशोषक किडींसाठी)."),
            ("६० ते ७५ दिवस", "पात्या आणि फुले लागताना बोरॉन + 19:19:19 खताची फवारणी."),
            ("९०+ दिवस", "बोंडे भरताना 0:0:50 खत व बोंडअळी प्रतिबंधक नियंत्रण.")
        ]
    },
    "मका": {
        "title": "मका (Maize)",
        "img": "https://t4.ftcdn.net/jpg/09/49/13/93/360_F_949139356_3ZFuYjKHBYEaQmhrmxh3S3TQsU3LNtlc.jpg",
        "schedule": [
            ("0 ते २० दिवस", "पेरणीवेळी DAP देणे. लष्करी अळीसाठी कामगंध सापळे लावा."),
            ("३० ते ४० दिवस", "युरियाचा डोस देणे व झाडांना मातीची भर लावणे."),
            ("५० ते ६५ दिवस", "कणीस लागताना 19:19:19 खताची फवारणी व योग्य पाणी देणे."),
            ("७५+ दिवस", "दाणे भरण्याच्या अवस्थेत 13:0:45 फवारणी करणे.")
        ]
    },
    "केळी": {
        "title": "केळी (Banana)",
        "img": "https://t4.ftcdn.net/jpg/02/15/33/67/360_F_215336758_TKaVsJtZHJzpJ0pIp9d2eTUV58fsbN8v.jpg",
        "schedule": [
            ("१ ते ३ महिने", "रोपांची लागवड, बेसल डोस आणि ठिबकमधून युरिया व पोटाश देणे."),
            ("४ ते ६ महिने", "बागेची स्वच्छता ठेवणे व करपा रोगावर बुरशीनाशक फवारणे."),
            ("७ ते ९ महिने", "कमळ निघताना पोटॅश आणि सूक्ष्म अन्नद्रव्ये देणे."),
            ("१०+ महिने", "घड भरण्यासाठी स्कर्टिंग बॅग वापरणे व पाणी देणे.")
        ]
    },
    "ऊस": {
        "title": "ऊस (Sugarcane)",
        "img": "https://t4.ftcdn.net/jpg/08/94/17/97/360_F_894179702_92GZbuES2xi1uRbSZnuh17jJgDe0bipV.jpg",
        "schedule": [
            ("0 ते ४५ दिवस", "लागवड, बेसल खते आणि खोडकिडीवर नियंत्रण."),
            ("६० ते ९० दिवस", "पहिली बाळभरणी आणि युरियाचा पहिला हप्ता देणे."),
            ("१२० ते १५० दिवस", "मोठी भरणी करणे आणि सूक्ष्म अन्नद्रव्ये टाकणे."),
            ("१८०+ दिवस", "पाणी नियोजन सांभाळणे व सुकलेली पाचट काढणे.")
        ]
    },
    "सोयाबीन": {
        "title": "सोयाबीन (Soybean)",
        "img": "https://media.istockphoto.com/id/1401722160/photo/sunny-plantation-with-growing-soya.jpg?s=612x612&w=0&k=20&c=r_Y3aJ-f-4Oye0qU_TBKvqGUS1BymFHdx3ryPkyyV0w=",
        "schedule": [
            ("0 ते १५ दिवस", "बीजप्रक्रिया ट्रायकोडर्माने करावी. योग्य अंतर ठेवावे."),
            ("२० ते ३० दिवस", "खोडकिडा व चक्रभुंगा नियंत्रणासाठी फवारणी."),
            ("४० ते ५० दिवस", "फुलोऱ्याच्या वेळी सूक्ष्म अन्नद्रव्ये देणे व पाणी देणे."),
            ("६० ते ७५ दिवस", "शेंगा भरताना 0:52:34 खताची फवारणी करणे.")
        ]
    },
    "तूर": {
        "title": "तूर (Pigeon Pea)",
        "img": "https://gardenerspath.com/wp-content/uploads/2022/02/How-to-Grow-Pigeon-Peas-Feature.jpg",
        "schedule": [
            ("0 ते ३० दिवस", "पेरणीवेळी DAP + सल्फर खत देणे. तणनियंत्रण करणे."),
            ("५० ते ६० दिवस", "फांद्या फुटण्यासाठी शेंडे खुडणे (Nipping)."),
            ("८० ते ९० दिवस", "फुलोऱ्याच्या अवस्थेत पाण्याचा ताण पडू न देणे."),
            ("११०+ दिवस", "शेंगा भरताना कडुनिंब अर्क किंवा कीटकनाशक फवारणी.")
        ]
    },
    "कांदा": {
        "title": "कांदा (Onion)",
        "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTjC7WnSMVhRQ79SotB0WaSgnuN7Vh_G0XfJUYACmtMsFxRR_pw_NKtDkbW&s=10",
        "schedule": [
            ("0 ते १५ दिवस", "पुनर्लागवड, हलके पाणी देणे व बेसल खतांचा वापर."),
            ("२५ ते ३५ दिवस", "थ्रिप्स नियंत्रणासाठी फिप्रोनिल किंवा निंबोळी अर्क."),
            ("४५ ते ६० दिवस", "कांदा फुगवणीसाठी 0:52:34 खत व करप्यावर फवारणी."),
            ("७०+ दिवस", "काढणीच्या १५ दिवस आधी पाणी पूर्ण बंद करणे.")
        ]
    },
    "गहू": {
        "title": "गहू (Wheat)",
        "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT84-70cVC1Af-nsb0_nXZBk9C2NTibMtyNryecQUeVeg&s=10",
        "schedule": [
            ("0 ते २१ दिवस", "पेरणीवेळी DAP देणे. २१ व्या दिवशी पहिले पाणी देणे."),
            ("४० ते ४५ दिवस", "कांडी धरताना दुसरे पाणी व युरिया देणे."),
            ("६० ते ६५ दिवस", "ओंबी बाहेर पडताना पाणी व तांब्या रोगावर लक्ष."),
            ("८० ते ८५ दिवस", "दाणे भरण्याच्या अवस्थेत पाण्याचा ताण पडू न देणे.")
        ]
    }
}

# फोटो कॉम्प्रेस फंक्शन (जलद गतीसाठी)
def optimize_image(img_file):
    image = Image.open(img_file)
    if image.mode != "RGB":
        image = image.convert("RGB")
    image.thumbnail((800, 800))
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    return buf.getvalue()

# -------------------------------------------------------------
# स्क्रीन १: शेतकरी लॉगिन
# -------------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown("""
    <div style="background:white; padding:25px; border-radius:18px; border:2px solid #2e7d32; text-align:center; box-shadow:0 6px 20px rgba(0,0,0,0.1); max-width:480px; margin:auto;">
        <h2 style="color:#1b5e20; margin-top:0;">🌾 कृषी मित्र</h2>
        <p style="color:#555;">शेतकरी मित्रांनो, पिकांचे नियोजन आणि रोग निदानासाठी आपले नाव टाका:</p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    
    col_u1, col_u2, col_u3 = st.columns([1, 2, 1])
    with col_u2:
        user_name = st.text_input("शेतकऱ्याचे नाव:", placeholder="उदा. अमोल पाटील")
        user_mob = st.text_input("मोबाईल नंबर:", placeholder="उदा. 98XXXXXXXX", max_chars=10)
        
        if st.button("प्रवेश करा ➡️"):
            if user_name.strip():
                st.session_state.logged_in = True
                st.session_state.user_name = user_name.strip()
                st.rerun()
            else:
                st.warning("कृपया तुमचे नाव टाका.")

# -------------------------------------------------------------
# स्क्रीन २: मुख्य ॲप (नकाशाप्रमाणे २x४ लेआउट आणि AI स्कॅनर)
# -------------------------------------------------------------
else:
    # १. वर फक्त हेच शीर्षक येणार
    st.markdown(f"""
    <div class="welcome-banner">
        <h2>नमस्कार {st.session_state.user_name}, कृषी मित्र वर आपले स्वागत आहे</h2>
    </div>
    """, unsafe_allow_html=True)

    # २. कागदावरील नकाशाप्रमाणे डावी आणि उजवी बाजू (४ रांगा)
    crop_pairs = [
        ("कपाशी", "मका"),
        ("केळी", "ऊस"),
        ("सोयाबीन", "तूर"),
        ("कांदा", "गहू")
    ]

    for left_crop, right_crop in crop_pairs:
        col_l, col_r = st.columns(2)
        
        # डावा डबा
        with col_l:
            st.markdown(f'<div class="crop-grid-box">', unsafe_allow_html=True)
            st.image(CROPS[left_crop]["img"], use_container_width=True)
            if st.button(f"🌾 {left_crop}", key=f"btn_{left_crop}"):
                st.session_state.active_crop = left_crop
            st.markdown('</div>', unsafe_allow_html=True)

        # उजवा डबा
        with col_r:
            st.markdown(f'<div class="crop-grid-box">', unsafe_allow_html=True)
            st.image(CROPS[right_crop]["img"], use_container_width=True)
            if st.button(f"🌾 {right_crop}", key=f"btn_{right_crop}"):
                st.session_state.active_crop = right_crop
            st.markdown('</div>', unsafe_allow_html=True)

    # ३. क्लिक केलेल्या पिकाचे वेळापत्रक (खाली स्वच्छ बॉक्समध्ये दिसेल)
    if st.session_state.active_crop:
        selected_crop_data = CROPS[st.session_state.active_crop]
        st.markdown(f"""
        <div class="schedule-card">
            <h3 style="color:#1b5e20; margin-top:0; border-bottom: 2px solid #a5d6a7; padding-bottom:8px;">
                📋 {selected_crop_data['title']} - संपूर्ण वेळापत्रक
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        for period, detail in selected_crop_data["schedule"]:
            st.markdown(f"""
            <div style="background:#f1f8e9; border-left: 5px solid #2e7d32; padding: 12px 16px; border-radius: 8px; margin-bottom: 10px;">
                <b style="color:#1b5e20;">⏱️ {period}:</b> <span style="color:#222;">{detail}</span>
            </div>
            """, unsafe_allow_html=True)

    # ४. शेवटी कागदावर असलेला मोठा "Scanner" डबा
    st.markdown("""
    <div class="scanner-banner">
        <h2>📸 Scanner (AI रोग स्कॅनर)</h2>
        <p style="color: #1b5e20; margin-top:6px; font-weight:600; font-size:1.05rem;">
            पिकावरील रोगाचे अचूक निदान करण्यासाठी झाडाचे <b>४ ते ७ फोटो</b> निवडा किंवा कॅमेऱ्याने काढा.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="schedule-card">', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "फोटो अपलोड करा (४ ते ७ फोटो निवडा):",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.write(f"निवडलेले फोटो: **{len(uploaded_files)}**")
        
        # फोटोंची ग्रिड
        p_cols = st.columns(min(len(uploaded_files), 7))
        for i, file in enumerate(uploaded_files[:7]):
            with p_cols[i]:
                st.image(file, caption=f"फोटो {i+1}", use_container_width=True)

        if st.button("⚡ रोगाचे जलद व अचूक निदान करा", type="primary"):
            if len(uploaded_files) < 2:
                st.warning("चांगल्या व अचूक निकालासाठी किमान २ ते ४ फोटो अपलोड करा.")
            else:
                prog = st.progress(20)
                status = st.empty()
                status.info("फोटो प्रक्रिया करून AI कडे पाठवत आहोत...")

                try:
                    processed_contents = []
                    for f in uploaded_files:
                        img_bytes = optimize_image(f)
                        processed_contents.append(
                            types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
                        )

                    prog.progress(55)
                    status.info("Gemini Vision AI रोगाचे विश्लेषण करत आहे...")

                    prompt = """
                    तुम्ही एक अनुभवी कृषी शास्त्रज्ञ आहात. 
                    दिलेल्या फोटोंचे बारकाईने निरीक्षण करा आणि शुद्ध मराठीत खालील मुद्द्यांनुसार थेट, स्पष्ट व अचूक उत्तर द्या:

                    १. **पिकाचे नाव आणि संभाव्य रोग/कीड:** (रोगाचे नाव ठळक लिहा)
                    २. **रोगाची मुख्य लक्षणे व कारणे:** (फोटोत काय दिसले ते सांगा)
                    ३. **शेतकऱ्याने आधी काय काळजी घ्यायला हवी होती?** (प्रतिबंधात्मक उपाय)
                    ४. **तात्काळ करावयाचे उपाय:** (रोग वाढू नये म्हणून काय करावे)
                    ५. **रासायनिक व सेंद्रिय औषधांची शिफारस:** (औषधांची नावे आणि फवारणीचे प्रमाण)

                    शेतकऱ्याला समजेल अशी सोपी आणि थेट भाषा वापरा.
                    """
                    processed_contents.append(prompt)

                    # ---------------------------------------------------------
                    # Gemini Client
                    # ---------------------------------------------------------
                    # API KEY इथे तू स्वतः टाक
                    GEMINI_API_KEY = ""

                    if not GEMINI_API_KEY or GEMINI_API_KEY == "":
                        st.error("कृपया GEMINI_API_KEY मध्ये तुमची API key टाका.")
                        st.stop()

                    client = genai.Client(api_key="")

                    # Available models - fallback क्रम
                    models_to_try = [
                        "gemini-3.5-flash-lite",
                        "gemini-3.6-flash",
                        "gemini-3.8-flash"
                    ]

                    response = None
                    last_error = None

                    for model_name in models_to_try:
                        try:
                            status.info(
                                f"Gemini {model_name} वापरून रोगाचे विश्लेषण करत आहे..."
                            )

                            response = client.models.generate_content(
                                model=model_name,
                                contents=processed_contents
                            )

                            if response and response.text:
                                break

                        except Exception as e:
                            last_error = e
                            continue

                    # सर्व models fail झाले
                    if response is None:
                        raise Exception(
                            "सध्या Gemini API कडून response मिळत नाही. "
                            "थोड्या वेळाने पुन्हा प्रयत्न करा.\n\n"
                            f"Last error: {last_error}"
                        )

                    prog.progress(100)
                    status.empty()
                    prog.empty()

                    st.success("✅ AI रोग निदान यशस्वीरित्या पूर्ण झाले!")
                    st.markdown("""
                    <div style="background: white; border-left: 6px solid #2e7d32; padding: 18px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-top:15px;">
                        <h3 style="color: #1b5e20; margin-top:0;">🌾 कृषी-AI तपासणी अहवाल:</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(response.text)

                except Exception as e:
                    prog.empty()
                    status.empty()
                    st.error(f"तांत्रिक त्रुटी आली: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
