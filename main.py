import csv
import os
import sqlite3
import random
import PIL.Image
from PIL import ImageTk
from tkinter import messagebox, ttk
from tkinter import *
from urllib.request import urlopen
from io import BytesIO


class MovieRecomSystem:
    def __init__(self):
        # Variables
        self.new_movies_canvas = None
        self.scrollbar = None
        self.canvas = None
        self.recommendations_text = None
        self.current_user = None

        self.first_screen = Tk()

        # Initialize SQLite database
        self.conn = sqlite3.connect("movie_database.db")
        self.cursor = self.conn.cursor()

        # Create tables if they don't exist
        self.create_tables()

        # Create 'recommended_movies' table
        self.create_recommendations_table()

        # Create a custom style for the search bar
        self.style = ttk.Style()
        self.style.configure("Search.TEntry", padding=(10, 5), relief="solid", background="white")

        # Create a Text widget for displaying recommendations with black background and gray text
        self.recommendations_text = Text(self.first_screen, wrap=WORD, width=80, height=20, bg="black", fg="gray")
        self.recommendations_text.pack(pady=20)

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        # Create the 'watched_movies' table with a foreign key reference to 'users'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watched_movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                series_title TEXT NOT NULL,
                poster_link TEXT,  -- Add the 'poster_link' column
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, series_title)
            )
        ''')

        # Commit the changes and close the connection
        self.conn.commit()

    def create_recommendations_table(self):
        # Create the 'recommended_movies' table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommended_movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                series_title TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, series_title)
            )
        ''')
        self.conn.commit()

    def main_account_screen(self):
        self.first_screen.title("Login")
        self.first_screen.geometry("1550x800+0+0")

        self.bg = ImageTk.PhotoImage(file=r"C:\Users\libia\PycharmProjects\MovieRecogSystem\Images\netflixbg.jpg")
        label_bg = Label(self.first_screen, image=self.bg)
        label_bg.place(x=0, y=0, relwidth=1, relheight=1)

        frame = Frame(self.first_screen, bg="black")
        frame.place(x=610, y=170, width=340, height=450)

        login_scr = Label(frame, text="Login Screen", font=("Comic Sans MS", 25, "bold"), fg="white",
                          bg="black")
        login_scr.place(x=70, y=80)

        # button labels
        login_btn = Button(frame, text="Login", font=("Comic Sans MS", 10, "bold"), height="2", bg="#2E8B57",
                           width="30", command=self.login)
        login_btn.place(x=50, y=180)
        register_btn = Button(frame, text="Register", height="2", bg="#E50914", width="30",
                              font=("Comic Sans MS", 10, "bold"), command=self.register)
        register_btn.place(x=50, y=250)

        self.first_screen.mainloop()

    def movies_window(self):
        self.movie_recommendations_screen = Tk()
        self.movie_recommendations_screen.title("Movie Recommendations")
        self.movie_recommendations_screen.geometry("1550x800+0+0")
        self.movie_recommendations_screen.configure(bg="black")

        # Create a frame
        self.main_frame = Frame(self.movie_recommendations_screen, bg="black")
        self.main_frame.pack(fill=BOTH, expand=1)

        # Create frames inside main_frame
        frame_height = 150  # Adjust the height as needed

        # New Movies Frame
        self.new_movies_frame = Frame(self.main_frame, bg="black", height=frame_height)
        self.new_movies_frame.pack(fill=BOTH)

        # Label for new movies
        Label(self.new_movies_frame, text="New Movies", font=("Comic Sans MS", 15),
              bg="black", fg="white").pack()

        # Create a canvas for new movies
        self.new_movies_canvas = Canvas(self.new_movies_frame, bg="black")
        self.new_movies_canvas.pack(side=TOP, fill=BOTH, expand=True)

        for movie_data in self.recent_movies:
            # Get the poster URL for each new movie
            poster_url = movie_data.get('Poster_Link', '')

            # Display the poster image for each new movie
            self.display_poster_image(self.new_movies_canvas, poster_url)

        # Create a horizontal scrollbar for the new movies canvas
        self.new_movies_scrollbar = ttk.Scrollbar(self.new_movies_frame, orient=HORIZONTAL,
                                                  command=self.new_movies_canvas.xview)
        self.new_movies_scrollbar.pack(side=BOTTOM, fill=X)

        # Configure the new movies canvas
        self.new_movies_canvas.configure(xscrollcommand=self.new_movies_scrollbar.set)
        self.new_movies_canvas.bind('<Configure>',
                                    lambda e: self.new_movies_canvas.configure(
                                        scrollregion=self.new_movies_canvas.bbox("all"),
                                        xscrollcommand=self.new_movies_scrollbar.set))

        # Watched Movies Frame
        self.watched_movies_frame = Frame(self.main_frame, bg="black", height=frame_height)
        self.watched_movies_frame.pack(fill=BOTH)

        # Create a canvas for watched movies
        self.watched_movies_canvas = Canvas(self.watched_movies_frame, bg="black")
        self.watched_movies_canvas.pack(side=TOP, fill=BOTH, expand=True)

        # Label for watched movies
        Label(self.watched_movies_canvas, text="Watched Movies", font=("Comic Sans MS", 15),
              bg="black", fg="white").pack(pady=5)

        for watched_movie_data in self.display_watched_movies():
            # Get the poster URL for each watched movie
            poster_url = watched_movie_data.get('Poster_Link', '')

            # Display the poster image for each watched movie
            self.display_poster_image(self.watched_movies_canvas, poster_url)

        # Create a horizontal scrollbar for the watched movies canvas
        self.watched_movies_scrollbar = ttk.Scrollbar(self.watched_movies_frame, orient=HORIZONTAL,
                                                      command=self.watched_movies_canvas.xview)
        self.watched_movies_scrollbar.pack(side=BOTTOM, fill=X)

        # Configure the watched movies canvas
        self.watched_movies_canvas.configure(xscrollcommand=self.watched_movies_scrollbar.set)
        self.watched_movies_canvas.bind('<Configure>',
                                        lambda e: self.watched_movies_canvas.configure(
                                            scrollregion=self.watched_movies_canvas.bbox("all")))

        # Recommended Movies Frame
        self.recommended_movies_frame = Frame(self.main_frame, bg="black", height=frame_height)
        self.recommended_movies_frame.pack(fill=BOTH)

        # Label for recommended movies
        Label(self.recommended_movies_frame, text="Recommended Movies", font=("Comic Sans MS", 15),
              bg="black", fg="white").pack(pady=20)

        Button(self.recommended_movies_frame, text="Recommendations",
               command=self.movie_recommendations_window, bg="medium spring green", width=30, height=2).pack(pady=10)

    def movie_recommendations_window(self):
        self.movie_recommendations_screen = Toplevel()
        self.movie_recommendations_screen.title("Movie Recommendations")
        self.movie_recommendations_screen.geometry("1550x800+0+0")
        self.movie_recommendations_screen.configure(bg="black")

        # Create a frame
        self.main_frame = Frame(self.movie_recommendations_screen, bg="black")
        self.main_frame.pack(fill=BOTH, expand=1)

        # Create a canvas
        self.poster_canvas = Canvas(self.main_frame, bg="black")
        self.poster_canvas.pack(side=LEFT, fill=BOTH, expand=1)

        # Create a scrollbar
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient=VERTICAL, command=self.poster_canvas.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        # Configure the canvas
        self.poster_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.poster_canvas.bind('<Configure>',
                                lambda e: self.poster_canvas.configure(scrollregion=self.poster_canvas.bbox("all")))

        # Create another frame INSIDE the Canvas
        self.second_frame = Frame(self.poster_canvas, bg="black")

        # Add the new frame to a window In the Canvas
        self.poster_canvas.create_window(self.poster_canvas.winfo_width() / 2, 0, window=self.second_frame, anchor="n")

        Label(self.second_frame, text="Movie Recommendations", font=("Comic Sans MS", 30),
              bg="black", fg="white").pack(pady=10)

        search_var = StringVar()
        self.movie_entry = ttk.Entry(self.second_frame, textvariable=search_var,
                                     font=("Comic Sans MS", 12), style="Search.TEntry", width=50)
        self.movie_entry.insert(0, "Enter a movie...")
        self.movie_entry.bind("<FocusIn>", lambda event: self.on_entry_click(event, search_var))
        self.movie_entry.bind("<FocusOut>", lambda event: self.on_focus_out(event, search_var))
        self.movie_entry.pack(pady=20)

        Button(self.second_frame, text="Get Recommendations",
               command=self.get_movie_recommendations, bg="medium spring green", width=30, height=2).pack(pady=10)

        self.movie_recommendations_screen.mainloop()

    def scroll_main_frame(self, *args):
        self.new_movies_canvas.xview(*args)  # Use xview for horizontal scrolling
        self.watched_movies_canvas.yview(*args)

    def new_movies(self):
        # Load movies data from the CSV file
        movies_data = self.load_movies_from_csv()

        # Filter movies released between 2018 and 2023
        self.recent_movies = []

        for movie in movies_data:
            released_year_str = movie.get('Released_Year', '')
            try:
                released_year = int(released_year_str)
                if 2015 <= released_year <= 2023:
                    self.recent_movies.append(movie)
            except ValueError:
                print(f"Warning: Skipping movie '{movie['Series_Title']}' due to invalid 'Released_Year' value.")

        if not self.recent_movies:
            messagebox.showinfo("No New Movies", "No movies released between 2018 and 2023 found.")
            return

        print("Debug: Displaying new movies released between 2018 and 2023:", self.recent_movies)

    def watched_movie(self):
        # Get the user's ID based on the username
        self.cursor.execute('SELECT id FROM users WHERE username = ?', (self.current_user[0],))
        user_id = self.cursor.fetchone()

        if user_id:
            # Fetch watched movies for the user from the 'watched_movies' table
            self.cursor.execute('SELECT series_title FROM watched_movies WHERE user_id = ?', (user_id[0],))
            watched_movies = self.cursor.fetchall()

            if watched_movies:
                print(f"User has watched the following movies:")
                for movie_info in watched_movies:
                    series_title = movie_info[0]
                    print(f"Series Title: {series_title}")

            else:
                # If the user doesn't have any watched movies, insert random movies
                print("User has no watched movies. Inserting random movies.")
                self.insert_random_movies(user_id[0])
        else:
            messagebox.showerror("Error", "User ID not found.")

    def display_watched_movies(self):
        watched_movies_array = []  # Create an array to store watched movies

        # Get the user's ID based on the username
        self.cursor.execute('SELECT id FROM users WHERE username = ?', (self.current_user[0],))
        user_id = self.cursor.fetchone()

        if user_id:
            # Fetch watched movies for the user from the 'watched_movies' table
            self.cursor.execute('SELECT series_title, poster_link FROM watched_movies WHERE user_id = ?', (user_id[0],))
            watched_movies = self.cursor.fetchall()

            if watched_movies:
                print(f"User has watched the following movies:")
                for movie_info in watched_movies:
                    series_title, poster_link = movie_info
                    print(f"Series Title: {series_title}")
                    watched_movies_array.append({'Series_Title': series_title, 'Poster_Link': poster_link})

            else:
                # If the user doesn't have any watched movies, insert random movies
                print("User has no watched movies. Inserting random movies.")
                self.insert_random_movies(user_id[0])
        else:
            messagebox.showerror("Error", "User ID not found.")

        print("Watched Movies Array:", watched_movies_array)

        return watched_movies_array

    def insert_random_movies(self, user_id):
        # Fetch 10 random movies with posters from the CSV file or any other source
        random_movies_with_posters = self.get_random_movies_with_posters()

        # Insert the random movies into the watched_movies table for the user
        for series_title, poster_link in random_movies_with_posters:
            # Insert both series title and poster link into the watched_movies table
            self.cursor.execute('INSERT INTO watched_movies (user_id, series_title, poster_link) VALUES (?, ?, ?)',
                                (user_id, series_title, poster_link))
            print(f"Inserted movie '{series_title}' with poster link '{poster_link}' for user ID {user_id}")

        self.conn.commit()

    def get_random_movies_with_posters(self):
        # Load movies data from the CSV file
        movies_data = self.load_movies_from_csv()

        # Shuffle the list of movies to get a random order
        random.shuffle(movies_data)

        # Select the first 10 movies (or fewer if there are fewer than 10 movies)
        random_movies = movies_data[:10]

        # Extract series titles and poster links
        series_titles_with_posters = [(movie['Series_Title'], movie['Poster_Link']) for movie in random_movies]

        print(f"Random movies with posters: {series_titles_with_posters}")
        return series_titles_with_posters

    def on_entry_click(self, event, search_var):
        if search_var.get() == "Enter a movie...":
            self.movie_entry.delete(0, END)
            self.movie_entry.config()

    def on_focus_out(self, event, search_var):
        if search_var.get() == "":
            self.movie_entry.insert(0, "Enter a movie...")
            self.movie_entry.config()

    def get_movie_recommendations(self):
        # Clear existing movie frames
        for widget in self.second_frame.winfo_children():
            if isinstance(widget, Frame):
                widget.destroy()

        user_input_movie = self.movie_entry.get()
        recommended_series_data = self.recommend_movies(user_input_movie)

        for series_data in recommended_series_data:
            # Create a Frame for each movie to hold the poster and details
            movie_frame = Frame(self.second_frame, bg="black")
            movie_frame.pack(pady=10)

            # Display movie poster and details in the same line
            self.display_poster_and_text(movie_frame, series_data)

    def recommend_movies(self, series_title):
        # Load movies data from the new CSV file
        movies_data = self.load_movies_from_csv()

        # Find details of the entered series title
        series_details = next((row for row in movies_data if row['Series_Title'] == series_title), None)

        # Get the user's ID based on the username
        self.cursor.execute('SELECT id FROM users WHERE username = ?', (self.current_user[0],))
        user_id = self.cursor.fetchone()

        recommended_series_data = []  # List to store dictionaries of recommended series

        if series_details:
            # Check if the required fields are available
            if all(key in series_details for key in ['Genre', 'Series_Title']):
                # Extract genre names
                genre_names = series_details['Genre'].split(', ')

                # Check if genre_names is not empty
                if genre_names:
                    # Find series with similar genres
                    similar_series = [row for row in movies_data if row['Series_Title'] != series_title
                                      and any(name in row['Genre'] for name in genre_names)]

                    # Count occurrences of each series across genres
                    series_occurrences = {}
                    for recommended_series in similar_series:
                        for genre in genre_names:
                            if genre in recommended_series['Genre']:
                                series_occurrences[recommended_series['Series_Title']] = series_occurrences.get(
                                    recommended_series['Series_Title'], 0) + 1

                    # Sort series based on occurrence count
                    sorted_series = sorted(series_occurrences.items(), key=lambda x: x[1], reverse=True)

                    # Display only the top 8 movies
                    top_8_series = sorted_series[:8]

                    # Print or display recommended series
                    if top_8_series:
                        print("Top 8 commonly recommended series across genres:")
                        for recommended_series, count in top_8_series:
                            # Find detailed information for the recommended series
                            series_data = next(
                                (row for row in movies_data if row['Series_Title'] == recommended_series), None)

                            if series_data:
                                recommended_series_data.append(series_data)  # Add detailed information to the list
                    else:
                        messagebox.showinfo("No recommended series found.")
                else:
                    messagebox.showinfo("No genres information available for series.")
            else:
                messagebox.showinfo("Insufficient data for series recommendations.")
        else:
            # Display messagebox when series is not found
            messagebox.showinfo("Movie Not Found", f"Series '{series_title}' not found.")

        print(recommended_series_data)

        # Save recommended movies to the database
        if user_id and recommended_series_data:
            self.save_recommendations_to_db(user_id[0], [movie['Series_Title'] for movie in recommended_series_data])

        return recommended_series_data

    def save_recommendations_to_db(self, user_id, recommended_movies):
        # Create the 'recommended_movies' table if it doesn't exist
        self.create_recommendations_table()

        # Delete existing recommendations for the user
        self.cursor.execute('DELETE FROM recommended_movies WHERE user_id = ?', (user_id,))
        self.conn.commit()

        # Insert the new recommendations into the 'recommended_movies' table
        for movie_title in recommended_movies:
            self.cursor.execute('INSERT INTO recommended_movies (user_id, series_title) VALUES (?, ?)',
                                (user_id, movie_title))
        self.conn.commit()

    def print_saved_recommendations(self):
        # Get the user's ID based on the username
        self.cursor.execute('SELECT id FROM users WHERE username = ?', (self.current_user[0],))
        user_id = self.cursor.fetchone()

        if user_id:
            # Fetch saved recommended movies from the 'recommended_movies' table
            self.cursor.execute('SELECT series_title FROM recommended_movies WHERE user_id = ?', (user_id[0],))
            recommended_movies = self.cursor.fetchall()

            if recommended_movies:
                print(f"Recommended movies for {self.current_user[0]}:")
                for movie_title in recommended_movies:
                    print(movie_title[0])
            else:
                print(f"No recommended movies found for {self.current_user[0]}.")
        else:
            print("User ID not found.")

    def load_movies_from_csv(self):
        movies_data = []
        with open(r'C:\Users\libia\PycharmProjects\MovieRecogSystem\data\IMDB_data.csv', newline='',
                  encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                movies_data.append(row)
        return movies_data

    def display_poster_image(self, canvas, poster_url):
        try:
            with urlopen(poster_url) as response:
                image_data = response.read()
                image = PIL.Image.open(BytesIO(image_data))
                image = image.resize((150, 200), PIL.Image.LANCZOS)  # Use LANCZOS resampling
                img = ImageTk.PhotoImage(image)

                # Create a Label to display the poster image with top padding
                poster_label = Label(canvas, image=img, bg="black", pady=20)
                poster_label.image = img
                poster_label.pack(side=LEFT)

        except Exception as e:
            print(f"Error loading poster image: {e}")

    def display_poster_and_text(self, movie_frame, series_data):
        title = series_data['Series_Title']
        imdb_rating = series_data.get('IMDB_Rating', 'N/A')
        overview = series_data.get('Overview', 'No overview available')
        poster_url = series_data.get('Poster_Link', '')

        # Display poster image and text in the given movie frame
        self.display_poster_image(movie_frame, poster_url)

        # Display movie details, including title, IMDb rating, and formatted overview
        details_text = f"Title: {title}\n" \
                       f"IMDb Rating: {imdb_rating}\n" \
                       f"Overview: {self.format_overview(overview)}"

        # Create a Label to display the movie details
        details_label = Label(movie_frame, text=details_text, font=("Comic Sans MS", 12), fg="white", bg="black",
                              justify=LEFT, wraplength=400)  # Adjust wraplength as needed
        details_label.pack(side=LEFT)

    def format_overview(self, overview, max_width=70):
        # Format the overview into a paragraph with a limited width
        words = overview.split()
        lines = []
        current_line = []

        for word in words:
            if len(' '.join(current_line + [word])) <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return '\n'.join(lines)

    def register(self):
        self.registering_screen = Toplevel(self.first_screen)
        self.registering_screen.title("Register")
        self.registering_screen.geometry("300x250")

        self.username = StringVar()
        self.password = StringVar()

        Label(self.registering_screen, text="Please enter the credentials below").pack()
        Label(self.registering_screen, text="").pack()

        username_lable = Label(self.registering_screen, text="Username")
        username_lable.pack()
        self.username_entry = Entry(self.registering_screen, textvariable=self.username)
        self.username_entry.pack()

        password_lable = Label(self.registering_screen, text="Password")
        password_lable.pack()
        self.password_entry = Entry(self.registering_screen, textvariable=self.password, show='*')
        self.password_entry.pack()

        Label(self.registering_screen, text="").pack()
        Button(self.registering_screen, text="Register", width=10, bg="light cyan", height=1,
               command=self.register_user).pack()

    def login(self):
        self.login_screen = Toplevel(self.first_screen)
        self.login_screen.title("Login")
        self.login_screen.geometry("300x250")

        Label(self.login_screen, text="Please enter details below to login").pack()
        Label(self.login_screen, text="").pack()

        self.username_verify = StringVar()
        self.password_verify = StringVar()

        Label(self.login_screen, text="Username").pack()
        self.username_login_entry = Entry(self.login_screen, textvariable=self.username_verify)
        self.username_login_entry.pack()

        Label(self.login_screen, text="").pack()
        Label(self.login_screen, text="Password").pack()
        self.password_login_entry = Entry(self.login_screen, textvariable=self.password_verify, show='*')
        self.password_login_entry.pack()

        Label(self.login_screen, text="").pack()
        Button(self.login_screen, text="Login", bg="medium spring green", width=10, height=1, command=self.login_verify).pack()

    def register_user(self):
        username_info = self.username.get()
        password_info = self.password.get()

        # Check if the username is already taken
        self.cursor.execute('SELECT * FROM users WHERE username = ?', (username_info,))
        existing_user = self.cursor.fetchone()

        if not username_info or not password_info:
            messagebox.showerror("Error", "Blank Entries!")
        elif existing_user:
            messagebox.showerror("Error", "Username already taken!")
        elif len(password_info) >= 9:
            messagebox.showerror("Error", "Password has to be 8 characters or less!")
        else:
            # Insert user information into the 'users' table
            self.cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username_info, password_info))
            self.conn.commit()

            self.username_entry.delete(0, END)
            self.password_entry.delete(0, END)

            messagebox.showinfo("Registration Success", "Registration Success")

    def login_verify(self):
        self.name = self.username_verify.get()
        password1 = self.password_verify.get()
        self.username_login_entry.delete(0, END)
        self.password_login_entry.delete(0, END)

        # Fetch user information from the 'users' table
        self.cursor.execute('SELECT * FROM users WHERE username = ?', (self.name,))
        user_info = self.cursor.fetchone()

        if user_info:
            if password1 == user_info[2]:  # Assuming password is stored at index 2
                # Set self.current_user with user information
                self.current_user = (user_info[1],)  # Assuming username is stored at index 1
                self.login_success()
            else:
                self.password_not_recognised()
        else:
            self.user_not_found()

    def check_credentials(self, username, password):
        list_of_files = os.listdir()
        if username in list_of_files:
            file_path = os.path.join(username)
            with open(file_path, "r") as file1:
                lines = file1.read().splitlines()
                if password == lines[1]:
                    return True
        return False

    def login_success(self):
        print("Login success method")
        self.login_success_screen = Toplevel(self.login_screen)
        self.login_success_screen.title("Success")
        self.login_success_screen.geometry("150x100")

        user_id = self.current_user[0]

        Label(self.login_success_screen, text="Successfully logged in").pack()
        Button(self.login_success_screen, text="OK", command=self.delete_login_success).pack()
        self.first_screen.destroy()
        self.new_movies()
        self.watched_movie()
        # Call this method after the user logs in
        self.print_saved_recommendations()

        self.movies_window()

    def password_not_recognised(self):
        self.password_not_recogognised_screen = Toplevel(self.login_screen)
        self.password_not_recogognised_screen.title("Success")
        self.password_not_recogognised_screen.geometry("150x100")

        Label(self.password_not_recogognised_screen, text="Invalid Password ").pack()
        Button(self.password_not_recogognised_screen, text="OK", command=self.delete_password_not_recognised).pack()

    def user_not_found(self):
        self.unknown_user_screen = Toplevel(self.login_screen)
        self.unknown_user_screen.title("Success")
        self.unknown_user_screen.geometry("150x100")

        Label(self.unknown_user_screen, text="Error, User Not Found").pack()
        Button(self.unknown_user_screen, text="OK", command=self.delete_user_not_found_screen).pack()

    def delete_login_success(self):
        self.login_success_screen.destroy()

    def delete_password_not_recognised(self):
        self.password_not_recogognised_screen.destroy()

    def delete_user_not_found_screen(self):
        self.unknown_user_screen.destroy()

    def __del__(self):
        # Close the database connection when the object is deleted
        self.conn.close()


if __name__ == "__main__":
    movie_system = MovieRecomSystem()
    movie_system.main_account_screen()
