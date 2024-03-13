from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import pandas as pd
import streamlit as st
import os
from google.cloud import storage
from io import BytesIO


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\hari5\downloads\nth-silo-410612-026a4a85986e.json"
def login():
    st.title("Login Page")

    
    credentials = {"user": "pass"}
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")

    if st.button("Login"):
        if username in credentials and credentials[username] == password:
            st.success("Login successful!")
            seem_dashboard()
        else:
            st.error("Invalid username or password")

def seem_dashboard():

    df = pd.DataFrame()
    edited_table = None
    st.title("SEMM for engineers")

    create_folder("data")
    session_state = st.session_state
    if "edited_table" not in session_state:
        session_state["edited_table"] = edited_table

    if "file_uploaded" not in session_state:
        session_state["file_uploaded"] = False

    if "df" not in session_state:
        session_state["df"] = df

    edited_df = matrix_editor_page(session_state)

    if not session_state["df"].empty:
        filename = st.text_input("Enter a filename for the saved data:")
        if st.button("Save Method Matrix"):
            if not filename:
                st.warning("Please enter a filename.")
            else:
                df = session_state["df"]
                df.to_csv(os.path.join("data/", filename + ".csv"), index=False)
                st.write(f"Saved file {filename} locally")

        if st.button("Save to Google Cloud"):
            save_to_google_cloud(session_state["df"], filename)


        session_state.selected_filename = st.selectbox("Select a file to import:", get_files_from_google_cloud())
        if st.button("Import from Google Cloud"):
            if session_state.selected_filename:
                imported_df = import_from_google_cloud(session_state)
                if imported_df is not None:
                    session_state["df"] = imported_df
                    st.write('Data imported successfully!')

def save_to_google_cloud(df, filename):

    project_id = 'nth-silo-410612'
    bucket_name = 'streamlit_semm-bucket'

    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)

    csv_data = df.to_csv(index=False)
    blob.upload_from_string(csv_data)

    st.write(f'Data saved to Google Cloud Storage: {filename}')

def import_from_google_cloud(session_state):
    project_id = 'nth-silo-410612'
    bucket_name = 'streamlit_semm-bucket'

    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)

    if session_state.selected_filename:
        blob = bucket.blob(session_state.selected_filename)
        file_content = blob.download_as_string()
        imported_df = pd.read_csv(BytesIO(file_content))

        st.write('Data import successful!')
        session_state["df"] = imported_df  
        return imported_df
    else:
        st.warning("Please select a file to import.")
        return None

def get_files_from_google_cloud():
    project_id = 'nth-silo-410612'
    bucket_name = 'streamlit_semm-bucket'

    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)

    blobs = list(bucket.list_blobs())

    return [blob.name for blob in blobs]

def matrix_editor_page(session_state):
    st.title("Matrix Editor")

    curr_dim = 0
    uploaded_file = st.file_uploader("Choose an Excel file", type='csv')
    upload = st.button("Render")
    if uploaded_file and upload and not session_state["file_uploaded"]:
        df = pd.read_csv(uploaded_file)
        session_state["df"] = df
        st.write('Data import successful!')
        session_state["file_uploaded"] = True

    new_entry = st.text_input("Enter new entry's name")
    add_entry = st.button('Add Entry')

    if "add_entry" not in session_state:
        session_state.add_entry = False
    if add_entry or session_state["edited_table"] or session_state["file_uploaded"]:
        session_state.add_entry = True
        update_curr_grid_dimension(add_entry, curr_dim, session_state)

        df = session_state["df"]

        df = create_df(add_entry, df, new_entry)

        grid_table = render_grid(df)

        update_edited_values(df, grid_table)

        edited_df = grid_table['data']
        session_state["edited_table"] = grid_table
        session_state["df"] = df
        session_state["file_uploaded"] = False

        return grid_table


def update_curr_grid_dimension(add_entry, curr_dim, session_state):
    if not session_state["edited_table"] is None:
        if add_entry:
            curr_dim += len(session_state["edited_table"]["data"]) + 1
        else:
            curr_dim += len(session_state["edited_table"]["data"])

    else:
        curr_dim += 1


def create_df(add_entry, df, new_entry):
    if df.empty:
        df = pd.DataFrame(data=[" "], columns=[new_entry] if new_entry is not None else ["col_0"])
        df["Entry"] = new_entry
        df["Method"] = ""
        df["Method-Description"] = ""
        df = df[["Entry"] + ["Method"] + ["Method-Description"] + [col for col in df.columns if col not in ["Entry", "Method", "Method-Description"]]]
    if new_entry not in df.columns and add_entry:
        df.loc[len(df)] = pd.Series([""], index=[new_entry])
        df.at[len(df) - 1, "Entry"] = new_entry
        df[new_entry] = pd.Series()
    return df



def update_edited_values(df, grid_table):
    if grid_table.selected_rows:
        row_to_update = grid_table.selected_rows[0]["_selectedRowNodeInfo"]["nodeRowIndex"]
        del grid_table.selected_rows[0]["_selectedRowNodeInfo"]
        df.iloc[row_to_update] = grid_table.selected_rows[0]

        df.columns = ["Entry", "Method", "Method-Description"] + list((df["Entry"].unique()))
        columns_to_drop = [col for col in df.columns if col not in ["Entry", "Method", "Method-Description"] + list((df["Entry"].unique()))]
        df.drop(columns=columns_to_drop, inplace=True)
        grid_table.data = df
        new_entry = None

        st.experimental_rerun()


def render_grid(df):
    gd = GridOptionsBuilder.from_dataframe(df)
    gd.configure_pagination(enabled=True)
    gd.configure_default_column(editable=True, groupable=True)
    gd.configure_selection(selection_mode="multiple")
    gridoptions = gd.build()
    gridoptions["rowDragMultiRow"] = True
    gridoptions["rowDragManaged"] = True
    gridoptions["rowDragEntireRow"] = True
    grid_table = AgGrid(
        df,
        gridOptions=gridoptions,
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        # theme="material"
    )
    return grid_table


def create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{folder_path}' created successfully.")

def main():
    page = st.sidebar.radio("Navigation", ["Login", "SEEM Dashboard"], key="main_navigation")

    if page == "Login":
        login()
    elif page == "SEEM Dashboard":
        seem_dashboard()  



if __name__ == "__main__":
    main()