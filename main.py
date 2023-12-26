import streamlit as st
import pandas as pd

# Define the SessionState class
class SessionState:
    def _init_(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

# Function to add a row and a column to the DataFrame
@st.cache(allow_output_mutation=True)
def add_row_and_column(df):
    # Add a new row and column to the DataFrame
    new_col_name = f"New Column {df.shape[1] + 1}"
    df.loc[df.shape[0] + 1] = ""
    df[new_col_name] = ""
    return df

def main():
    st.title("SEEM for engineers")

    # Use st.session_state to store and retrieve session variables
    session_state = st.session_state

    # Sidebar navigation
    page = st.sidebar.radio("Select a page", ["Login", "Matrix Editor"])

    if page == "Login":
        login_page(session_state)
    elif page == "Matrix Editor":
        matrix_editor_page(session_state)

def login_page(session_state):
    # Login
    session_state.email = st.text_input("Email:")
    session_state.password = st.text_input("Password:", type="password")
    login_button = st.button("Login")

    if login_button:
        # Add authentication logic here (for simplicity, we'll just display a message)
        st.success(f"Logged in as {session_state.email}")

        # Change the page
        session_state.page = "Matrix Editor"

        # Redirect to the matrix editor page using JavaScript
        redirect_js = """
        <script>
            window.location.href = "/?page=Matrix%20Editor";
        </script>
        """
        st.components.v1.html(redirect_js)

def matrix_editor_page(session_state):
    st.title("Matrix Editor")

    # Load the existing DataFrame or create a new one
    df = load_or_create_matrix(session_state)

    # Display the existing DataFrame
    edited_table = st.data_editor(df)
    value = edited_table["Column1"].iloc[0]
    st.markdown(f"Your favorite command is **{value}** 🎈")

    # Display text area for manual editing


def load_or_create_matrix(session_state):
    # Load the existing DataFrame or create a new one
    if hasattr(session_state, "matrix_df"):
        return session_state.matrix_df
    else:
        return create_matrix()

def create_matrix():
    # Create a DataFrame with 15 rows and 15 columns
    data = {f"Column{i}": [""] * 15 for i in range(1, 16)}
    df = pd.DataFrame(data)
    return df

def parse_edited_text(text):
    # Parse the edited text and convert it to a DataFrame
    lines = text.split('\n')
    parsed_data = [line.split() for line in lines]
    updated_df = pd.DataFrame(parsed_data, columns=[f"Column{i}" for i in range(1, 16)])
    return updated_df

def save_matrix(session_state, df):
    # Save the updated DataFrame to session_state
    session_state.matrix_df = df

# Run the Streamlit app
if __name__ == "__main__":
    main()

