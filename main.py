
import streamlit as st
from processing import preprocess
from processing.display import Main
import pandas as pd
import requests

# Page configuration
st.set_page_config(
    page_title="Movie recommender",
    layout="centered",  # Adjust layout to 'centered' for a cleaner look
    page_icon="🎥",
)

# Custom CSS for styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
        background-color: #1a1a2e;
        color: #ffffff;
    }
    .main-container {
        padding: 2rem;
        border-radius: 8px;
        background-color: #282c34;
    }
    .title {
        text-align: center;
        font-weight: 600;
        color: #ff9f43;
    }
    .recommend-section, .details-section {
        margin-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state variables
if "selected_movie_name" not in st.session_state:
    st.session_state["selected_movie_name"] = None

if "show_recommendations" not in st.session_state:
    st.session_state["show_recommendations"] = False

# TMDB API key (Replace with your actual key)
TMDB_API_KEY = "d543024474e640f3980a08dfd2750403"

def fetch_movie_details(movie_name):
    """
    Fetch movie details using TMDB API for a given movie name.
    """
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    response = requests.get(search_url)
    data = response.json()

    try:
        movie_id = data['results'][0]['id']
        movie_details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
        movie_details_response = requests.get(movie_details_url)
        movie_details = movie_details_response.json()

        title = movie_details['title']
        rating = movie_details.get('vote_average', 'N/A')
        runtime = movie_details.get('runtime', 'N/A')
        overview = movie_details.get('overview', 'Overview not available.')
        poster_url = f"https://image.tmdb.org/t/p/w780/{movie_details['poster_path']}" if 'poster_path' in movie_details else "https://via.placeholder.com/150"

        return title, rating, runtime, overview, poster_url
    except (IndexError, KeyError):
        return None, None, None, None, None

def recommend_display(new_df):
    """
    Display movie recommendations and handle movie selection with a predictive search bar.
    """
    st.markdown("<h1 class='title'>🎥 Movie Recommender</h1>", unsafe_allow_html=True)
    st.markdown("<div class='recommend-section'>", unsafe_allow_html=True)

    # Get unique movie titles for the search bar
    movie_titles = new_df["title"].dropna().unique().tolist()

    # Predictive search bar for movie search
    search_query = st.text_input(
        "Search for a Movie:",
        value="",
        placeholder="Type the movie name...",
    )

    recommend_button = st.button("Get Movie Details")

    if recommend_button:
        if search_query:
            movie_found = new_df[new_df["title"].str.contains(search_query, case=False, na=False)]
            if not movie_found.empty:
                st.session_state["selected_movie_name"] = movie_found["title"].iloc[0]
                st.session_state["show_recommendations"] = False
                st.experimental_rerun()
            else:
                st.error("Movie not found. Please try another name.")
        else:
            st.warning("Please enter a movie name before clicking 'Get Movie Details'.")

    if st.session_state["selected_movie_name"]:
        # Display selected movie details first
        selected_movie_name = st.session_state["selected_movie_name"]
        title, rating, runtime, overview, poster_url = fetch_movie_details(selected_movie_name)

        if title:
            st.markdown("### Movie Details")
            # Create two columns: one for the poster, one for the details
            col1, col2 = st.columns([1, 2])  # 1 for the poster, 2 for the details

            with col1:
                st.image(poster_url, width=200)

            with col2:
                st.subheader(f"{title}")
                st.text(f"Rating: {rating}")
                st.text(f"Runtime: {runtime} minutes")
                st.write("Overview:")
                st.write(overview)

        else:
            st.warning("Movie details not available.")
        
        # Now show movie recommendations
        st.subheader(f"Recommended Movies for '{selected_movie_name}'")
        st.write("---")
        try:
            movies, posters = preprocess.recommend(new_df, selected_movie_name, r"Files/similarity_tags_tags.pkl")
            for i in range(0, len(movies), 4):
                cols = st.columns(4)
                for j, col in enumerate(cols):
                    if i + j < len(movies):
                        with col:
                            st.image(posters[i + j], width=140)
                            st.subheader(movies[i + j])
                            if st.button(f"See {movies[i + j]}", key=f"movie_{movies[i + j]}_{i + j}"):
                                st.session_state["selected_movie_name"] = movies[i + j]
                                st.session_state["show_recommendations"] = False
                                st.experimental_rerun()
        except Exception as e:
            st.error(f"Error fetching recommendations: {e}")
        
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    """
    Main function to run the app.
    """
    with Main() as bot:
        bot.main_()
        new_df, movies, _ = bot.getter()

        if st.session_state["show_recommendations"]:
            recommend_display(new_df)
        else:
            recommend_display(new_df)  # Keeps the logic running for recommendations after movie details

if __name__ == "__main__":
    main()


