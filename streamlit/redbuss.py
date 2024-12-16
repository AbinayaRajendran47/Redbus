import streamlit as st
import pymysql
import pandas as pd

# Connect to MySQL database
def get_connection():
    return pymysql.connect(host='localhost', user='root', passwd='Password@123', port=3307, database='redbus')

# Function to fetch route names starting with a specific letter, arranged alphabetically
def fetch_route_names(connection, starting_letter):
    query = f"SELECT DISTINCT Route_Name FROM bus_routes WHERE Route_Name LIKE '{starting_letter}%' ORDER BY Route_Name"
    route_names = pd.read_sql(query, connection)['Route_Name'].tolist()
    return route_names

# Function to fetch data from MySQL based on selected Route_Name, price range, price sort order, and duration
def fetch_data(connection, route_name, price_range, price_sort_order, duration_range):
    # Define price range conditions
    if price_range == '0-500':
        price_condition = "Price BETWEEN 0 AND 500"
    elif price_range == '500-1000':
        price_condition = "Price BETWEEN 500 AND 1000"
    elif price_range == '1000-2000':
        price_condition = "Price BETWEEN 1000 AND 2000"
    elif price_range == '2000 and above':
        price_condition = "Price > 2000"
    else:
        price_condition = "1=1"  # Default to no filtering if no range is selected

    # Convert the price_sort_order to valid SQL order
    if price_sort_order == 'Low to High':
        sort_order = 'ASC'
    elif price_sort_order == 'High to Low':
        sort_order = 'DESC'
    else:
        sort_order = 'ASC'  # Default to ASC if the input is invalid

    # Define duration condition
    if duration_range:
        duration_condition = f"Duration BETWEEN {duration_range[0]} AND {duration_range[1]}"
    else:
        duration_condition = "1=1"  # No filtering if no range is selected

    # Construct SQL query with price range, duration filter, and sorting order
    query = f"""
        SELECT * 
        FROM bus_routes 
        WHERE Route_Name = %s AND {price_condition} AND {duration_condition} 
        ORDER BY Star_Rating DESC, Price {sort_order}
    """

    # Execute the query and return the dataframe
    df = pd.read_sql(query, connection, params=(route_name,))
    
    # Transform the Bus_Type column to group it into categories
    df['Bus_Type'] = df['Bus_Type'].apply(
        lambda x: 'AC' if 'AC' in x.upper() else 
                  ('Non-AC' if 'NON A/C' in x.upper() else 
                   ('Sleeper' if 'SLEEPER' in x.upper() else 'Seater'))
    )
    
    return df

# Function to filter data based on Star_Rating and Bus_Type
def filter_data(df, star_rating_range, bus_types):
    # Filter data by Star_Rating range
    filtered_df = df[(df['Star_Rating'] >= star_rating_range[0]) & (df['Star_Rating'] <= star_rating_range[1])]
    # Filter by Bus_Type
    filtered_df = filtered_df[filtered_df['Bus_Type'].isin(bus_types)]
    return filtered_df

# Main Streamlit app
def main():
    st.image(r"C:\Users\abina\Downloads\220px-Redbus_logo.jpg", width=200)
    st.header('Redbus Data Scraping with Selenium & Dynamic Filtering using Streamlit')

    connection = get_connection()

    try:
        # Sidebar - Input for starting letter
        starting_letter = st.sidebar.text_input('Enter starting letter of Route Name', 'A')

        # Fetch route names starting with the specified letter
        if starting_letter:
            route_names = fetch_route_names(connection, starting_letter.upper())

            if route_names:
                # Sidebar - Selectbox for Route_Name
                selected_route = st.sidebar.radio('Select Route Name', route_names)

                if selected_route:
                    # Sidebar - Selectbox for sorting preference
                    price_sort_order = st.sidebar.selectbox('Sort by Price', ['Low to High', 'High to Low'])

                    # Sidebar - Select Price Range filter
                    price_range = st.sidebar.selectbox("Choose Bus Fare Range", ['0-500', '500-1000', '1000-2000', '2000 and above'])

                    # Sidebar - Duration filter (in hours or minutes, e.g., 0 to 10 hours)
                    min_duration = st.sidebar.number_input('Minimum Duration (in hours)', min_value=0, value=0)
                    max_duration = st.sidebar.number_input('Maximum Duration (in hours)', min_value=0, value=10)
                    duration_range = (min_duration, max_duration)

                    # Fetch data based on selected Route_Name, price range, price sort order, and duration range
                    data = fetch_data(connection, selected_route, price_range, price_sort_order, duration_range)

                    if not data.empty:
                        # Display data table with a subheader
                        st.write(f"### Data for Route: {selected_route}")
                        st.write(data)

                        # Star Rating filter - Slider to select Star Rating range
                        star_rating_range = st.slider(
                            'Select Star Rating Range:',
                            min_value=float(data['Star_Rating'].min()), 
                            max_value=float(data['Star_Rating'].max()), 
                            value=(float(data['Star_Rating'].min()), float(data['Star_Rating'].max()))
                        )

                        # Bus Type filter
                        bus_types = data['Bus_Type'].unique().tolist()
                        selected_bus_types = st.multiselect('Filter by Bus Type', bus_types)

                        # Filter by Star Rating and Bus Type
                        if selected_bus_types:
                            filtered_data = filter_data(data, star_rating_range, selected_bus_types)
                            # Display filtered data table with a subheader
                            st.write(f"### Filtered Data for Star Rating Range: {star_rating_range} and Bus Type(s): {selected_bus_types}")
                            st.write(filtered_data)
                    else:
                        st.write(f"No data found for Route: {selected_route} with the specified filters.")
            else:
                st.write("No routes found starting with the specified letter.")
    finally:
        connection.close()
    
    st.subheader(":blue[Developed-by:]  Abinaya Rajendran")

if __name__ == '__main__':
    main()
