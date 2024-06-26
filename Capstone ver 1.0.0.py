import cv2
import pytesseract
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
from PIL import Image, ImageTk
import re
import os
from datetime import datetime
from googletrans import Translator

# Set the path to the Tesseract executable (replace this with your actual path)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Set up a set to keep track of processed gluten-containing ingredients
processed_gluten_ingredients = set()

# Folder to store the recipes persistently
recipe_folder_path = 'Saved_Recipes'

# Create the translator object
translator = Translator()

def create_recipe_folder():
    # Create the recipe folder if it doesn't exist
    if not os.path.exists(recipe_folder_path):
        os.makedirs(recipe_folder_path)

def load_saved_recipes():
    global last_five_recipes
    try:
        with open(recipe_folder_path + '/Last_Five_Recipes.txt', 'r') as file:
            last_five_recipes = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        pass  # File doesn't exist yet

def save_last_five_recipes():
    # Save the last five recipes to a file
    with open(recipe_folder_path + '/Last_Five_Recipes.txt', 'w') as file:
        for idx, recipe in enumerate(last_five_recipes, start=1):
            file.write(f"Recipe {idx}:\n{recipe}\n\n")
    print(f"Last five recipes saved to {recipe_folder_path}/Last_Five_Recipes.txt")

def set_background(root, image_path):
    try:
        # Open the image using Pillow
        image = Image.open(image_path)

        # Convert the image to the PhotoImage format
        background_image = ImageTk.PhotoImage(image)

        # Get the image dimensions
        image_width = background_image.width()
        image_height = background_image.height()

        # Create a Canvas widget to place the background image
        canvas = tk.Canvas(root, width=image_width, height=image_height, highlightthickness=0)  # Set highlightthickness to 0 to make the Canvas transparent
        canvas.pack()

        # Place the background image on the Canvas
        canvas.create_image(0, 0, anchor=tk.NW, image=background_image)

        # This line will keep a reference to the image, preventing it from being garbage collected
        canvas.image = background_image

        # Return the canvas to add widgets on top of it
        return canvas
    except Exception as e:
        print(f"Error setting background image: {e}")
        return None

def scale_numbers(text, scale_factor):
    # Split the text into lines
    lines = text.split('\n')
    scaled_lines = []

    for line in lines:
        scaled_line = ""
        words = line.split()
        for word in words:
            try:
                number = float(word)
                scaled_number = number * scale_factor
                scaled_line += f"{scaled_number} "
            except ValueError:
                scaled_line += f"{word} "

        scaled_lines.append(scaled_line.strip())

    # Join the lines back into a single string
    scaled_text = '\n'.join(scaled_lines)
    return scaled_text

def start_processing(original_text, image, scale_factor, window_to_destroy):
    if window_to_destroy:
        window_to_destroy.destroy()

    # Update the Text widgets to display the extracted and scaled text side by side
    text_display_original.delete(1.0, tk.END)  # Clear existing text
    text_display_original.insert(tk.END, f"Original Text:\n{original_text}\n\n")

    scaled_text = scale_numbers(original_text, scale_factor)

    text_display_scaled.delete(1.0, tk.END)  # Clear existing text
    text_display_scaled.insert(tk.END, f"Scaled Text (Factor {scale_factor}):\n{scaled_text}\n\n")

    # Save the scaled text to a .txt file
    output_file_path = f'{recipe_folder_path}/Scaled_Recipe_{datetime.now().strftime("%Y%m%d%H%M%S")}.txt'
    with open(output_file_path, 'w') as file:
        file.write(scaled_text)

    # Save the scaled text to the last_five_recipes list
    if len(last_five_recipes) == 5:
        last_five_recipes.pop(0)
    last_five_recipes.append(scaled_text)

    # Resize the image to a smaller size for display (optional)
    if image:
        resized_image = cv2.resize(image, (800, 600))

        # Display the original image
        cv2.imshow('Original Image', resized_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    print(f"Scaled text saved to {output_file_path}")

    # Show a message indicating image processing is done
    messagebox.showinfo("Image Processing Complete", "Image processing is complete. Check the output.")

def select_recipe_image():
    file_path = filedialog.askopenfilename(title="Select a Recipe Image", filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])

    if file_path:
        # Read the selected image
        image = cv2.imread(file_path)

        # Use Tesseract to extract text
        text = pytesseract.image_to_string(image)

        # Replace "Ye" with "1/2" in the extracted text
        text = text.replace("Ye", "1/2")
        text = text.replace("Teel6ffel","Teeléffel")
        # Ask if the user wants to apply a scale
        apply_scale = messagebox.askyesno("Apply Scale", "Do you want to apply a scale to the text?")

        if apply_scale:
            # Ask for the scale input
            scale_factor = simpledialog.askfloat("Scale Input", "Enter Scale Factor:")
        else:
            # If no scale is applied, set the scale factor to 1
            scale_factor = 1.0

        # Create a new window for text confirmation
        confirm_window = tk.Toplevel(root)
        confirm_window.title("Confirm Text")

        # Text widget to display extracted text for confirmation
        confirm_text_display = tk.Text(confirm_window, height=20, width=50, wrap=tk.WORD, font=('Helvetica', 12))
        confirm_text_display.pack(pady=20)
        confirm_text_display.insert(tk.END, f"Is the detected text correct?\n\n{text}\n\n")

        # Buttons for confirmation
        confirm_button = tk.Button(confirm_window, text="Yes", command=lambda: start_processing(text, image, scale_factor, confirm_window))
        confirm_button.pack(side=tk.LEFT, padx=10, pady=10)
        cancel_button = tk.Button(confirm_window, text="No", command=confirm_window.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=10, pady=10)

def translate_text():
    # Get the current content of the original text display
    original_text = text_display_original.get(1.0, tk.END)


    # Detect the language of the text
    language = translator.detect(original_text).lang

    # Translate the text to English
    translated_text = translator.translate(original_text, dest='en').text

    # Update the scaled text display
    # Update the scaled text display with the translated text
    text_display_scaled.delete(1.0, tk.END)  # Clear existing text
    text_display_scaled.insert(tk.END, f"Translated Text:\n{translated_text}\n\n")

def suggest_gluten_alternatives():
    # Get the current content of the Text widget
    scaled_text = text_display_scaled.get(1.0, tk.END)

    # Use a regular expression to find ingredients that may contain gluten
    gluten_pattern = re.compile(r'\b(wheat|barley|rye|oats|all-purpose flour|flour)\b', re.IGNORECASE)
    matches = gluten_pattern.findall(scaled_text)

    if matches:
        # Display gluten-containing ingredients and suggest alternatives
        gluten_message = "Ingredients that may contain gluten:\n"
        for ingredient in matches:
            if ingredient not in processed_gluten_ingredients:
                gluten_message += f"{ingredient}\n"
                processed_gluten_ingredients.add(ingredient)
                # Add your own suggestions for gluten-free alternatives here
                gluten_message += f"Suggested gluten-free alternative for {ingredient}: Try using a gluten-free flour alternative that claims 1 to 1 replacement. Or you can try using a combination of rice flour with starchy additives like potato starch, or xanthum powder\n"
    else:
        gluten_message = "No gluten-containing ingredients found in the scaled text."

    # Display the gluten suggestion in the Text widget
    text_display_scaled.insert(tk.END, gluten_message)

def suggest_lactose_alternatives():
    # Get the current content of the Text widget
    scaled_text = text_display_scaled.get(1.0, tk.END)

    # Use a regular expression to find ingredients that may contain lactose
    lactose_pattern = re.compile(r'\b(milk|butter|cream|cheese|yogurt|ice cream)\b', re.IGNORECASE)
    matches = lactose_pattern.findall(scaled_text)

    if matches:
        # Display lactose-containing ingredients and suggest alternatives
        lactose_message = "Ingredients that may contain lactose:\n"
        for ingredient in matches:
            # Add suggestions for lactose-free alternatives here
            lactose_message += f"{ingredient}\n"
            lactose_message += f"Suggested lactose-free alternative for {ingredient}: Consider using dairy-free alternatives like almond milk, coconut milk, or soy-based products.\n"
    else:
        lactose_message = "No lactose-containing ingredients found in the scaled text."

    # Display the lactose suggestion in the Text widget
    text_display_scaled.insert(tk.END, lactose_message)

def suggest_allergen_supplements():
    suggest_gluten_alternatives()
    suggest_lactose_alternatives()

def exit_application():
    save_last_five_recipes()
    root.destroy()

def save_current_output():
    # Get the current content of the scaled text display
    current_output = text_display_scaled.get(1.0, tk.END)

    # Save the current output to a file
    output_file_path = f'{recipe_folder_path}/Current_Output_{datetime.now().strftime("%Y%m%d%H%M%S")}.txt'
    with open(output_file_path, 'w') as file:
        file.write(current_output)

    print(f"Current output saved to {output_file_path}")

    return output_file_path

def print_saved_output():
    file_path = filedialog.askopenfilename(title="Select File to Print", initialdir=recipe_folder_path, filetypes=[("Text files", "*.txt")])
    
    if file_path:
        # Print the selected file
        os.startfile(file_path, "print")

def select_previous_recipe():
    file_path = filedialog.askopenfilename(title="Select a Previous Recipe", initialdir=recipe_folder_path, filetypes=[("Text files", "*.txt")])
    
    if file_path:
        # Ask if the user wants to apply a scale
        apply_scale = messagebox.askyesno("Apply Scale", "Do you want to apply a scale to the selected recipe?")
        
        if apply_scale:
            with open(file_path, 'r') as file:
                original_text = file.read()

            # Use Tesseract to extract text
            image = None  # No image for previous recipes
            scale_factor = simpledialog.askfloat("Scale Input", "Enter Scale Factor:")
            start_processing(original_text, image, scale_factor, None)
        else:
            with open(file_path, 'r') as file:
                raw_text = file.read()

            # Display the raw text in the output box
            text_display_scaled.delete(1.0, tk.END)  # Clear existing text
            text_display_scaled.insert(tk.END, raw_text)

            # Clear the original text box
            text_display_original.delete(1.0, tk.END)  # Clear existing text

def open_and_modify_file():
    file_path = filedialog.askopenfilename(title="Open Recipe Text File", initialdir=recipe_folder_path, filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, 'r') as file:
            text_content = file.read()

        modified_text = simpledialog.askstring("Modify Recipe", "Modify the recipe text:", initialvalue=text_content)
        if modified_text is not None:
            with open(file_path, 'w') as file:
                file.write(modified_text)
            messagebox.showinfo("File Saved", "Modified recipe saved successfully.")

# Create the main window
root = tk.Tk()
root.title("Snap n Bake")
root.configure(bg='#7BE3E0')

# Create recipe folder if it doesn't exist
create_recipe_folder()

# Set background image
background_canvas = set_background(root, r'C:\App\background.jpg')

# Title bar
title_label = tk.Label(background_canvas, text="Snap n Bake", font=('Comic Sans MS', 25, 'italic bold'), bg='#7BE3E0')
title_label.pack(pady=10)

#Main Frame
main_frame = ttk.Frame(background_canvas, style="Colored.TFrame")
main_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

# Add a custom style to change the background color
style = ttk.Style()
style.configure("Colored.TFrame", background='#F08BB6')

# Button for selecting recipe image
select_recipe_button = tk.Button(main_frame, text="Process Recipe", command=select_recipe_image)
select_recipe_button.pack(pady=10)

# Button for translating text
translate_button = tk.Button(main_frame, text="Translate", command=translate_text)
translate_button.pack(pady=10)

# Button for suggesting allergen supplements (both gluten and lactose)
allergen_suggestion_button = tk.Button(main_frame, text="Allergen Supplement Suggestion", command=suggest_allergen_supplements)
allergen_suggestion_button.pack(pady=10)

# Button for selecting previous recipe
select_previous_recipe_button = tk.Button(main_frame, text="Select Previous Recipe", command=select_previous_recipe)
select_previous_recipe_button.pack(pady=10)

# Button for opening and modifying a file
open_modify_button = tk.Button(main_frame, text="Open & Modify Recipe", command=open_and_modify_file)
open_modify_button.pack(pady=10)

# Button for printing saved output
print_saved_output_button = tk.Button(main_frame, text="Print Selected Output", command=print_saved_output)
print_saved_output_button.pack(pady=10)

# Button for exiting the application
exit_button = tk.Button(main_frame, text="Exit", command=exit_application)
exit_button.pack(pady=10)

# Text widgets to display extracted and scaled text
text_display_original = tk.Text(main_frame, height=20, width=50, wrap=tk.WORD, font=('Helvetica', 12), bg='#7BE3E0')
text_display_original.pack(side=tk.LEFT, padx=10, pady=20)

text_display_scaled = tk.Text(main_frame, height=20, width=50, wrap=tk.WORD, font=('Helvetica', 12), bg='#7BE3E0')
text_display_scaled.pack(side=tk.LEFT, padx=10, pady=20)

# Load saved recipes on startup
load_saved_recipes()

# Run the Tkinter event loop
root.mainloop()
