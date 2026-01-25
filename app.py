import requests
import streamlit as st

# =============================
# CONFIG..
# =============================
API_BASE = "https://movie-rec-466x.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(
    page_title="🎬 Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# =============================
# SESSION STATE
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None


# =============================
# NAVIGATION
# =============================
def goto_home():
    st.session_state.view = "home"
    st.session_state.selected_tmdb_id = None
    st.rerun()

def goto_details(tmdb_id):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = tmdb_id
    st.rerun()


# =============================
# API
# =============================
@st.cache_data(ttl=30)
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
        return r.json() if r.status_code == 200 else None
    except:
        return None


# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.header("🎥 Explore Movies")
    if st.button("🏠 Home"):
        goto_home()

    st.divider()

    home_category = st.selectbox(
        "Choose Category",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"]
    )

    grid_cols = st.slider("Posters per row", 4, 8, 6)

# =============================
# HEADER
# =============================
st.title("🎬 Movie Recommendation System")
st.caption(
    "Search a movie → view details → get **TF-IDF & Genre-based recommendations**"
)
st.divider()

# =============================
# POSTER GRID
# =============================
def poster_grid(cards, cols, key_prefix):
    rows = (len(cards) + cols - 1) // cols
    idx = 0
    for _ in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards):
                break
            movie = cards[idx]
            idx += 1

            with colset[c]:
                with st.container(border=True):
                    if movie.get("poster_url"):
                        st.image(movie["poster_url"], use_column_width=True)
                    st.markdown(f"**{movie.get('title','')}**")
                    if st.button("View 🎬", key=f"{key_prefix}_{idx}"):
                        goto_details(movie["tmdb_id"])


# ==================================================
# HOME VIEW
# ==================================================
if st.session_state.view == "home":

    search = st.text_input(
        "🔍 Search Movie",
        placeholder="Type movie name like Avengers, Batman..."
    )

    # SEARCH MODE
    if search.strip():
        data = api_get("/tmdb/search", {"query": search})
        results = []

        if data and "results" in data:
            for m in data["results"][:24]:
                results.append({
                    "tmdb_id": m["id"],
                    "title": m["title"],
                    "poster_url": f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None
                })

        st.subheader("🔎 Search Results")
        poster_grid(results, grid_cols, "search")

    # HOME FEED
    else:
        st.subheader(f"🔥 {home_category.replace('_',' ').title()} Movies")
        movies = api_get("/home", {"category": home_category, "limit": 24})
        if movies:
            poster_grid(movies, grid_cols, "home")


# ==================================================
# DETAILS VIEW
# ==================================================
elif st.session_state.view == "details":

    tmdb_id = st.session_state.selected_tmdb_id
    data = api_get(f"/movie/id/{tmdb_id}")

    if not data:
        st.error("Movie details not found.")
        st.stop()

    col1, col2 = st.columns([1, 2])

    with col1:
        if data.get("poster_url"):
            st.image(data["poster_url"], use_column_width=True)

    with col2:
        st.header(data["title"])
        st.write(data.get("overview", "No overview available"))
        st.caption(f"📅 Release: {data.get('release_date','-')}")
        genres = ", ".join(g["name"] for g in data.get("genres", []))
        st.caption(f"🎭 Genres: {genres}")

    st.divider()

    # RECOMMENDATIONS
    bundle = api_get("/movie/search", {"query": data["title"]})

    if bundle:
        st.subheader("🔎 Similar Movies (TF-IDF)")
        tfidf_cards = [
            x["tmdb"] for x in bundle["tfidf_recommendations"] if x.get("tmdb")
        ]
        poster_grid(tfidf_cards, grid_cols, "tfidf")

        st.subheader("🎭 Genre Based Recommendations")
        poster_grid(bundle["genre_recommendations"], grid_cols, "genre")

    if st.button("⬅ Back to Home"):
        goto_home()
