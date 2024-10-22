import pandas as pd
import os

# File names
PRODUCTS_FILE = 'products.csv'
AVAILABLE_FILE = 'available.csv'
SOLD_FILE = 'sold.csv'


# Function to add products
def add_product():
    df = pd.read_csv(PRODUCTS_FILE)

    # Input product details
    print("\nTypes: type (S = Sneakers, T = T-Shirts, H = Hoodies, J = Jacket, O = Other)")
    product_type_input = input("Enter product type: ")
    print("\nTypes: type (J = Jordans, W = Women, M = Men, K = Kids, NG = No Gender)")
    gender_input = input("Enter Gender: ")
    
    brand = input("Enter brand: ")
    name = input("Enter name: ")
    color = input("Enter color: ")
    cost = float(input("Enter cost (USD): "))
    expected_price = float(input("Enter expected price (USD): "))
    trip_number = input("Enter trip number: ")
    sizes = input("Enter available sizes (comma separated): ").strip().split(",")

    # Clean sizes and count occurrences
    size_counts = {}
    for size in sizes:
        size = size.strip()  # Clean up size string
        if size in size_counts:
            size_counts[size] += 1  # Increment count if size already exists
        else:
            size_counts[size] = 1  # Initialize count for new size

    # Generate product ID in the format {Type}{Gender}01 (e.g., HW01)
    type_code = product_type_input[0].upper()  # Get the first letter of the type
    gender_code = gender_input[0].upper()  # Get the first letter of the gender
    
    # Find the next number for the ID
    existing_ids = df[df['ID'].str.startswith(f"{type_code}{gender_code}")]['ID']

    if existing_ids.empty:
        new_number = 1  # Start numbering from 1 if none exist
    else:
        existing_numbers = existing_ids.str.extract(r'(\d+)$').astype(int)
        new_number = existing_numbers.max()[0] + 1

    # Format the ID
    product_id = f"{type_code}{gender_code}{new_number:02d}"  # Generate ID like HW01

    # Use pd.concat to append the new product
    new_row_df = pd.DataFrame([{
        'ID': product_id,
        'Type': product_type_input,
        'Gender': gender_input,
        'Brand': brand,
        'Name': name,
        'Color': color,
        'Cost (USD)': cost,
        'Expected Price (USD)': expected_price,
        'Trip #': trip_number,
        'Sizes': ', '.join(size_counts.keys()),  # Store sizes as a comma-separated string
        'Count': sum(size_counts.values())  # Store total count
    }])
    
    df = pd.concat([df, new_row_df], ignore_index=True)
    df.to_csv(PRODUCTS_FILE, index=False)
    print(f"Product added with ID: {product_id}")

    # Also add to available products
    available_df = pd.DataFrame(columns=['ID', 'Type', 'Gender', 'Brand', 'Name', 'Color', 'Cost (USD)', 'Expected Price (USD)', 'Trip #', 'Sizes', 'Count'])

    for size, count in size_counts.items():
        available_product = {
            'ID': product_id,
            'Type': product_type_input,
            'Gender': gender_input,
            'Brand': brand,
            'Name': name,
            'Color': color,
            'Cost (USD)': cost,
            'Expected Price (USD)': expected_price,
            'Trip #': trip_number,
            'Sizes': size,  # Store each size in a new row
            'Count': count  # Store the count for this size
        }
        available_df = pd.concat([available_df, pd.DataFrame([available_product])], ignore_index=True)

    # Write to available.csv
    if os.path.exists(AVAILABLE_FILE):
        existing_available_df = pd.read_csv(AVAILABLE_FILE)
        available_df = pd.concat([existing_available_df, available_df], ignore_index=True)

    available_df.to_csv(AVAILABLE_FILE, index=False)

# Function to process sold items
def process_sold_item():
    available_df = pd.read_csv(AVAILABLE_FILE)  # Load available products from the available file
    sold_df = pd.read_csv(SOLD_FILE)  # Load sold items from the sold file

    product_id = input("Enter product ID sold: ")
    
    # Find the available sizes for the product ID
    available_sizes = available_df[available_df['ID'] == product_id]['Sizes'].values
    if available_sizes.size == 0:
        print("Product ID not found.")
        return
    
    # Display the available sizes
    sizes_list = available_sizes.tolist()
    print(f"Available sizes for {product_id}: [{', '.join(size.strip() for size in sizes_list)}]")

    size = input("Enter size sold: ")
    selling_date = input("Enter selling date (YYYY-MM-DD): ")
    final_price = float(input("Enter final price (USD): "))
    customer = input("Enter customer name: ")
    notes = input("Enter notes: ")

    # Check if the product ID and size are available
    sold_item = available_df[(available_df['ID'] == product_id) & (available_df['Sizes'] == size)]
    
    if sold_item.empty:
        print("Item not available in the specified size.")
        return

    # Update sold items DataFrame
    sold_entry = {
        **sold_item.iloc[0].to_dict(),
        'Selling Date': selling_date,
        'Final Price': final_price,
        'Customer': customer,
        'Notes': notes,
        'Size Sold': size  # Store the sold size
    }

    # Convert sold_entry to DataFrame and concatenate
    sold_entry_df = pd.DataFrame([sold_entry])
    sold_df = pd.concat([sold_df, sold_entry_df], ignore_index=True)
    sold_df.to_csv(SOLD_FILE, index=False)

    # Update available items: Decrease the count for the sold size
    available_df.loc[(available_df['ID'] == product_id) & (available_df['Sizes'] == size), 'Count'] -= 1  # Decrement the count by 1
    
    # Remove entries where count is zero
    available_df = available_df[available_df['Count'] > 0]

    # Save changes to available products
    available_df.to_csv(AVAILABLE_FILE, index=False)
    print("Item processed and recorded as sold.")

# Function to calculate expected profit
def calculate_expected_profit():
    df = pd.read_csv(PRODUCTS_FILE)
    
    # Ensure 'Sizes' column is treated as a string
    df['Sizes'] = df['Sizes'].astype(str)

    # Calculate the number of products based on the sizes
    df['Number_of_Products'] = df['Sizes'].apply(lambda x: len(x.split(',')))  # Count the number of sizes available
    df['Gross_Cost'] = df['Cost (USD)'] * df['Number_of_Products']  # Calculate gross cost
    df['Expected_Selling_Price'] = df['Expected Price (USD)'] * df['Number_of_Products']  # Calculate expected selling price

    # Group by Trip # and aggregate costs and expected prices
    profit_summary = df.groupby('Trip #').agg(
        Gross_Cost=('Gross_Cost', 'sum'),
        Expected_Selling_Price=('Expected_Selling_Price', 'sum'),  # Use the updated expected selling price
        Number_of_Products=('Number_of_Products', 'sum')  # Total number of products based on sizes
    ).reset_index()

    # Calculate Expected Profit
    profit_summary['Expected_Profit'] = profit_summary['Expected_Selling_Price'] - profit_summary['Gross_Cost']
    
    # Print the summary
    print(profit_summary)

# Function to calculate net profit based on sales period
def calculate_net_profit(start_date, end_date):
    sold_df = pd.read_csv(SOLD_FILE)
    sold_df['Selling Date'] = pd.to_datetime(sold_df['Selling Date'])

    filtered_sales = sold_df[(sold_df['Selling Date'] >= start_date) & (sold_df['Selling Date'] <= end_date)]
    
    total_cost = sum(filtered_sales['Cost (USD)'])
    total_revenue = sum(filtered_sales['Final Price'])
    net_profit = total_revenue - total_cost
    number_of_products = len(filtered_sales)

    print(f"Net Profit: {net_profit}, Number of Products Sold: {number_of_products}")

def generate_html(df, filename='index.html'):
    # Create a DataFrame to hold unique products and their sizes
    unique_products = {}

    for _, row in df.iterrows():
        product_id = row['ID']
        
        if product_id not in unique_products:
            unique_products[product_id] = {
                'Type': row['Type'],
                'Brand': row['Brand'],
                'Name': row['Name'],
                'Color': row['Color'],
                'Expected Price (USD)': row['Expected Price (USD)'],
                'Sizes': [row['Sizes']],  # Convert sizes
                'Image': f"images/{product_id}.png"  # Path to the image
            }
        else:
            # If the product already exists, add the sizes to the list if not already present
            if row['Sizes'] not in unique_products[product_id]['Sizes']:
                unique_products[product_id]['Sizes'].append(row['Sizes'])
    
    # Start generating the HTML
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("""<html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>fily - de USA a ARG</title>

            <!-- Favicon -->
            <link rel="icon" href="favicon.ico" type="image/x-icon">

            <!-- Google Fonts -->
            <link href="https://fonts.googleapis.com/css2?family=YourCustomFont:wght@400;700&family=Open+Sans:wght@400;700&display=swap" rel="stylesheet">
            <link href="https://fonts.googleapis.com/css2?family=IM+Fell+DW+Pica:ital@0;1&display=swap" rel="stylesheet">

            <style>
                body {
                    font-family: 'Open Sans', sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f9f9f9;
                    color: #333;
                }

                header {
                    color: black;
                    padding: 20px;
                    text-align: center;
                }

                header h1 {
                    font-family: 'IM Fell DW Pica', serif;
                    font-size: 3.5em;
                    margin: 0;
                }

                header h2 {
                    font-family: 'IM Fell DW Pica', serif;
                    font-size: 1.5em;
                    margin: 20px 0;
                }

                .social-media-icons {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 10px;
                }

                .social-media-icons img {
                    width: 30px;
                    height: auto;
                }

                .info-bar {
                    padding: 10px;
                    text-align: center;
                    margin-top: 10px;
                    font-size: 0.9em;
                    display: inline-block;
                    width: 50%;
                    border-top: 1px solid #333;
                    border-bottom: 1px solid #333;
                }

                .product-container {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-around;
                    padding: 20px;
                }

                .product {
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    margin: 20px;
                    padding: 20px;
                    width: calc(25% - 40px);
                    text-align: center;
                    transition: transform 0.2s;
                }

                .product:hover {
                    transform: scale(1.05);
                }

                .product img {
                    width: 300px;
                    height: 300px;
                    object-fit: cover; /* This ensures the image is centered and cropped if necessary */
                    object-position: center; /* Keep the center of the image in view */
                    border-bottom: 2px solid black;
                    display: block;
                    margin: 0 auto;
                }

                .product h3 {
                    font-family: 'IM Fell DW Pica', serif;
                    font-size: 1.2em;
                    margin: 15px 0;
                }

                .product p {
                    font-size: 1em;
                    margin: 5px 0;
                }

                .price {
                    font-size: 1.2em;
                    margin: 10px 0;
                    font-weight: bold;
                }

                .sizes-container {
                    display: flex;
                    justify-content: center;
                    gap: 5px;
                    margin-top: 10px;
                }

                .size {
                    padding: 5px 10px;
                    border: 1px solid black;
                    border-radius: 5px;
                    font-size: 1em;
                    background-color: white;
                    color: black;
                }

                footer {
                    background-color: #333;
                    color: white;
                    padding: 10px;
                    text-align: center;
                    position: fixed;
                    width: 100%;
                    bottom: 0;
                }

                footer a {
                    color: white;
                    font-weight: bold;
                }

                @media (max-width: 768px) {
                    .product {
                        width: calc(50% - 40px);
                    }

                    .info-bar {
                        width: 90%;
                    }

                    .product img {
                        max-width: 100%;
                    }
                }

                @media (max-width: 500px) {
                    .product {
                        width: calc(100% - 40px);
                    }

                    .info-bar {
                        width: 90%;
                    }
                }
            </style>
            <script>
                function openPopup() {
                    window.open('sizes.png', 'popup', 'width=600,height=600');
                }
            </script>
        </head>
        <body>

            <header>
                <h1>fily</h1><br>
                <div class="social-media-icons">
                    <a href="https://www.instagram.com/yourprofile">
                        <img src="instagram.png" alt="Instagram"> 
                    </a>
                    <a href="https://api.whatsapp.com/send?phone=yourphonenumber">
                        <img src="whatsapp.png" alt="WhatsApp">
                    </a>
                </div>
            </header>

            <div class="product-container">
        """)

        for product_id, details in unique_products.items():
            sizes_html = ''.join([f"<span class='size'>{size}</span>" for size in details['Sizes']])
            price_without_decimal = int(details['Expected Price (USD)'])

            f.write(f"""
                <div class="product">
                    <img src='{details['Image']}' alt='{details['Name']}'>
                    <h3>{details['Name']}</h3>
                    <p class="price">${price_without_decimal} USD</p>
                    <div class="sizes-container">
                        {sizes_html}
                    </div>
                </div>
            """)

        f.write("""
            </div>
            <footer>
                <p>Los talles de las zapatillas son de US Men.  
                    <a href="javascript:void(0)" onclick="openPopup()">Tabla de Conversiones</a>.</p>
            </footer>
        </body>
        </html>
        """)

    print(f"HTML file {filename} generated successfully.")



# Function to search available items
def search_available_items():
    df = pd.read_csv(AVAILABLE_FILE)
    search_term = input("Enter search term (leave blank for all items): ")
    filtered_df = df[df['Name'].str.contains(search_term, case=False) | (search_term == '')]

    print(filtered_df)

    # Generate HTML for search results
    html_content = "<html><body><h1>Search Results</h1><table border='1'>"
    html_content += "<tr><th>ID</th><th>Name</th><th>Available Sizes</th><th>Price</th><th>Image</th></tr>"

    for index, row in filtered_df.iterrows():
        sizes = ", ".join(row['Sizes'])
        image_path = f"{row['ID']}.png"
        html_content += f"<tr><td>{row['ID']}</td><td>{row['Name']}</td><td>{sizes}</td><td>{row['Expected Price (USD)']}</td><td><img src='{image_path}' alt='{row['Name']}' width='100'/></td></tr>"

    html_content += "</table></body></html>"

    with open('search_results.html', 'w') as f:
        f.write(html_content)

    print("Search results HTML file created.")

# Function to view sales records
def view_sales_records():
    sold_df = pd.read_csv(SOLD_FILE)
    print(sold_df)

# Function to view available products
def view_available_products():
    df = pd.read_csv(AVAILABLE_FILE)  # Load from available.csv

    # Ensure 'Sizes' column is treated as a string
    df['Sizes'] = df['Sizes'].astype(str)

    # Initialize a list to collect available products
    available_products = []

    for index, row in df.iterrows():
        size = row['Sizes']  # Use the size directly
        available_products.append({
            'ID': row['ID'],
            'Type': row['Type'],
            'Gender': row['Gender'],
            'Brand': row['Brand'],
            'Name': row['Name'],
            'Color': row['Color'],
            'Cost (USD)': row['Cost (USD)'],
            'Expected Price (USD)': row['Expected Price (USD)'],
            'Trip #': row['Trip #'],
            'Sizes': size,  # Show the available size
            'Count': row['Count']  # Show the count for this size
        })

    # Create a DataFrame from the available products
    available_df = pd.DataFrame(available_products)

    # Display the available products
    print(available_df)

    return available_df  # Return the DataFrame for further use


# Main menu function
def main_menu():
    while True:
        print("\nMenu:")
        print("1. Add Product")
        print("2. View Available Products")
        print("3. Process Sold Item")
        print("4. Calculate Expected Profit")
        print("5. Calculate Net Profit by Period")
        print("6. Create HTML Report of Available Items")
        print("7. Search Available Items")
        print("8. View Sales Records")
        print("9. Exit")

        choice = input("Choose an option: ")
        
        if choice == '1':
            add_product()
        elif choice == '2':
            available_df = view_available_products()  # Save the DataFrame for use later
        elif choice == '3':
            process_sold_item()
        elif choice == '4':
            calculate_expected_profit()
        elif choice == '5':
            start_date = input("Enter start date (YYYY-MM-DD): ")
            end_date = input("Enter end date (YYYY-MM-DD): ")
            calculate_net_profit(start_date, end_date)
        elif choice == '6':
            generate_html(available_df)  # Pass the available DataFrame to the generate_html function
        elif choice == '7':
            search_available_items()
        elif choice == '8':
            view_sales_records()
        elif choice == '9':
            break
        else:
            print("Invalid choice. Please try again.")


# Run the main menu
if __name__ == "__main__":
    # Create empty CSV files if they do not exist
    if not os.path.exists(PRODUCTS_FILE):
        pd.DataFrame(columns=['ID', 'Type', 'Gender', 'Brand', 'Name', 'Color', 'Cost (USD)', 'Expected Price (USD)', 'Trip #', 'Sizes']).to_csv(PRODUCTS_FILE, index=False)
    if not os.path.exists(AVAILABLE_FILE):
        pd.DataFrame(columns=['ID', 'Type', 'Gender', 'Brand', 'Name', 'Color', 'Cost (USD)', 'Expected Price (USD)', 'Trip #', 'Sizes', 'Count']).to_csv(AVAILABLE_FILE, index=False)
    if not os.path.exists(SOLD_FILE):
        pd.DataFrame(columns=['ID', 'Type', 'Gender', 'Brand', 'Name', 'Color', 'Cost (USD)', 'Expected Price (USD)', 'Trip #', 'Sizes', 'Selling Date', 'Final Price', 'Customer', 'Notes']).to_csv(SOLD_FILE, index=False)

    main_menu()
