import machine
import network
import time
import os
from Pico_ePaper import EPD_2in13_V3_Landscape
from library import Book

library_path = '/sd'

EPD_WIDTH  = 250
EPD_HEIGHT = 122

# Declare hardware connections
SELECT_BUTTON = 2
UP_BUTTON     = 3
DOWN_BUTTON   = 4

class EReader:
    def __init__(self):
        # --- POWER OPTIMIZATION ---
        # Instantly kill the Wi-Fi chip on boot to save battery
        try:
            wlan = network.WLAN(network.STA_IF)
            wlan.active(False)
        except:
            pass # Fails cleanly if it's a standard non-W Pico
        
        self.epd = EPD_2in13_V3_Landscape()
        
        # State variables
        self.state = "MAIN_MENU"
        
        self.dark_mode = False
        self.txt_color = 0x00
        self.bkg_color = 0xff
        
        # State Button Connections
        self.up_button = machine.Pin(UP_BUTTON, machine.Pin.IN, machine.Pin.PULL_UP)
        self.down_button = machine.Pin(DOWN_BUTTON, machine.Pin.IN, machine.Pin.PULL_UP)
        
        self.select_button = machine.Pin(SELECT_BUTTON, machine.Pin.IN, machine.Pin.PULL_UP)
        self.select_button.irq(trigger=machine.Pin.IRQ_FALLING, handler=lambda pin: None)
        
        self.book_collection = self.get_books(library_path)
        self.active_book = None
        
        # Updated Menu configuration
        self.menu_items = ["Return to Book", "Select Book", "Dark Mode", "Power Off"]
        self.selected_index = 0
        self.previous_index = 0
        
        self.current_library_page = 1
        self.total_library_pages = -(-(len(self.book_collection) + 1) // 8) # Ceiling division, +1 for Return Option
    
    def update_colors(self):
        """Updates the hex colors based on the current dark mode state."""
        self.txt_color = 0xff if self.dark_mode else 0x00
        self.bkg_color = 0x00 if self.dark_mode else 0xff

    def center_x(self, text):
        """Helper to center text based on standard 8-pixel wide characters."""
        text_width = len(text) * 8
        return int((EPD_WIDTH - text_width) / 2)
    
    def get_books(self, path):
        # Define selection of books
        books = []
        for file in os.listdir(path):
            if file.endswith(".txt"): # if it's a txt file
                book = Book(file[:-4], path + "/" + file) # [:-4] removes .txt
                books.append(book)
        
        return books

    def draw_main_menu(self, partial=False):
        """Draws the main menu to the e-paper buffer and pushes it to the display."""
        # Draw Menu Items (Adjusted spacing for 122px max height)
        start_y = 38
        spacing = 20
        
        if not partial:
            self.epd.init()
            
            # Fill background
            self.epd.fill(self.bkg_color)
            self.epd.rect(0, 6, EPD_WIDTH, EPD_HEIGHT, self.txt_color)
            
            # Draw Header
            title = "Configuration Menu"
            self.epd.text(title, self.center_x(title), 11, self.txt_color)
            self.epd.hline(0, 24, EPD_WIDTH, self.txt_color) # Separator line
            
            for i, item in enumerate(self.menu_items):
                y = start_y + (i * spacing)
                display_text = item
                
                # Responsive Dark Mode Option
                if i == 2: 
                    display_text = f"Theme: {'Dark' if self.dark_mode else 'Light'}"
                
                # Draw selection cursor
                if i == self.selected_index:
                    self.epd.text(">", 15, y, self.txt_color)
                
                self.epd.text(display_text, 30, y, self.txt_color)
            
            self.epd.Display_Base(self.epd.buffer)
            
        else:
            prev_y = start_y + self.previous_index*spacing
            sele_y = start_y + self.selected_index*spacing
            
            self.epd.fill_rect(15, prev_y, 8, 8, self.bkg_color)
            self.epd.text(">", 15, sele_y, self.txt_color)
            
            # Twice so there's less ghosting
            self.epd.display_Partial(self.epd.buffer)
        
    def draw_library_menu(self, partial=False):
        # Define menu properties
        start_y = 22
        spacing = 12
        items_per_page = 8
        
        new_page = -(-(self.selected_index + 1) // 8) # Ceiling division
        
        if not partial or self.current_library_page != new_page:
            self.epd.init()
            
            # Design Menu
            self.epd.fill(self.bkg_color)
            title = "My Library"
            self.epd.text(title, 0, 7, self.txt_color)
            self.epd.hline(0, 16, 255, self.txt_color)
            
            book_count = f"Book Count: {len(self.book_collection)}"
            self.epd.text(book_count, EPD_WIDTH - len(book_count)*8, 7, self.txt_color)
            
            self.epd.hline(0, 118, 250, self.txt_color)
            self.current_library_page = new_page
            footer = f"Page {self.current_library_page}/{self.total_library_pages}"
            self.epd.text(footer, self.center_x(footer), 120, self.txt_color)
            
            # Write out all the "books"
            # Select books at indeces 1-8, 9-16, 17-24, etc.
            start_index = items_per_page*(self.current_library_page - 1)
            end_index = start_index + items_per_page
            
            displayed_books = self.book_collection[start_index:end_index] # Display sets of 8 books determined by page
            
            for display_row, book in enumerate(displayed_books):
                actual_list_index = start_index + display_row
                
                title = book.get_title()
                y = start_y + display_row*spacing # Reset the height from new page
                
                self.epd.text(title, 15, y, self.txt_color)
                    
                # Draw selection cursor
                if actual_list_index == self.selected_index:
                    self.epd.text(">", 0, y, self.txt_color)
            
            if self.current_library_page == self.total_library_pages:
                y = start_y + len(displayed_books)*spacing
                
                self.epd.text("Return to Main Menu", 15, y, self.txt_color)
            
            self.epd.Display_Base(self.epd.buffer)
        
        else:
            prev_y = start_y + (self.previous_index % 8)*spacing
            sele_y = start_y + (self.selected_index % 8)*spacing
            
            self.epd.fill_rect(0, prev_y, 8, 8, self.bkg_color)
            self.epd.text(">", 0, sele_y, self.txt_color)
            
            self.epd.display_Partial(self.epd.buffer)
    
    def draw_book(self):
        self.active_book.display_page(self.epd, self.txt_color, self.bkg_color)
    
    def draw_current_view(self, partial=False):
        if self.state == "MAIN_MENU":
            self.draw_main_menu(partial)
        elif self.state == "LIBRARY_MENU":
            self.draw_library_menu(partial)
        elif self.state == "BOOK":
            self.draw_book()

    def handle_main_menu(self, button):
        # Triggers the action for the selected main menu item using exact matching indexes.
        if button == "UP":
            self.previous_index = self.selected_index
            self.selected_index = (self.selected_index - 1) % len(self.menu_items)
            self.draw_current_view(partial=True)
            
        elif button == "DOWN":
            self.previous_index = self.selected_index
            self.selected_index = (self.selected_index + 1) % len(self.menu_items)
            self.draw_current_view(partial=True)
            
        elif button == "SELECT":
            # Handle each selection in the main menu
            if self.selected_index == 0:
                
                # Handle exception of no active book
                if self.active_book == None:
                    self.epd.init()
                    self.epd.fill(self.bkg_color)
                    msg = "NO ACTIVE BOOK"
                    self.epd.text(msg, self.center_x(msg), 61, self.txt_color)
                    self.epd.display(self.epd.buffer)
                    self.epd.sleep()
                    
                    time.sleep(1)
                    
                    self.draw_current_view()
                    
                else:
                    self.state = "BOOK"
                    self.draw_current_view()
                
            elif self.selected_index == 1:
                self.state = "LIBRARY_MENU"
                self.selected_index = 0
                self.draw_current_view()
                
            elif self.selected_index == 2:
                self.dark_mode = not self.dark_mode
                self.update_colors()
                self.draw_current_view()
                
            elif self.selected_index == 3:
                self.power_off()
                
    def handle_library_menu(self, button):
        # Triggers the action for the selected main menu item using exact matching indexes.
        if button == "UP":
            self.previous_index = self.selected_index
            self.selected_index = (self.selected_index - 1) % (len(self.book_collection) + 1) # +1 for Return to Menu option
            self.draw_current_view(partial=True)
        
        elif button == "DOWN":
            self.previous_index = self.selected_index
            self.selected_index = (self.selected_index + 1) % (len(self.book_collection) + 1) # +1 for Return to Menu option
            self.draw_current_view(partial=True)
        
        elif button == "SELECT":
            if self.selected_index == len(self.book_collection): # If the last option (Return to menu) is selected
                self.state = "MAIN_MENU"
                self.selected_index = 0
                self.draw_current_view()
            else:
                self.active_book = self.book_collection[self.selected_index]
                self.state = "BOOK"
                self.draw_current_view()                
    
    def handle_book(self, button):
        if button == "UP":
            next_page = self.active_book.get_page() - 1
            
            if next_page >= 0:
                self.active_book.set_page(next_page)
                self.draw_current_view()
            
        elif button == "DOWN":
            next_page = self.active_book.get_page() + 1
            
            if next_page < (self.active_book.get_total_pages() - 1):
                self.active_book.set_page(next_page)
                self.draw_current_view()
            
        elif button == "SELECT":
            self.state = "MAIN_MENU"
            self.selected_index = 0
            self.draw_current_view()
            
    def run(self):
        """Main application loop."""
        # Initial clear and draw
        self.epd.init()
        self.epd.Clear()
        self.draw_current_view()
        
        while True:
            button = None
            
            if self.up_button.value() == 0:
                button = "UP"
                
            elif self.down_button.value() == 0:
                button = "DOWN"
                
            elif self.select_button.value() == 0:
                button = "SELECT"
            
            # If a button was pressed, process it
            if button:
                if self.state == "MAIN_MENU":
                    self.handle_main_menu(button)
                elif self.state == "LIBRARY_MENU":
                    self.handle_library_menu(button)
                elif self.state == "BOOK":
                    self.handle_book(button)
                
            time.sleep(0.05) # Keep CPU cool

    def power_off(self):
        """Safely shuts down the display and puts the Pico into light sleep."""
        self.epd.init()
        self.epd.fill(0xff) # Leave screen white to prevent ghosting
        msg = "Powering Off..."
        self.epd.text(msg, self.center_x(msg), int(EPD_HEIGHT/2) - 4, 0x00)
        self.epd.display(self.epd.buffer)
        time.sleep(2)
        
        self.epd.Clear()
        self.epd.delay_ms(2000)
        self.epd.sleep()
        
        while True:
            if self.select_button.value() == 0:
                break
            
            time.sleep(2) # Check every other second
            
        self.power_on()
        
    def power_on(self):
        self.epd.init()
        self.epd.fill(0xff) # Leave screen white to prevent ghosting
        msg = "Powering On..."
        self.epd.text(msg, self.center_x(msg), int(EPD_HEIGHT/2) - 4, 0x00)
        self.epd.display(self.epd.buffer)
        time.sleep(2)
        
        # Continue where it left off after button press
        self.selected_index = 0
        self.draw_main_menu()
        

